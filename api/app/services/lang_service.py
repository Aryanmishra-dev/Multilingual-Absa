import fasttext
from pathlib import Path


class LanguageService:
    def __init__(self):
        # Using a simple heuristic or fasttext if available.
        # For this phase, we'll try to load a fasttext model if it exists,
        # otherwise fallback to simple heuristics.
        self.model = None
        model_path = Path("models/lid.176.ftz")
        if model_path.exists():
            self.model = fasttext.load_model(str(model_path))

    def detect_language(self, text: str) -> str:
        if self.model:
            predictions = self.model.predict(text.replace("\n", " "), k=1)
            lang = predictions[0][0].replace("__label__", "")
            if lang in ["en", "hi"]:
                return lang
            # Default to en if unknown or other
            return "en"
        else:
            # Simple heuristic fallback
            hindi_chars = sum(1 for c in text if "\u0900" <= c <= "\u097f")
            if hindi_chars > 0:
                return "hi"
            return "en"


lang_service = LanguageService()
