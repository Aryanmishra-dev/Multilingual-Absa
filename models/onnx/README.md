---
language:
- en
- hi
tags:
- sentiment-analysis
- aspect-based-sentiment-analysis
- onnx
- int8
- xlm-roberta
---

# Multilingual ABSA (Aspect-Based Sentiment Analysis)

## Model Description
This repository contains INT8-quantized ONNX models for Multilingual Aspect-Based Sentiment Analysis (ABSA).
It uses a two-stage pipeline:
1. **Aspect Extraction**: Token classification model to identify aspects in text.
2. **Sentiment Classification**: Sequence classification model to determine sentiment (Positive, Negative, Neutral, Conflict) for extracted aspects.

Both models are based on `xlm-roberta-base`, fine-tuned using QLoRA, and exported to ONNX for CPU-optimized inference.

## Languages Supported
- English (en)
- Hindi (hi)
- Hinglish (code-mixed)

## Performance Metrics (Phase 4)
- **English**: Macro-F1 > 78%
- **Hindi**: Macro-F1 > 65%
- **Latency (INT8 CPU)**: P95 < 300ms

## Usage
```python
from optimum.onnxruntime import ORTModelForTokenClassification, ORTModelForSequenceClassification
from transformers import AutoTokenizer

model_id = "YOUR_HF_USERNAME/multilingual-absa"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# Load Aspect Extraction Model
aspect_model = ORTModelForTokenClassification.from_pretrained(
    model_id, 
    subfolder="aspect_extraction_int8"
)

# Load Sentiment Model
sentiment_model = ORTModelForSequenceClassification.from_pretrained(
    model_id,
    subfolder="sentiment_int8"
)
```

## Training Data
Fine-tuned on combined SemEval (English) and translated/native Hindi product review datasets.
