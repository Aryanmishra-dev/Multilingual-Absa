"""
Script for QLoRA fine-tuning of XLM-RoBERTa for sentiment analysis.
"""
import os
from pathlib import Path
import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    set_seed
)
from peft import get_peft_model, LoraConfig, TaskType
from datasets import load_dataset
import mlflow
import numpy as np
from sklearn.metrics import f1_score

# Constraints: seed=42 everywhere
set_seed(42)

def compute_metrics(eval_pred) -> dict:
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    macro_f1 = f1_score(labels, predictions, average="macro")
    return {"macro_f1": macro_f1}

def main():
    model_name = "xlm-roberta-base"
    output_dir = Path("models/sentiment/qlora-adapter")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data_dir = Path("data/processed")
    
    # 4-bit quantization config
    try:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
    except Exception as e:
        print(f"Warning: bitsandbytes might not be supported on this system. Detailed error: {e}")
        bnb_config = None # Fallback or error based on environment

    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=4, # positive, negative, neutral, conflict
        quantization_config=bnb_config if bnb_config else None,
        device_map="auto"
    )

    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["query", "value"]
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # NOTE: Assuming combined dataset is prepared or we combine them here.
    # For now, we load a placeholder train dataset
    train_file = data_dir / "semeval_train.jsonl"
    if not train_file.exists():
        print(f"Train file {train_file} does not exist. Please prepare data first.")
        return

    dataset = load_dataset("json", data_files={"train": str(train_file)})
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)
        
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        evaluation_strategy="epoch",
        learning_rate=2e-4,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        seed=42,
        logging_dir='./logs',
        logging_steps=10,
        save_strategy="epoch"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        # eval_dataset=tokenized_datasets["test"], # Add test set if available
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics
    )
    
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("qlora-sentiment")
    
    with mlflow.start_run():
        trainer.train()
        
        # Save adapter
        model.save_pretrained(str(output_dir))
        tokenizer.save_pretrained(str(output_dir))
        
        # Log adapter weights to MLflow
        mlflow.log_artifacts(str(output_dir), artifact_path="qlora-adapter")

if __name__ == "__main__":
    main()
