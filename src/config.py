from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT_DIR / "models"
MLFLOW_DIR = ROOT_DIR / "mlflow"

FASTTEXT_MODEL_PATH = DATA_DIR / "models" / "lid.176.ftz"
SEMEVAL_TRAIN_PATH = PROCESSED_DIR / "semeval_train.jsonl"
SEMEVAL_TEST_PATH = PROCESSED_DIR / "semeval_test.jsonl"
AMAZON_HINDI_PATH = PROCESSED_DIR / "amazon_hindi.jsonl"

XLM_ROBERTA_MODEL = "xlm-roberta-base"
INDICBERT_MODEL = "ai4bharat/indic-bert"
MAX_SEQ_LENGTH = 128
SEED = 42

SENTIMENT_LABELS = ["positive", "negative", "neutral", "conflict"]
BIO_LABELS = ["O", "B-ASP", "I-ASP"]
