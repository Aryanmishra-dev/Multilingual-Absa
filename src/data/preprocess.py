import re
import unicodedata
from src.data.transliterate import transliterate

def clean(text: str, language: str) -> str:
    """Clean text by lowercasing, removing URLs/mentions/hashtags, normalizing unicode, stripping whitespace."""
    if not text:
        return ""
        
    # lowercase
    text = text.lower()
    
    # remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    
    # remove mentions
    text = re.sub(r'@\w+', '', text)
    
    # remove hashtags
    text = re.sub(r'#\w+', '', text)
    
    # Apply transliteration only for hi/hinglish inputs
    if language in ["hi", "hinglish"]:
        text = transliterate(text, language)
        
    # normalize unicode
    text = unicodedata.normalize("NFKC", text)
    
    # strip whitespace
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    
    return text
