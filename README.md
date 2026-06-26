## Project Overview
Multilingual Aspect-Based Sentiment Analysis (ABSA) supporting English, Hindi, and Hinglish. It leverages XLM-RoBERTa and IndicBERT to perform aspect term extraction and sentiment classification for multilingual product reviews.

## Repo Structure
Multilingual-Absa/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── config/                 # Configuration files
│   ├── docker/             # docker-compose.yml, docker-compose.prod.yml
│   └── dvc.yaml            # DVC pipeline config
├── src/                    # ML source code
├── api/                    # API source code
├── dashboard/              # Frontend dashboard
├── tests/                  # All tests
├── scripts/                # Utility/automation scripts
├── notebooks/              # Jupyter notebooks
├── docs/                   # Documentation
├── data/                   # Gitignored, DVC-tracked only
├── models/                 # Gitignored, DVC-tracked only
├── .dvcignore
├── .env.example            # Template only
├── .gitignore
├── .gitattributes
├── AGENTS.md
├── README.md
├── requirements.txt
├── railway.json            # GITIGNORED, stays local only
└── dvc.lock

## Setup
```bash
# 1. Clone and install
git clone <repository-url>
pip install -r requirements.txt

# 2. Copy env template
cp .env.example .env
# Fill in your values in .env

# 3. Run with Docker
docker-compose -f config/docker/docker-compose.yml up
```

## ML Pipeline (DVC)
```bash
dvc repro        # Run full pipeline
dvc push         # Push data/models to remote
```

## API
```bash
cd api && uvicorn main:app --reload
```
