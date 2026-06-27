"""
ABSA Pipeline — Zero-download, production-ready fallback.

Strategy:
  1. Try loading custom ONNX models (if present in models/onnx/).
  2. Fall back to a fast, pure-Python rule-based engine:
       - Aspect extraction: keyword matching against a curated product-review lexicon.
       - Sentiment classification: context-window scoring with a 200-word
         positive/negative/negation dictionary — works for EN and HI.
     No external downloads. Starts instantly.
"""

import os
import re
import time
import threading
from pathlib import Path
from typing import List, Tuple
import numpy as np

from api.models.schemas import PredictionResponse, AspectSentiment
from api.services.lang_service import lang_service

# ── Optional heavy imports (ONNX custom models) ───────────────────────────────
try:
    from optimum.onnxruntime import (
        ORTModelForTokenClassification,
        ORTModelForSequenceClassification,
    )
    from transformers import AutoTokenizer

    OPTIMUM_AVAILABLE = True
except ImportError:
    try:
        from transformers import AutoTokenizer

        OPTIMUM_AVAILABLE = False
    except ImportError:
        OPTIMUM_AVAILABLE = False

# ── Aspect keyword lexicon ────────────────────────────────────────────────────
# Ordered longest-first so multi-word matches win over single words.
ASPECT_PHRASES: List[str] = sorted(
    [
        # Audio
        "sound quality",
        "audio quality",
        "bass response",
        "bass",
        "treble",
        "noise cancellation",
        "active noise cancellation",
        "anc",
        "passive noise isolation",
        "microphone quality",
        "microphone",
        "mic",
        "speakers",
        "speaker",
        "audio",
        "sound",
        "volume",
        # Battery / Power
        "battery life",
        "battery performance",
        "charging speed",
        "fast charging",
        "wireless charging",
        "charging case",
        "battery",
        "charging",
        "power",
        # Design / Build
        "build quality",
        "build",
        "design",
        "comfort",
        "fit and finish",
        "ergonomics",
        "weight",
        "size",
        "material",
        "finish",
        "durability",
        # Connectivity
        "bluetooth connectivity",
        "bluetooth",
        "wifi",
        "wi-fi",
        "connectivity",
        "wireless connection",
        "pairing",
        "latency",
        "lag",
        # Display
        "display quality",
        "screen quality",
        "display",
        "screen",
        "resolution",
        "brightness",
        "touchscreen",
        # Camera
        "camera quality",
        "image quality",
        "video quality",
        "camera",
        "lens",
        "photo",
        # Performance
        "performance",
        "processing speed",
        "speed",
        "processor",
        "ram",
        "memory",
        "loading time",
        # Software / Features
        "user interface",
        "software",
        "app",
        "features",
        "controls",
        "buttons",
        "touch controls",
        # Value
        "value for money",
        "price",
        "cost",
        "value",
        # Support / Delivery
        "customer service",
        "customer support",
        "warranty",
        "delivery",
        "packaging",
        # General
        "quality",
        "reliability",
        "overall experience",
    ],
    key=len,
    reverse=True,
)

# ── Sentiment lexicon ─────────────────────────────────────────────────────────
POSITIVE_WORDS = {
    "excellent",
    "great",
    "amazing",
    "outstanding",
    "superb",
    "fantastic",
    "wonderful",
    "perfect",
    "impressive",
    "exceptional",
    "brilliant",
    "splendid",
    "good",
    "nice",
    "solid",
    "strong",
    "reliable",
    "consistent",
    "smooth",
    "clear",
    "crisp",
    "rich",
    "deep",
    "powerful",
    "comfortable",
    "enjoyable",
    "satisfied",
    "happy",
    "love",
    "loved",
    "like",
    "loved",
    "commendable",
    "recommend",
    "recommended",
    "worth",
    "affordable",
    "value",
    "effective",
    "efficient",
    "accurate",
    "precise",
    "sharp",
    "vibrant",
    "vivid",
    "fast",
    "quick",
    "snappy",
    "instant",
    "stable",
    "durable",
    "sturdy",
    "premium",
    "high-quality",
    "high quality",
    "top-notch",
    "top notch",
    "long",
    "lasting",
    "enduring",
    "impressive",
    "praise",
    "appreciate",
    # Hindi positive (transliterated)
    "badhiya",
    "achha",
    "accha",
    "shandar",
    "zabardast",
    "mast",
}

