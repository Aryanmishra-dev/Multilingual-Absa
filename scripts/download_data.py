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
    restaurants = load_dataset("tomaarsen/absa-semeval-2014-restaurants")
    laptops = load_dataset("tomaarsen/absa-semeval-2014-laptops")
    
    rest_path = RAW_DIR / "semeval_restaurants"
    lap_path = RAW_DIR / "semeval_laptops"
    
    restaurants.save_to_disk(str(rest_path))
    laptops.save_to_disk(str(lap_path))
    
    print(f"SemEval Restaurants train samples: {len(restaurants['train'])}")
    print(f"SemEval Laptops train samples: {len(laptops['train'])}")

def download_amazon_hindi():
    print("Downloading Amazon Hindi dataset...")
    # Load just 5000 from train
    amz_hi = load_dataset("amazon_reviews_multi", "hi", split="train[:5000]")
    
    amz_path = RAW_DIR / "amazon_hindi"
    amz_hi.save_to_disk(str(amz_path))
    
    print(f"Amazon Hindi train samples: {len(amz_hi)}")

if __name__ == "__main__":
    os.makedirs(RAW_DIR, exist_ok=True)
    download_fasttext()
    download_semeval()
    download_amazon_hindi()
    print("Download complete.")
