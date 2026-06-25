import mlflow
from typing import Dict, Any, Optional
from pathlib import Path
import os

# Default configuration
MLFLOW_TRACKING_URI = "sqlite:///mlflow/mlflow.db"
EXPERIMENT_NAME = "multilingual-absa"

def setup_mlflow():
    """Initializes MLflow tracking URI and experiment."""
    # Ensure the directory exists
    Path("mlflow").mkdir(parents=True, exist_ok=True)
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

def log_training_run(params: Dict[str, Any], metrics: Dict[str, float], model_path: Optional[str | Path] = None, run_name: Optional[str] = None) -> str:
    """
    Logs parameters, metrics, and optionally a model artifact to MLflow.
    
    Args:
        params: Dictionary of hyperparameters or configuration.
        metrics: Dictionary of evaluation metrics.
        model_path: Path to the saved model directory or file.
        run_name: Optional name for the run.
        
    Returns:
        The ID of the created MLflow run.
    """
    setup_mlflow()
    
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        
        if model_path:
            model_path_obj = Path(model_path)
            if model_path_obj.exists():
                mlflow.log_artifact(str(model_path_obj), artifact_path="model")
            else:
                print(f"Warning: Model path {model_path} does not exist. Artifact not logged.")
                
        return run.info.run_id

def get_best_run(metric: str = "eval_macro_f1", ascending: bool = False) -> Optional[mlflow.entities.Run]:
    """
    Retrieves the best run from the experiment based on a specific metric.
    
    Args:
        metric: The metric to sort by.
        ascending: True if a lower metric is better (e.g., loss), False for higher is better (e.g., F1).
        
    Returns:
        The MLflow Run object for the best run, or None if no runs exist.
    """
    setup_mlflow()
    
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if not experiment:
        return None
        
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} {'ASC' if ascending else 'DESC'}"],
        max_results=1,
        output_format="list"
    )
    
    if not runs:
        return None
        
    return runs[0]
