import os
import torch
import numpy as np
from pathlib import Path
from datasets import load_from_disk
from transformers import (
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    AutoTokenizer,
    set_seed
)
from sklearn.metrics import f1_score, confusion_matrix
import mlflow

from src.training.mlflow_utils import setup_mlflow

def compute_metrics(p):
    """Computes evaluation metrics (F1 score) for sequence classification.
    
    Args:
        p: EvalPrediction tuple containing predictions and labels.
        
    Returns:
        Dictionary with macro F1 and per-class F1 metrics.
    """
    predictions, labels = p
    predictions = np.argmax(predictions, axis=1)
    
    macro_f1 = f1_score(labels, predictions, average="macro")
    per_class_f1 = f1_score(labels, predictions, average=None)
    
    # We will log confusion matrix in the main function
    return {
        "macro_f1": macro_f1,
        "f1_positive": per_class_f1[0] if len(per_class_f1) > 0 else 0.0,
        "f1_negative": per_class_f1[1] if len(per_class_f1) > 1 else 0.0,
        "f1_neutral": per_class_f1[2] if len(per_class_f1) > 2 else 0.0,
        "f1_conflict": per_class_f1[3] if len(per_class_f1) > 3 else 0.0,
    }

class ImbalancedTrainer(Trainer):
    def __init__(self, class_weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights
        
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        
        if self.class_weights is not None:
            loss_fct = torch.nn.CrossEntropyLoss(weight=self.class_weights.to(model.device))
        else:
            loss_fct = torch.nn.CrossEntropyLoss()
            
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        
        return (loss, outputs) if return_outputs else loss

def main():
    """Main function to train and evaluate the sentiment classification model.
    
    Loads tokenized dataset, initializes XLM-RoBERTa for sequence classification,
    handles class imbalances using a custom Trainer, executes training loop,
    evaluates on test set, logs confusion matrix, and logs results to MLflow.
    """
    set_seed(42)
    setup_mlflow()
    
    dataset_path = Path("data/tokenized/absa_cls_dataset")
    print(f"Loading dataset from {dataset_path}")
    dataset = load_from_disk(str(dataset_path))
    
    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    label_map = {0: "positive", 1: "negative", 2: "neutral", 3: "conflict"}
    model = AutoModelForSequenceClassification.from_pretrained(
        "xlm-roberta-base",
        num_labels=len(label_map),
        id2label=label_map,
        label2id={v: k for k, v in label_map.items()}
    )
    
    output_dir = "models/sentiment"
    
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
        metric_for_best_model="eval_macro_f1",
        load_best_model_at_end=True,
        seed=42,
        report_to="mlflow"
    )
    
    # Calculate class weights for imbalanced dataset (especially 'conflict')
    train_labels = dataset["train"]["label"]
    from sklearn.utils.class_weight import compute_class_weight
    class_weights = compute_class_weight('balanced', classes=np.unique(train_labels), y=train_labels)
    class_weights_tensor = torch.tensor(class_weights, dtype=torch.float)
    
    trainer = ImbalancedTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        class_weights=class_weights_tensor
    )
    
    print("Training Sentiment Classification model...")
    trainer.train()
    
    print("Evaluating on test set...")
    test_results = trainer.evaluate(dataset["test"], metric_key_prefix="test")
    print(test_results)
    
    best_model_path = Path(output_dir) / "best"
    trainer.save_model(str(best_model_path))
    print(f"Best model saved to {best_model_path}")
    
    # Confusion matrix on test set
    predictions = trainer.predict(dataset["test"])
    preds = np.argmax(predictions.predictions, axis=1)
    labels = predictions.label_ids
    cm = confusion_matrix(labels, preds)
    
    with mlflow.start_run(run_id=trainer.state.trial_params.get("mlflow_run_id") if trainer.state.trial_params else mlflow.active_run().info.run_id if mlflow.active_run() else None) as run:
        mlflow.log_metrics({
            "test_macro_f1": test_results["test_macro_f1"],
            "test_loss": test_results["test_loss"]
        })
        mlflow.log_dict({"confusion_matrix": cm.tolist()}, "confusion_matrix.json")
        print(f"Logged test metrics and confusion matrix to run {run.info.run_id}")

if __name__ == "__main__":
    main()
