from src.data.lang_detect import detect_language

def test_detect_language():
    samples = [
        ("This is a simple English sentence.", "en"),
        ("The food was amazing!", "en"),
        ("यह एक हिंदी वाक्य है।", "hi"),
        ("मुझे यह उत्पाद बहुत पसंद आया।", "hi"),
        ("The phone is great but battery life kharab hai.", "en"), # no devanagari -> en
        ("Phone bahut badhiya hai, लेकिन battery is bad.", "hinglish"),
        ("I love this! मुझे यह पसंद है", "hinglish"),
        ("Bonjour tout le monde", "other"),
        ("12345 67890 !@#", "other"),
        ("Just english text with 123", "en"),
        ("सिर्फ हिंदी 123", "hi")
    ]
    for text, expected in samples:
        assert detect_language(text) == expected, f"Failed on '{text}', expected {expected}"
