import json
from absa.utils.config import RAW_DIR, AMAZON_HINDI_PATH
from absa.data.preprocess import clean
from absa.data.lang_detect import detect_language


def process_hindi():
    raw_path = RAW_DIR / "amazon_hindi" / "hindi_sentiment.jsonl"
    if not raw_path.exists():
        print(f"File not found: {raw_path}")
        return

    AMAZON_HINDI_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    lang_counts = {"hi": 0, "hinglish": 0, "en": 0, "other": 0}

    with open(raw_path, "r", encoding="utf-8") as fin, open(
        AMAZON_HINDI_PATH, "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            row = json.loads(line)
            text = row.get("INDIC REVIEW", row.get("text", ""))
            if not text:
                continue

            label = str(row.get("LABEL", row.get("label", ""))).lower()
            if label == "0" or label == "negative":
                label = "negative"
            elif label == "1" or label == "positive":
                label = "positive"
            else:
                label = "neutral"

            lang = detect_language(text)
            if lang in lang_counts:
                lang_counts[lang] += 1
            else:
                lang_counts[lang] = 1

            cleaned_text = clean(text, lang)

            sample = {
                "text": cleaned_text,
                "language": lang,
                "label": label,
                "source": "amazon_hindi",
            }
            fout.write(json.dumps(sample, ensure_ascii=False) + "\n")
            total += 1

    print(f"Hindi samples processed: {total}")
    print(f"Hindi language distribution: {lang_counts}")


if __name__ == "__main__":
    process_hindi()
