import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer
from sklearn.model_selection import train_test_split
from absa.data.bio_tagger import convert_to_bio

np.random.seed(42)


def load_data(file_paths: List[Path]) -> List[Dict[str, Any]]:
    data = []
    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    return data


def prepare_ner_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepares data for Token Classification (NER)."""
    ner_data: List[Dict[str, Any]] = []
    label_map = {"O": 0, "B-ASP": 1, "I-ASP": 2}

    for item in data:
        text = item["text"]
        aspects = item.get("aspect_terms", [])
        bio_tags = convert_to_bio(text, aspects)

        tokens = [t["token"] for t in bio_tags]
        ner_tags = [label_map[t["label"]] for t in bio_tags]

        ner_data.append(
            {
                "tokens": tokens,
                "ner_tags": ner_tags,
                "id": item.get("id", str(len(ner_data))),
            }
        )
    return ner_data


def prepare_cls_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepares data for Sequence Classification (Sentiment)."""
    cls_data: List[Dict[str, Any]] = []
    sentiment_map = {"positive": 0, "negative": 1, "neutral": 2, "conflict": 3}

    for item in data:
        text = item["text"]
        aspects = item.get("aspect_terms", [])

        for aspect in aspects:
            term = aspect["term"]
            polarity = aspect["polarity"]

            if polarity not in sentiment_map:
                continue

            cls_data.append(
                {
                    "text": text,
                    "aspect_term": term,
                    "label": sentiment_map[polarity],
                    "id": f"{item.get('id', str(len(cls_data)))}_{term}",
                }
            )
    return cls_data


def align_labels_with_tokens(labels, word_ids):
    new_labels = []
    current_word = None
    for word_id in word_ids:
        if word_id is None:
            new_labels.append(-100)
        elif word_id != current_word:
            new_labels.append(labels[word_id])
            current_word = word_id
        else:
            new_labels.append(-100)
    return new_labels


def main():
    data_dir = Path("data/processed")
    output_dir = Path("data/tokenized")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load all English SemEval data
    train_path = data_dir / "semeval_train.jsonl"
    test_path = data_dir / "semeval_test.jsonl"
    all_data = load_data([train_path, test_path])

    # Prepare datasets
    ner_data = prepare_ner_data(all_data)
    cls_data = prepare_cls_data(all_data)

    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")

    # ---------------------------------------------------------
    # 1. Token Classification (NER) Dataset
    # ---------------------------------------------------------
    ner_df = pd.DataFrame(ner_data)

    # Split 80/10/10
    # For NER, we don't have a single sentiment to stratify on easily, so random split
    train_ner, temp_ner = train_test_split(ner_df, test_size=0.2, random_state=42)
    val_ner, test_ner = train_test_split(temp_ner, test_size=0.5, random_state=42)

    def tokenize_and_align_labels(examples):
        tokenized_inputs = tokenizer(
            examples["tokens"],
            truncation=True,
            is_split_into_words=True,
            max_length=128,
        )
        labels = []
        for i, label in enumerate(examples["ner_tags"]):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            labels.append(align_labels_with_tokens(label, word_ids))
        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    ner_dataset = DatasetDict(
        {
            "train": Dataset.from_pandas(train_ner, preserve_index=False),
            "validation": Dataset.from_pandas(val_ner, preserve_index=False),
            "test": Dataset.from_pandas(test_ner, preserve_index=False),
        }
    )

    tokenized_ner = ner_dataset.map(
        tokenize_and_align_labels,
        batched=True,
        remove_columns=["tokens", "ner_tags", "id"],
    )
    tokenized_ner.save_to_disk(str(output_dir / "absa_ner_dataset"))
    print(f"NER Dataset saved to {output_dir / 'absa_ner_dataset'}")

    # ---------------------------------------------------------
    # 2. Sequence Classification (Sentiment) Dataset
    # ---------------------------------------------------------
    cls_df = pd.DataFrame(cls_data)

    # Stratified split 80/10/10 based on label
    train_cls, temp_cls = train_test_split(
        cls_df, test_size=0.2, random_state=42, stratify=cls_df["label"]
    )
    val_cls, test_cls = train_test_split(
        temp_cls, test_size=0.5, random_state=42, stratify=temp_cls["label"]
    )

    def tokenize_cls(examples):
        # Format: [CLS] text [SEP] aspect_term [SEP]
        return tokenizer(
            examples["text"],
            examples["aspect_term"],
            truncation=True,
            max_length=128,
            padding=False,
        )

    cls_dataset = DatasetDict(
        {
            "train": Dataset.from_pandas(train_cls, preserve_index=False),
            "validation": Dataset.from_pandas(val_cls, preserve_index=False),
            "test": Dataset.from_pandas(test_cls, preserve_index=False),
        }
    )

    tokenized_cls = cls_dataset.map(
        tokenize_cls, batched=True, remove_columns=["text", "aspect_term", "id"]
    )
    tokenized_cls.save_to_disk(str(output_dir / "absa_cls_dataset"))
    print(f"CLS Dataset saved to {output_dir / 'absa_cls_dataset'}")


if __name__ == "__main__":
    main()
