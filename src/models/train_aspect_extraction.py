import numpy as np
from pathlib import Path
from datasets import load_from_disk
from transformers import (
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
    AutoTokenizer,
    set_seed,
)
from seqeval.metrics import f1_score as seqeval_f1_score
import mlflow

from src.training.mlflow_utils import setup_mlflow


def compute_metrics(p):
    """Computes evaluation metrics (F1 score) for token classification.

    Args:
        p: EvalPrediction tuple containing predictions and labels.

    Returns:
        Dictionary with 'f1' key and its computed value.
    """
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    label_map = {0: "O", 1: "B-ASP", 2: "I-ASP"}

    true_predictions = [
        [label_map[p] for (p, lbl) in zip(prediction, label) if lbl != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_map[lbl] for (p, lbl) in zip(prediction, label) if lbl != -100]
        for prediction, label in zip(predictions, labels)
    ]

    # Seqeval F1 handles span-level scoring
    f1 = seqeval_f1_score(true_labels, true_predictions)

    # Calculate macro F1 roughly from classification report if needed,
    # but for NER, seqeval's micro-averaged F1 (which seqeval_f1_score returns) is standard span-F1
    return {"f1": f1}


def main():
    """Main function to train and evaluate the aspect extraction model.

    Loads tokenized dataset, initializes XLM-RoBERTa for token classification,
    configures Trainer, executes training loop, evaluates on test set,
    and logs results to MLflow.
    """
    set_seed(42)
    setup_mlflow()

    dataset_path = Path("data/tokenized/absa_ner_dataset")
    print(f"Loading dataset from {dataset_path}")
    dataset = load_from_disk(str(dataset_path))

    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    label_map = {0: "O", 1: "B-ASP", 2: "I-ASP"}
    model = AutoModelForTokenClassification.from_pretrained(
        "xlm-roberta-base",
        num_labels=len(label_map),
        id2label=label_map,
        label2id={v: k for k, v in label_map.items()},
    )

    output_dir = "models/aspect_extraction"

    training_args = TrainingArguments(
        output_dir=output_dir,
        learning_rate=2e-5,
        num_train_epochs=5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_ratio=0.1,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        metric_for_best_model="eval_f1",
        load_best_model_at_end=True,
        seed=42,
        report_to="mlflow",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print("Training Aspect Extraction model...")
    trainer.train()

    print("Evaluating on test set...")
    test_results = trainer.evaluate(dataset["test"], metric_key_prefix="test")
    print(test_results)

    best_model_path = Path(output_dir) / "best"
    trainer.save_model(str(best_model_path))
    print(f"Best model saved to {best_model_path}")

    # Log test metric manually since trainer.train() only automatically logs eval metrics
    # if report_to="mlflow" handles it, but test results we need to make sure are in the same run.
    with mlflow.start_run(
        run_id=(
            trainer.state.trial_params.get("mlflow_run_id")
            if trainer.state.trial_params
            else mlflow.active_run().info.run_id if mlflow.active_run() else None
        )
    ) as run:
        mlflow.log_metrics(
            {"test_f1": test_results["test_f1"], "test_loss": test_results["test_loss"]}
        )
        print(f"Logged test metrics to run {run.info.run_id}")


if __name__ == "__main__":
    main()
