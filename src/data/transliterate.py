import logging
import unicodedata
import re
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from indicnlp.transliterate.unicode_transliterate import ItransTransliterator
    HAS_INDIC_NLP = True
except ImportError:
    HAS_INDIC_NLP = False
    logger.warning("indic-nlp-library not found. Transliteration will fallback to basic unicode handling.")

def transliterate(text: str, src_lang: str) -> str:
    """Romanize Devanagari text."""
    if src_lang not in ["hi", "hinglish"]:
        return text
        
    if HAS_INDIC_NLP:
        try:
            # We will process word by word if needed, but itrans translates string.
            # actually to_itrans takes devanagari and romanizes it.
            roman_text = ItransTransliterator.to_itrans(text, "hi")
        except Exception as e:
            logger.warning(f"indicnlp transliteration failed: {e}")
            roman_text = text
    else:
        # Fallback to basic unicode normalization
        roman_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    if not roman_text:
        roman_text = text
        
    # Normalize common Hinglish spellings
    # replace acha / accha -> achha
    roman_text = re.sub(r'\baccha\b', 'achha', roman_text, flags=re.IGNORECASE)
    roman_text = re.sub(r'\bacha\b', 'achha', roman_text, flags=re.IGNORECASE)
    
    return roman_text
