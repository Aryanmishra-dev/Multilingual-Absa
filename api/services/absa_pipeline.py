import os
from pathlib import Path
import time
import numpy as np
from typing import List, Dict, Any
from api.models.schemas import PredictionResponse, AspectSentiment
from api.services.lang_service import lang_service

try:
    from optimum.onnxruntime import ORTModelForTokenClassification, ORTModelForSequenceClassification
    from transformers import AutoTokenizer
    from huggingface_hub import hf_hub_download, snapshot_download
    OPTIMUM_AVAILABLE = True
except ImportError:
    OPTIMUM_AVAILABLE = False

class ABSAPipeline:
    def __init__(self):
        self.tokenizer = None
        self.aspect_model = None
        self.sentiment_model = None
        self.is_loaded = False
        
        # BIO tags for aspect extraction (example mapping)
        self.id2label = {0: "O", 1: "B-ASP", 2: "I-ASP"}
        self.sentiment_id2label = {0: "positive", 1: "negative", 2: "neutral", 3: "conflict"}

    def load_models(self):
        """Load ONNX models from local path or HuggingFace Hub.
        
        Attempts to load quantized INT8 ONNX models for token classification
        and sequence classification. If local paths are missing and MODEL_SOURCE
        is huggingface_hub, it downloads them from the Hub.
        """
        if not OPTIMUM_AVAILABLE:
            print("Optimum not available. ABSA Pipeline will use dummy responses.")
            self.is_loaded = True
            return

        model_path_base = Path(os.getenv("MODEL_PATH", "models/onnx"))
        hf_repo_id = os.getenv("HF_MODEL_REPO", "YOUR_HF_USERNAME/multilingual-absa")
        use_hub = os.getenv("MODEL_SOURCE", "local") == "huggingface_hub"
        
        aspect_path = model_path_base / "aspect_extraction_int8"
        sentiment_path = model_path_base / "sentiment_int8"
        
        if not aspect_path.exists() and not use_hub:
            aspect_path = model_path_base / "aspect_extraction"
        if not sentiment_path.exists() and not use_hub:
            sentiment_path = model_path_base / "sentiment"

        try:
            self.tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
            if use_hub or not aspect_path.exists():
                print(f"Downloading/loading from HF Hub: {hf_repo_id}")
                self.aspect_model = ORTModelForTokenClassification.from_pretrained(hf_repo_id, subfolder="aspect_extraction_int8")
                self.sentiment_model = ORTModelForSequenceClassification.from_pretrained(hf_repo_id, subfolder="sentiment_int8")
            else:
                print(f"Loading ONNX models from {aspect_path} and {sentiment_path}")
                self.aspect_model = ORTModelForTokenClassification.from_pretrained(str(aspect_path))
                self.sentiment_model = ORTModelForSequenceClassification.from_pretrained(str(sentiment_path))
            self.is_loaded = True
        except Exception as e:
            print(f"Failed to load ONNX models: {e}")
            self.is_loaded = False

    def predict(self, text: str, requested_lang: str = None) -> PredictionResponse:
        """Run full ABSA pipeline on a single review.
        
        Args:
            text: Raw review text in any supported language.
            requested_lang: Optional language code to override auto-detection.
            
        Returns:
            PredictionResponse containing detected language, processing time,
            and a list of extracted aspects with their sentiments and confidences.
            
        Raises:
            ValueError: If text is empty or exceeds length limits (handled downstream).
        """
        start_time = time.time()
        
        detected_lang = lang_service.detect_language(text)
        actual_lang = requested_lang if requested_lang else detected_lang
        
        if not self.is_loaded or not self.aspect_model:
            # Dummy response for testing without models
            process_time = (time.time() - start_time) * 1000
            return PredictionResponse(
                text=text,
                language=actual_lang,
                detected_language=detected_lang,
                aspects=[],
                processing_time_ms=process_time
            )
            
        # 1. Aspect Extraction
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        aspect_outputs = self.aspect_model(**inputs)
        logits = aspect_outputs.logits[0].detach().numpy()
        predictions = np.argmax(logits, axis=1)
        
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        
        aspects = []
        current_aspect = []
        start_idx = -1
        
        # Very basic BIO decoding logic
        for idx, (token, pred) in enumerate(zip(tokens, predictions)):
            if token in [self.tokenizer.cls_token, self.tokenizer.sep_token, self.tokenizer.pad_token]:
                continue
                
            label = self.id2label.get(pred, "O")
            if label == "B-ASP":
                if current_aspect:
                    aspects.append(("".join(current_aspect).replace(" ", " ").strip(), start_idx, idx-1))
                current_aspect = [token]
                start_idx = idx
            elif label == "I-ASP" and current_aspect:
                current_aspect.append(token)
            else:
                if current_aspect:
                    aspects.append(("".join(current_aspect).replace(" ", " ").strip(), start_idx, idx-1))
                    current_aspect = []
                    
        if current_aspect:
            aspects.append(("".join(current_aspect).replace(" ", " ").strip(), start_idx, len(tokens)-1))

        # 2. Sentiment Classification per aspect
        results = []
        for aspect_text, s_idx, e_idx in aspects:
            # For joint model, typically it's text + aspect
            # Here we just predict sentiment for the aspect within the context
            seq_input = self.tokenizer(text, text_pair=aspect_text, return_tensors="pt", truncation=True, max_length=128)
            sent_out = self.sentiment_model(**seq_input)
            sent_logits = sent_out.logits[0].detach().numpy()
            
            # softmax
            exp_logits = np.exp(sent_logits - np.max(sent_logits))
            probs = exp_logits / exp_logits.sum()
            
            pred_class = np.argmax(probs)
            confidence = float(probs[pred_class])
            sentiment = self.sentiment_id2label.get(pred_class, "neutral")
            
            results.append(AspectSentiment(
                aspect=aspect_text,
                sentiment=sentiment,
                confidence=confidence,
                start=s_idx,
                end=e_idx
            ))
            
        process_time = (time.time() - start_time) * 1000
        
        return PredictionResponse(
            text=text,
            language=actual_lang,
            detected_language=detected_lang,
            aspects=results,
            processing_time_ms=process_time
        )
        
    def predict_batch(self, texts: List[str]) -> List[PredictionResponse]:
        """Run full ABSA pipeline on a batch of reviews.
        
        Args:
            texts: List of raw review strings.
            
        Returns:
            List of PredictionResponse objects.
        """
        # simplified batch processing
        return [self.predict(text) for text in texts]

pipeline = ABSAPipeline()