NEGATIVE_WORDS = {
    "bad",
    "poor",
    "terrible",
    "awful",
    "horrible",
    "dreadful",
    "atrocious",
    "disappointing",
    "disappointed",
    "mediocre",
    "weak",
    "subpar",
    "inferior",
    "cheap",
    "flimsy",
    "fragile",
    "unreliable",
    "inconsistent",
    "unstable",
    "slow",
    "sluggish",
    "laggy",
    "lag",
    "delay",
    "delayed",
    "glitchy",
    "buggy",
    "noisy",
    "distorted",
    "muffled",
    "blurry",
    "dim",
    "dull",
    "flat",
    "short",
    "low",
    "limited",
    "lacking",
    "missing",
    "absent",
    "expensive",
    "overpriced",
    "pricey",
    "costly",
    "uncomfortable",
    "annoying",
    "frustrating",
    "irritating",
    "failed",
    "failure",
    "broken",
    "defective",
    "faulty",
    "average",
    "ordinary",
    "basic",
    "minimal",
    # Hindi negative (transliterated)
    "kharab",
    "bekaar",
    "bura",
    "ganda",
    "faltu",
}

NEGATION_WORDS = {
    "not",
    "no",
    "never",
    "neither",
    "nor",
    "barely",
    "hardly",
    "scarcely",
    "doesn't",
    "don't",
    "didn't",
    "isn't",
    "aren't",
    "wasn't",
    "weren't",
    "without",
    "lack",
    "lacks",
    "lacking",
    "failed",
    "fails",
}

INTENSIFIERS = {
    "very",
    "extremely",
    "incredibly",
    "absolutely",
    "truly",
    "really",
    "highly",
    "remarkably",
    "exceptionally",
    "super",
    "too",
}


def _score_sentence(sentence: str) -> Tuple[float, float]:
    """
    Return (positive_score, negative_score) for a sentence.
    Handles negation (3-word window) and intensifiers.
    """
    words = re.findall(r"\b[\w'-]+\b", sentence.lower())
    pos, neg = 0.0, 0.0
    i = 0
    while i < len(words):
        w = words[i]
        # Look-back for negation in previous 3 words
        context = words[max(0, i - 3) : i]
        negated = any(n in context for n in NEGATION_WORDS)
        # Look-back for intensifier
        intensity = 1.5 if any(t in context for t in INTENSIFIERS) else 1.0

        if w in POSITIVE_WORDS:
            if negated:
                neg += 1.0 * intensity
            else:
                pos += 1.0 * intensity
        elif w in NEGATIVE_WORDS:
            if negated:
                pos += 0.5 * intensity
            else:
                neg += 1.0 * intensity
        i += 1
    return pos, neg


def _score_to_label(pos: float, neg: float) -> Tuple[str, float]:
    """Convert raw scores to (label, confidence)."""
    total = pos + neg
    if total == 0:
        return "neutral", 0.60
    ratio = pos / total
    if ratio > 0.60:
        confidence = min(0.55 + ratio * 0.40, 0.97)
        return "positive", round(confidence, 3)
    elif ratio < 0.40:
        confidence = min(0.55 + (1 - ratio) * 0.40, 0.97)
        return "negative", round(confidence, 3)
    return "neutral", round(0.50 + abs(ratio - 0.5) * 0.6, 3)


# ── Main pipeline class ───────────────────────────────────────────────────────


