import json
from datasets import load_from_disk
from collections import defaultdict
from src.utils.config import RAW_DIR, SEMEVAL_TRAIN_PATH, SEMEVAL_TEST_PATH
from src.data.preprocess import clean
from src.data.lang_detect import detect_language


def process_semeval():
    rest_path = RAW_DIR / "semeval_restaurants"
    lap_path = RAW_DIR / "semeval_laptops"

    rest_data = load_from_disk(str(rest_path))
    lap_data = load_from_disk(str(lap_path))

    train_samples = defaultdict(list)
    test_samples = defaultdict(list)

    for ds_name, ds, source_name in [
        ("train", rest_data["train"], "restaurants"),
        ("test", rest_data["test"], "restaurants"),
        ("train", lap_data["train"], "laptops"),
        ("test", lap_data["test"], "laptops"),
    ]:
        target = train_samples if ds_name == "train" else test_samples
        for row in ds:
            text = row["text"]
            span = row["span"]
            label = row["label"]

            target[(text, source_name)].append({"term": span, "polarity": label})

    SEMEVAL_TRAIN_PATH.parent.mkdir(parents=True, exist_ok=True)

    for path, data_dict in [
        (SEMEVAL_TRAIN_PATH, train_samples),
        (SEMEVAL_TEST_PATH, test_samples),
    ]:
        total = 0
        lang_counts = defaultdict(int)
        with open(path, "w", encoding="utf-8") as f:
            for (text, source), aspects in data_dict.items():
                lang = detect_language(text)
                cleaned_text = clean(text, lang)
                lang_counts[lang] += 1

                final_aspects = []
                for aspect in aspects:
                    term_clean = clean(aspect["term"], lang)
                    from_idx = cleaned_text.find(term_clean)
                    to_idx = from_idx + len(term_clean) if from_idx != -1 else -1
                    final_aspects.append(
                        {
                            "term": term_clean,
                            "polarity": aspect["polarity"],
                            "from": from_idx,
                            "to": to_idx,
                        }
                    )

                sample = {
                    "text": cleaned_text,
                    "language": lang,
                    "aspect_terms": final_aspects,
                    "source": source,
                }
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                total += 1

        print(f"SemEval {path.stem} samples: {total}")
        print(f"SemEval {path.stem} languages: {dict(lang_counts)}")


if __name__ == "__main__":
    process_semeval()
