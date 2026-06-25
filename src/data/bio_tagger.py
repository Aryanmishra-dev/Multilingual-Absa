import re
from typing import List, Dict, Any, Tuple

def tokenize(text: str) -> List[Tuple[str, int, int]]:
    """
    Tokenizes text by words, returning tokens and their start/end character offsets.
    Uses simple regex based tokenization to preserve whitespace semantics for BIO tagging.
    """
    tokens = []
    # Match non-whitespace characters
    for match in re.finditer(r'\S+', text):
        tokens.append((match.group(), match.start(), match.end()))
    return tokens

def convert_to_bio(text: str, aspect_terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts text and aspect spans to BIO tagged tokens.
    
    Args:
        text: The input review string.
        aspect_terms: List of dictionaries with 'term', 'from', and 'to' keys.
        
    Returns:
        List of dictionaries with 'token' and 'label' (B-ASP, I-ASP, O).
    """
    tokens = tokenize(text)
    
    # Sort aspects by start index
    sorted_aspects = sorted(aspect_terms, key=lambda x: x['from'])
    
    bio_tags = []
    aspect_idx = 0
    num_aspects = len(sorted_aspects)
    
    for token_str, t_start, t_end in tokens:
        label = "O"
        
        # Move aspect pointer if we've passed the current aspect completely
        while aspect_idx < num_aspects and sorted_aspects[aspect_idx]['to'] <= t_start:
            aspect_idx += 1
            
        if aspect_idx < num_aspects:
            curr_aspect = sorted_aspects[aspect_idx]
            a_start = curr_aspect['from']
            a_end = curr_aspect['to']
            
            # Check overlap
            if not (t_end <= a_start or t_start >= a_end):
                # There is overlap
                # If this token overlaps with the start of the aspect
                if t_start <= a_start or (len(bio_tags) > 0 and bio_tags[-1]['label'] == "O" and t_start > a_start):
                     label = "B-ASP"
                else:
                     # Check if previous tag was B-ASP or I-ASP for the *same* aspect
                     if len(bio_tags) > 0 and bio_tags[-1]['label'] in ("B-ASP", "I-ASP"):
                         label = "I-ASP"
                     else:
                         label = "B-ASP"
                         
        bio_tags.append({"token": token_str, "label": label})
        
    return bio_tags

def bio_to_aspects(tokens: List[str], labels: List[str]) -> List[str]:
    """
    Converts BIO tags back to a list of aspect terms.
    
    Args:
        tokens: List of string tokens.
        labels: List of BIO labels corresponding to the tokens.
        
    Returns:
        List of extracted aspect term strings.
    """
    aspects = []
    current_aspect = []
    
    for token, label in zip(tokens, labels):
        if label == "B-ASP":
            if current_aspect:
                aspects.append(" ".join(current_aspect))
            current_aspect = [token]
        elif label == "I-ASP":
            if current_aspect:
                current_aspect.append(token)
            else:
                # Invalid sequence (I-ASP without B-ASP), treat as B-ASP
                current_aspect = [token]
        else: # O
            if current_aspect:
                aspects.append(" ".join(current_aspect))
                current_aspect = []
                
    if current_aspect:
        aspects.append(" ".join(current_aspect))
        
    return aspects
