import os
import urllib.request
from datasets import load_dataset
from src.config import DATA_DIR, RAW_DIR, FASTTEXT_MODEL_PATH

def download_fasttext():
    url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"
    os.makedirs(FASTTEXT_MODEL_PATH.parent, exist_ok=True)
    if not FASTTEXT_MODEL_PATH.exists():
        print("Downloading fastText LID model...")
        urllib.request.urlretrieve(url, FASTTEXT_MODEL_PATH)
    else:
        print("fastText LID model already exists.")
    print(f"fastText model size: {os.path.getsize(FASTTEXT_MODEL_PATH) / 1024 / 1024:.2f} MB")

def download_semeval():
    print("Downloading SemEval datasets...")
    restaurants = load_dataset("tomaarsen/setfit-absa-semeval-restaurants")
    laptops = load_dataset("tomaarsen/setfit-absa-semeval-laptops")
    
    rest_path = RAW_DIR / "semeval_restaurants"
    lap_path = RAW_DIR / "semeval_laptops"
    
    restaurants.save_to_disk(str(rest_path))
    laptops.save_to_disk(str(lap_path))
    
    print(f"SemEval Restaurants train samples: {len(restaurants['train'])}")
    print(f"SemEval Laptops train samples: {len(laptops['train'])}")

def download_amazon_hindi():
    print("Downloading Amazon Hindi dataset...")
    ds = load_dataset("ai4bharat/IndicSentiment", "translation-hi", 
                      trust_remote_code=True, split="test")
    
    amz_path = RAW_DIR / "amazon_hindi"
    os.makedirs(amz_path, exist_ok=True)
    file_path = amz_path / "hindi_sentiment.jsonl"
    ds.to_json(str(file_path))
    print(f"Downloaded {len(ds)} Hindi samples")

if __name__ == "__main__":
    os.makedirs(RAW_DIR, exist_ok=True)
    download_fasttext()
    download_semeval()
    download_amazon_hindi()
    print("Download complete.")
