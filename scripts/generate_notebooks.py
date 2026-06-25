import json
from pathlib import Path

def create_notebook(filename: str, cells_content: list):
    cells = []
    for content, cell_type in cells_content:
        cells.append({
            "cell_type": cell_type,
            "metadata": {},
            "execution_count": None if cell_type == "code" else None,
            "outputs": [] if cell_type == "code" else None,
            "source": [line + "\n" for line in content.split("\n")]
        })
        
        # Clean up outputs/execution_count for markdown
        if cell_type == "markdown":
            del cells[-1]["execution_count"]
            del cells[-1]["outputs"]

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    Path("notebooks").mkdir(parents=True, exist_ok=True)
    with open(f"notebooks/{filename}", "w") as f:
        json.dump(notebook, f, indent=2)

def main():
    colab_cells = [
        ("# Google Colab Training Notebook\n\nThis notebook is intended to be run on Google Colab with a T4 GPU. It clones the repo, installs dependencies, and runs the training scripts.", "markdown"),
        ("!git clone https://github.com/Aryanmishra-dev/Multilingual-Absa.git\n%cd Multilingual-Absa\n!pip install -r requirements.txt", "code"),
        ("# Mount Google Drive to save models and MLflow logs persistently\nfrom google.colab import drive\ndrive.mount('/content/drive')", "code"),
        ("# Create symlinks or copy data if needed\n# Assuming data is in the repo for now\n!mkdir -p /content/drive/MyDrive/ABSA_models", "code"),
        ("# Prepare dataset\n!PYTHONPATH=. python src/data/hf_dataset.py", "code"),
        ("# Run Aspect Extraction Training\n!PYTHONPATH=. python src/models/train_aspect_extraction.py", "code"),
        ("# Run Sentiment Classification Training\n!PYTHONPATH=. python src/models/train_sentiment.py", "code"),
        ("# Run Baseline as well\n!PYTHONPATH=. python src/models/baseline.py", "code"),
        ("# Cross-lingual Evaluation\n!PYTHONPATH=. python src/evaluation/cross_lingual_eval.py", "code"),
        ("# Copy models back to Drive\n!cp -r models/* /content/drive/MyDrive/ABSA_models/\n!cp -r mlflow /content/drive/MyDrive/ABSA_models/", "code")
    ]
    
    comparison_cells = [
        ("# Model Comparison\n\nThis notebook connects to the MLflow tracking server and compares the results of our models.", "markdown"),
        ("import mlflow\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport json\n\nmlflow.set_tracking_uri('sqlite:///mlflow/mlflow.db')", "code"),
        ("# Load all runs\nexperiment = mlflow.get_experiment_by_name('multilingual-absa')\ndf = mlflow.search_runs(experiment_ids=[experiment.experiment_id])\ndisplay(df.head())", "code"),
        ("# Bar chart: macro-F1 comparison\nmetrics = df[['tags.mlflow.runName', 'metrics.eval_macro_f1', 'metrics.test_f1', 'metrics.test_macro_f1', 'metrics.hindi_zero_shot_macro_f1']].fillna(0)\nmetrics['Best F1'] = metrics[['metrics.eval_macro_f1', 'metrics.test_f1', 'metrics.test_macro_f1']].max(axis=1)\n\nplt.figure(figsize=(10, 6))\nsns.barplot(data=metrics, x='tags.mlflow.runName', y='Best F1')\nplt.title('Model Comparison by Macro-F1 / Span-F1')\nplt.xticks(rotation=45)\nplt.show()", "code"),
        ("# Load confusion matrix for best sentiment classifier\n# Note: Assuming the confusion_matrix.json artifact was downloaded or parsed.\nprint('Confusion Matrix (Placeholder for artifact loading)')", "code"),
        ("# 5 Example Predictions\nprint('Example 1: The food was great but service was slow.')\nprint('Example 2: El sistema operativo es muy estable.')\nprint('... (Load pipeline and infer here)')", "code")
    ]
    
    create_notebook("03_train_colab.ipynb", colab_cells)
    create_notebook("03_model_comparison.ipynb", comparison_cells)

if __name__ == '__main__':
    main()
