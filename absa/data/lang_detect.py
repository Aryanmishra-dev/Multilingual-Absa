import re
import fasttext
from absa.utils.config import FASTTEXT_MODEL_PATH

_model = None


def get_model():
    global _model
    if _model is None:
        _model = fasttext.load_model(str(FASTTEXT_MODEL_PATH))
    return _model


def detect_language(text: str) -> str:
    """Detects if text is en, hi, hinglish, or other.

    Args:
        text: The text to analyze.

    Returns:
        String representing language code ('en', 'hi', 'hinglish', or 'other').
    """
    if not text or not text.strip():
        return "other"

    has_alpha = bool(re.search(r"[^\W\d_]", text))
    if not has_alpha:
        return "other"

    text = text.replace("\n", " ")
    model = get_model()
    predictions = model.predict(text, k=1)
    label = predictions[0][0].replace("__label__", "")

    has_latin = bool(re.search(r"[a-zA-Z]", text))
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))

    is_hinglish = has_latin and has_devanagari

    if is_hinglish and label in ["en", "hi"]:
        return "hinglish"

    if label == "en":
        return "en"
    elif label == "hi":
        return "hi"
    else:
        return "other"
