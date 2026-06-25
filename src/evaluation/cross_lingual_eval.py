import os
import json
import torch
import numpy as np
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    pipeline
)
from sklearn.metrics import f1_score
import mlflow

from src.training.mlflow_utils import setup_mlflow
from src.data.bio_tagger import bio_to_aspects

def load_data(file_path: Path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def main():
    setup_mlflow()
    
    # Check if models exist (might not if trained on Colab)
    aspect_model_path = Path("models/aspect_extraction/best")
    sentiment_model_path = Path("models/sentiment/best")
    
    if not aspect_model_path.exists() or not sentiment_model_path.exists():
        print("Models not found locally. Skipping cross-lingual evaluation until models are trained.")
        return
        
    print("Loading models...")
    tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
    
    aspect_model = AutoModelForTokenClassification.from_pretrained(str(aspect_model_path))
    sentiment_model = AutoModelForSequenceClassification.from_pretrained(str(sentiment_model_path))
    
    device = 0 if torch.cuda.is_available() else -1
    
    ner_pipeline = pipeline("token-classification", model=aspect_model, tokenizer=tokenizer, device=device, aggregation_strategy="simple")
    
    # Load Hindi Data
    hindi_path = Path("data/processed/amazon_hindi.jsonl")
    hindi_data = load_data(hindi_path)
    
    print(f"Evaluating zero-shot on {len(hindi_data)} Hindi samples...")
    
    sentiment_map_rev = {0: "positive", 1: "negative", 2: "neutral", 3: "conflict"}
    sentiment_map = {"positive": 0, "negative": 1, "neutral": 2, "conflict": 3}
    
    true_labels = []
    pred_labels = []
    
    for item in hindi_data:
        text = item["text"]
        aspects = item.get("aspect_terms", [])
        
        for aspect in aspects:
            term = aspect["term"]
            true_polarity = aspect["polarity"]
            if true_polarity not in sentiment_map:
                continue
                
            true_labels.append(sentiment_map[true_polarity])
            
            # Inference Sentiment
            inputs = tokenizer(text, term, return_tensors="pt", truncation=True, max_length=128)
            if device == 0:
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                sentiment_model.to("cuda")
                
            with torch.no_grad():
                logits = sentiment_model(**inputs).logits
                pred_idx = torch.argmax(logits, dim=1).item()
                
            pred_labels.append(pred_idx)
            
    hindi_macro_f1 = f1_score(true_labels, pred_labels, average="macro") if len(true_labels) > 0 else 0.0
    print(f"Hindi Zero-Shot Macro-F1: {hindi_macro_f1}")
    
    # We retrieve the best English test score from MLflow
    # For now, let's just log the cross lingual gap if we know English F1
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name("multilingual-absa")
    
    en_macro_f1 = 0.0
    if experiment:
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="metrics.test_macro_f1 > 0",
            max_results=1,
            order_by=["metrics.test_macro_f1 DESC"]
        )
        if runs:
            en_macro_f1 = runs[0].data.metrics.get("test_macro_f1", 0.0)
            
    print(f"Best English Test Macro-F1: {en_macro_f1}")
    gap = en_macro_f1 - hindi_macro_f1
    print(f"Cross-Lingual Gap: {gap}")
    
    with mlflow.start_run(run_name="cross_lingual_eval"):
        mlflow.log_metrics({
            "hindi_zero_shot_macro_f1": float(hindi_macro_f1),
            "english_test_macro_f1": float(en_macro_f1),
            "cross_lingual_gap": float(gap)
        })

if __name__ == "__main__":
    main()
