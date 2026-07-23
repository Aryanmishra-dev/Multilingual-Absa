import pytest
from absa.data.bio_tagger import convert_to_bio, bio_to_aspects

def test_single_aspect():
    text = "The food was amazing."
    aspects = [{"term": "food", "from": 4, "to": 8}]
    tags = convert_to_bio(text, aspects)
    
    assert [t['token'] for t in tags] == ["The", "food", "was", "amazing."]
    assert [t['label'] for t in tags] == ["O", "B-ASP", "O", "O"]

def test_multiple_aspects():
    text = "The food was good, but the service was terrible."
    aspects = [
        {"term": "food", "from": 4, "to": 8},
        {"term": "service", "from": 27, "to": 34}
    ]
    tags = convert_to_bio(text, aspects)
    
    expected_labels = ["O", "B-ASP", "O", "O", "O", "O", "B-ASP", "O", "O"]
    assert [t['label'] for t in tags] == expected_labels

def test_no_aspects():
    text = "Everything was fine."
    aspects = []
    tags = convert_to_bio(text, aspects)
    
    assert all(t['label'] == "O" for t in tags)

def test_multi_word_aspect():
    text = "The operating system is very stable."
    aspects = [{"term": "operating system", "from": 4, "to": 20}]
    tags = convert_to_bio(text, aspects)
    
    assert [t['label'] for t in tags] == ["O", "B-ASP", "I-ASP", "O", "O", "O"]

def test_adjacent_aspects():
    text = "Great battery life." # Suppose battery and life are separate
    aspects = [
        {"term": "battery", "from": 6, "to": 13},
        {"term": "life.", "from": 14, "to": 19}
    ]
    tags = convert_to_bio(text, aspects)
    assert [t['label'] for t in tags] == ["O", "B-ASP", "B-ASP"]
    
def test_bio_to_aspects():
    tokens = ["The", "operating", "system", "and", "battery", "life", "are", "great"]
    labels = ["O", "B-ASP", "I-ASP", "O", "B-ASP", "B-ASP", "O", "O"]
    
    extracted = bio_to_aspects(tokens, labels)
    assert extracted == ["operating system", "battery", "life"]