class ABSAPipeline:
    def __init__(self):
        self.tokenizer = None
        self.aspect_model = None
        self.sentiment_model = None
        self.is_loaded = False
        self._lock = threading.Lock()

        self.id2label = {0: "O", 1: "B-ASP", 2: "I-ASP"}
        self.sentiment_id2label = {
            0: "positive",
            1: "negative",
            2: "neutral",
            3: "conflict",
        }

    def load_models(self):
        """Try to load custom ONNX models; mark ready immediately (no downloads)."""
        model_path_base = Path(os.getenv("MODEL_PATH", "models/onnx"))
        hf_repo_id = os.getenv("HF_MODEL_REPO", "")
        use_hub = os.getenv("MODEL_SOURCE", "local") == "huggingface_hub" and hf_repo_id

        if OPTIMUM_AVAILABLE and use_hub:
            try:
                print(f"Loading custom models from HF Hub: {hf_repo_id}")
                self.tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
                self.aspect_model = ORTModelForTokenClassification.from_pretrained(
                    hf_repo_id, subfolder="aspect_extraction_int8"
                )
                self.sentiment_model = (
                    ORTModelForSequenceClassification.from_pretrained(
                        hf_repo_id, subfolder="sentiment_int8"
                    )
                )
                print("Custom ONNX models loaded.")
            except Exception as e:
                print(f"Custom model load skipped: {e}")

        elif OPTIMUM_AVAILABLE:
            aspect_path = model_path_base / "aspect_extraction_int8"
            sentiment_path = model_path_base / "sentiment_int8"
            if not aspect_path.exists():
                aspect_path = model_path_base / "aspect_extraction"
            if not sentiment_path.exists():
                sentiment_path = model_path_base / "sentiment"

            if aspect_path.exists() and sentiment_path.exists():
                try:
                    print(f"Loading custom ONNX models from {model_path_base}")
                    self.tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
                    self.aspect_model = ORTModelForTokenClassification.from_pretrained(
                        str(aspect_path)
                    )
                    self.sentiment_model = (
                        ORTModelForSequenceClassification.from_pretrained(
                            str(sentiment_path)
                        )
                    )
                    print("Custom ONNX models loaded.")
                except Exception as e:
                    print(f"Custom model load skipped: {e}")

        if not self.aspect_model:
            print("No custom models found — using built-in rule-based ABSA engine.")

        self.is_loaded = True

    def predict(self, text: str, requested_lang: str = None) -> PredictionResponse:
        start = time.time()
        detected_lang = lang_service.detect_language(text)
        actual_lang = requested_lang or detected_lang

        if self.aspect_model:
            aspects = self._predict_onnx(text)
        else:
            aspects = self._predict_rule_based(text)

        return PredictionResponse(
            text=text,
            language=actual_lang,
            detected_language=detected_lang,
            aspects=aspects,
            processing_time_ms=(time.time() - start) * 1000,
        )

    def predict_batch(self, texts: List[str]) -> List[PredictionResponse]:
        return [self.predict(t) for t in texts]

    # ── Custom ONNX path ──────────────────────────────────────────────────────

    def _predict_onnx(self, text: str) -> List[AspectSentiment]:
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=128
        )
        logits = self.aspect_model(**inputs).logits[0].detach().numpy()
        preds = np.argmax(logits, axis=1)
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        raw, current, start_idx = [], [], -1
        skip = {
            self.tokenizer.cls_token,
            self.tokenizer.sep_token,
            self.tokenizer.pad_token,
        }
        for idx, (tok, pred) in enumerate(zip(tokens, preds)):
            if tok in skip:
                continue
            label = self.id2label.get(int(pred), "O")
            if label == "B-ASP":
                if current:
                    raw.append((" ".join(current).strip(), start_idx, idx - 1))
                current, start_idx = [tok], idx
            elif label == "I-ASP" and current:
                current.append(tok)
            else:
                if current:
                    raw.append((" ".join(current).strip(), start_idx, idx - 1))
                    current = []
        if current:
            raw.append((" ".join(current).strip(), start_idx, len(tokens) - 1))

        results = []
        for asp_text, s, e in raw:
            seq_in = self.tokenizer(
                text,
                text_pair=asp_text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
            )
            sent_logits = self.sentiment_model(**seq_in).logits[0].detach().numpy()
            exp = np.exp(sent_logits - sent_logits.max())
            probs = exp / exp.sum()
            cls = int(np.argmax(probs))
            results.append(
                AspectSentiment(
                    aspect=asp_text,
                    sentiment=self.sentiment_id2label.get(cls, "neutral"),
                    confidence=round(float(probs[cls]), 3),
                    start=s,
                    end=e,
                )
            )
        return results

    # ── Rule-based path ───────────────────────────────────────────────────────

    def _predict_rule_based(self, text: str) -> List[AspectSentiment]:
        text_lower = text.lower()
        sentences = re.split(r"(?<=[.!?])\s+", text)
        found_aspects = self._extract_aspects(text_lower)

        results = []
        for aspect_label, start_char, end_char in found_aspects:
            # Find the sentence(s) mentioning this aspect for focused scoring
            aspect_lower = aspect_label.lower()
            context_sentences = [s for s in sentences if aspect_lower in s.lower()] or [
                text
            ]
            context = " ".join(context_sentences)

            pos, neg = _score_sentence(context)

            # Also score the full text with lower weight
            full_pos, full_neg = _score_sentence(text)
            pos += full_pos * 0.3
            neg += full_neg * 0.3

            sentiment, confidence = _score_to_label(pos, neg)
            results.append(
                AspectSentiment(
                    aspect=aspect_label,
                    sentiment=sentiment,
                    confidence=confidence,
                    start=start_char,
                    end=end_char,
                )
            )
        return results

    def _extract_aspects(self, text_lower: str) -> List[Tuple[str, int, int]]:
        """Find aspect keyword matches; return (label, start, end) sorted by position."""
        found: List[Tuple[str, int, int]] = []
        seen_ranges: List[Tuple[int, int]] = []

        for phrase in ASPECT_PHRASES:
            for m in re.finditer(re.escape(phrase), text_lower):
                s, e = m.start(), m.end()
                # Skip if overlaps an already-matched longer phrase
                if any(s >= r0 and e <= r1 for r0, r1 in seen_ranges):
                    continue
                label = phrase.title()
                found.append((label, s, e))
                seen_ranges.append((s, e))
                break  # one match per phrase

        found.sort(key=lambda x: x[1])
        return found


pipeline = ABSAPipeline()
