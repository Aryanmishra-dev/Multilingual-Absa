import os
import pandas as pd
from datetime import datetime, timedelta
import mlflow
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TextOverviewPreset
from sqlalchemy import create_engine
import uuid

def main():
    # Attempt to fetch database URL, fallback to sqlite for local tests
    db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # We would normally load the reference data (e.g. from training data CSV)
    # For this script, we'll assume a local path or create a dummy reference if missing
    ref_path = "data/reference.csv"
    if os.path.exists(ref_path):
        ref_df = pd.read_csv(ref_path)
    else:
        print(f"Reference data not found at {ref_path}. Creating dummy reference data for testing.")
        ref_df = pd.DataFrame({
            "text": ["This is great", "I hate this", "Neutral statement"],
            "language": ["en", "en", "en"]
        })
        
    try:
        # Load production data from the last 7 days
        engine = create_engine(db_url)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Load directly from SQLAlchemy using pandas with parameterized query
        query = "SELECT text, language FROM reviews WHERE created_at >= %(cutoff)s"
        curr_df = pd.read_sql(query, engine, params={"cutoff": seven_days_ago})
    except Exception as e:
        print(f"Failed to fetch production data: {e}")
        curr_df = pd.DataFrame(columns=["text", "language"])
        
    if len(curr_df) < 50:
        print(f"Not enough data to run drift monitor (found {len(curr_df)} records, need at least 50). Exiting gracefully.")
        return

    # Run Evidently report
    print("Running Evidently drift report...")
    report = Report(metrics=[
        DataDriftPreset(),
        TextOverviewPreset(column_name="text")
    ])
    
    report.run(reference_data=ref_df, current_data=curr_df)
    
    # Create monitoring/reports dir if missing
    os.makedirs("monitoring/reports", exist_ok=True)
    
    report_path = f"monitoring/reports/drift_{datetime.now().strftime('%Y%m%d')}.html"
    report.save_html(report_path)
    print(f"Report saved to {report_path}")
    
    # Extract drift metrics as a dict
    report_dict = report.as_dict()
    
    # Simplified check for drift (using Dataset Drift metric from DataDriftPreset)
    dataset_drift = report_dict["metrics"][0]["result"]["dataset_drift"]
    drift_share = report_dict["metrics"][0]["result"]["drift_share"]
    
    if dataset_drift and drift_share > 0.3:
        print(f"⚠️ Drift detected — consider retraining. Drift share: {drift_share:.2f}")
        try:
            mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns"))
            with mlflow.start_run(run_name="drift_monitoring"):
                mlflow.log_metric("drift_share", drift_share)
                mlflow.log_artifact(report_path)
        except Exception as e:
            print(f"Failed to log warning to MLflow: {e}")

if __name__ == "__main__":
    main()
