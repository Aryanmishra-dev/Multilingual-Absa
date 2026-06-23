import urllib.request
from pathlib import Path
import json
import pandas as pd
from datasets import load_dataset

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import RAW_DIR, DATA_DIR

FASTTEXT_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
FASTTEXT_DEST = DATA_DIR / "models" / "lid.176.ftz"


def download_fasttext() -> dict:
    FASTTEXT_DEST.parent.mkdir(parents=True, exist_ok=True)
    if FASTTEXT_DEST.exists():
        size = FASTTEXT_DEST.stat().st_size
        print(f"  ✓ fasttext LID model already exists ({size / 1e6:.1f} MB)")
        return {"status": "skipped", "size_mb": round(size / 1e6, 1)}
    print(f"  Downloading fasttext LID model from {FASTTEXT_URL}...")
    urllib.request.urlretrieve(FASTTEXT_URL, FASTTEXT_DEST)
    size = FASTTEXT_DEST.stat().st_size
    print(f"  ✓ Downloaded ({size / 1e6:.1f} MB)")
    return {"status": "downloaded", "size_mb": round(size / 1e6, 1)}


def download_semeval_laptops() -> dict:
    dest = RAW_DIR / "semeval_laptops"
    dest.mkdir(parents=True, exist_ok=True)
    print("  Loading SemEval 2014 Laptops...")
    dataset = load_dataset("jakartaresearch/semeval-absa", "laptop")
    counts = {}
    for split in dataset:
        path = dest / f"{split}.jsonl"
        dataset[split].to_json(path)
        counts[split] = len(dataset[split])
        print(f"  ✓ {split}: {len(dataset[split])} samples -> {path}")
    return counts


def download_semeval_restaurants() -> dict:
    dest = RAW_DIR / "semeval_restaurants"
    dest.mkdir(parents=True, exist_ok=True)
    print("  Loading SemEval 2014 Restaurants...")
    dataset = load_dataset("jakartaresearch/semeval-absa", "restaurant")
    counts = {}
    for split in dataset:
        path = dest / f"{split}.jsonl"
        dataset[split].to_json(path)
        counts[split] = len(dataset[split])
        print(f"  ✓ {split}: {len(dataset[split])} samples -> {path}")
    return counts


def download_amazon_hindi() -> dict:
    dest = RAW_DIR / "amazon_hindi"
    dest.mkdir(parents=True, exist_ok=True)
    print("  Loading Hindi Amazon reviews...")

    base_url = "https://raw.githubusercontent.com/Udrasht/Hindi-Sentiment-Analysis-Corpus-from-Amazon-Reviews/main/data"

    for split, fname in [("train", "train.xlsx"), ("test", "test.xlsx")]:
        url = f"{base_url}/{fname}"
        print(f"  Downloading {split} from {url}...")
        df = pd.read_excel(url)
        records = []
        for _, row in df.iterrows():
            records.append({
                "text": row["content_hindi"],
                "title": row["title_hindi"],
                "rating": int(row["rating"]),
                "label": row["labels"],
            })
        path = dest / f"{split}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  ✓ {split}: {len(records)} samples -> {path}")

    return {"train": 3527, "test": 884}


def main():
    results = {}
    print("\n=== Downloading fasttext LID model ===")
    results["fasttext"] = download_fasttext()

    print("\n=== Downloading SemEval 2014 Laptops ===")
    results["semeval_laptops"] = download_semeval_laptops()

    print("\n=== Downloading SemEval 2014 Restaurants ===")
    results["semeval_restaurants"] = download_semeval_restaurants()

    print("\n=== Downloading Hindi Amazon reviews ===")
    results["amazon_hindi"] = download_amazon_hindi()

    print("\n" + "=" * 50)
    print("DOWNLOAD SUMMARY")
    print("=" * 50)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
