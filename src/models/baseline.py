import json
import joblib
from pathlib import Path
from typing import List
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
import mlflow
from src.training.mlflow_utils import log_training_run


def load_data(file_paths: List[Path]) -> pd.DataFrame:
    data = []
    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    return pd.DataFrame(data)


def extract_sentence_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts a sentence-level sentiment by taking the majority sentiment of aspects.
    If there is a tie or conflict, it maps it appropriately.
    For this baseline, we will filter to samples that have a clear sentence-level sentiment
    derived from the aspects, or use the aspects to build a flat list of text -> sentiment.
    Wait, the requirement says "Sentence-level sentiment only (not ABSA)".
    Let's just flatten it: pair each review text with the sentiment of its aspect,
    but wait, a sentence might have multiple aspects with different sentiments.
    If we do "Sentence-level sentiment only", we can just assign the sentence the label of the first aspect,
    or we can construct a dataset of (text, sentiment) for every aspect but just predict sentiment from text alone.
    Let's flatten it to (text, sentiment) pairs for every aspect to keep the dataset size comparable.
    """
    records = []
    sentiment_map = {"positive": 0, "negative": 1, "neutral": 2, "conflict": 3}

    for _, row in df.iterrows():
        text = row["text"]
        aspects = row.get("aspect_terms", [])

        for aspect in aspects:
            polarity = aspect["polarity"]
            if polarity in sentiment_map:
                records.append({"text": text, "label": sentiment_map[polarity]})
    return pd.DataFrame(records)


def main():
    data_dir = Path("data/processed")
    train_path = data_dir / "semeval_train.jsonl"

    # Load raw data
    # Test path has no labels, so we only use train_path like we effectively did in hf_dataset
    train_df_raw = load_data([train_path])

    # Prepare flat sequence classification data
    cls_df = extract_sentence_sentiment(train_df_raw)

    # Exact same split logic as hf_dataset.py
    train_cls, temp_cls = train_test_split(
        cls_df, test_size=0.2, random_state=42, stratify=cls_df["label"]
    )
    val_cls, test_cls = train_test_split(
        temp_cls, test_size=0.5, random_state=42, stratify=temp_cls["label"]
    )

    X_train = train_cls["text"].values
    y_train = train_cls["label"].values

    X_test = test_cls["text"].values
    y_test = test_cls["label"].values

    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

    # Baseline Model Pipeline
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000)
    classifier = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=42
    )

    # Train
    print("Training TF-IDF + Logistic Regression...")
    X_train_vec = vectorizer.fit_transform(X_train)
    classifier.fit(X_train_vec, y_train)

    # Evaluate
    print("Evaluating...")
    X_test_vec = vectorizer.transform(X_test)
    y_pred = classifier.predict(X_test_vec)

    # Metrics
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    per_class_f1 = f1_score(y_test, y_pred, average=None)
    conf_matrix = confusion_matrix(y_test, y_pred)

    print(
        classification_report(
            y_test, y_pred, target_names=["positive", "negative", "neutral", "conflict"]
        )
    )

    # Format metrics for MLflow
    metrics = {
        "eval_macro_f1": float(macro_f1),
        "eval_f1_positive": float(per_class_f1[0]),
        "eval_f1_negative": float(per_class_f1[1]),
        "eval_f1_neutral": float(per_class_f1[2]),
        "eval_f1_conflict": float(per_class_f1[3] if len(per_class_f1) > 3 else 0.0),
    }

    # Also log confusion matrix as flattened or individual values (optional, can be artifact later)
    # For now, print it. We will log it via mlflow log_dict or json artifact if we want, but let's just log metrics.

    # Save Model
    model_dir = Path("models/baseline")
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "tfidf_lr.pkl"
    joblib.dump({"vectorizer": vectorizer, "classifier": classifier}, model_path)
    print(f"Model saved to {model_path}")

    # Log to MLflow
    params = {
        "model": "tfidf_lr",
        "ngram_range": "(1, 2)",
        "max_features": 10000,
        "max_iter": 1000,
        "class_weight": "balanced",
    }

    run_id = log_training_run(params, metrics, model_path, run_name="baseline_tfidf_lr")

    # We can also explicitly log the confusion matrix as an artifact
    with mlflow.start_run(run_id=run_id):
        cm_dict = {"confusion_matrix": conf_matrix.tolist()}
        mlflow.log_dict(cm_dict, "confusion_matrix.json")

    print(f"MLflow run ID: {run_id}")


if __name__ == "__main__":
    main()
