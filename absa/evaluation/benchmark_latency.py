"""
Script to benchmark latency for PyTorch, ONNX, and ONNX INT8 models on CPU.
"""

import time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

try:
    from optimum.onnxruntime import ORTModelForSequenceClassification

    OPTIMUM_AVAILABLE = True
except ImportError:
    OPTIMUM_AVAILABLE = False
import mlflow


def benchmark_model(model, tokenizer, texts, model_type="pytorch"):
    latencies = []

    # Warmup
    inputs = tokenizer(texts[:5], return_tensors="pt", padding=True, truncation=True)
    if model_type == "pytorch":
        with torch.no_grad():
            model(**inputs)
    else:
        model(**inputs)

    print(f"Benchmarking {model_type}...")
    for text in texts:
        inputs = tokenizer(
            [text], return_tensors="pt", padding=True, truncation=True, max_length=128
        )

        start_time = time.perf_counter()
        if model_type == "pytorch":
            with torch.no_grad():
                model(**inputs)
        else:
            model(**inputs)
        end_time = time.perf_counter()

        latencies.append((end_time - start_time) * 1000)  # ms

    mean_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    throughput = len(texts) / (sum(latencies) / 1000)  # samples / sec

    return mean_latency, p95_latency, throughput


def main():
    model_name = "xlm-roberta-base"
    pytorch_dir = Path("models/sentiment/multilingual/best")
    onnx_dir = Path("models/onnx/sentiment")
    int8_dir = Path("models/onnx/sentiment_int8")

    if not pytorch_dir.exists():
        print(f"Directory {pytorch_dir} not found. Skipping benchmark.")
        return

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    texts = ["This is a test sentence."] * 100

    results = {}

    # 1. PyTorch CPU
    print("Loading PyTorch model...")
    pt_model = AutoModelForSequenceClassification.from_pretrained(str(pytorch_dir))
    pt_model.eval()

    mean_pt, p95_pt, tput_pt = benchmark_model(pt_model, tokenizer, texts, "pytorch")
    results["PyTorch (CPU)"] = {
        "mean_ms": mean_pt,
        "p95_ms": p95_pt,
        "throughput": tput_pt,
    }

    if OPTIMUM_AVAILABLE:
        # 2. ONNX CPU
        if onnx_dir.exists():
            print("Loading ONNX model...")
            onnx_model = ORTModelForSequenceClassification.from_pretrained(
                str(onnx_dir)
            )
            mean_onnx, p95_onnx, tput_onnx = benchmark_model(
                onnx_model, tokenizer, texts, "onnx"
            )
            results["ONNX (CPU)"] = {
                "mean_ms": mean_onnx,
                "p95_ms": p95_onnx,
                "throughput": tput_onnx,
            }

        # 3. ONNX INT8 CPU
        if int8_dir.exists():
            print("Loading ONNX INT8 model...")
            int8_model = ORTModelForSequenceClassification.from_pretrained(
                str(int8_dir)
            )
            mean_int8, p95_int8, tput_int8 = benchmark_model(
                int8_model, tokenizer, texts, "onnx_int8"
            )
            results["ONNX INT8 (CPU)"] = {
                "mean_ms": mean_int8,
                "p95_ms": p95_int8,
                "throughput": tput_int8,
            }

    print("\n--- Latency Benchmark Results ---")
    print(
        f"{'Model':<20} | {'Mean (ms)':<10} | {'P95 (ms)':<10} | {'Throughput (samples/s)':<25}"
    )
    print("-" * 75)
    for name, metrics in results.items():
        print(
            f"{name:<20} | {metrics['mean_ms']:<10.2f} | {metrics['p95_ms']:<10.2f} | {metrics['throughput']:<25.2f}"
        )

    # Target check
    if "ONNX INT8 (CPU)" in results:
        int8_p95 = results["ONNX INT8 (CPU)"]["p95_ms"]
        if int8_p95 < 300:
            print(
                f"\nSUCCESS: ONNX INT8 P95 latency is {int8_p95:.2f}ms, which is < 300ms target."
            )
        else:
            print(
                f"\nWARNING: ONNX INT8 P95 latency is {int8_p95:.2f}ms, which is > 300ms target."
            )

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("latency-benchmark")
    with mlflow.start_run():
        for name, metrics in results.items():
            prefix = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            mlflow.log_metric(f"{prefix}_mean_latency", metrics["mean_ms"])
            mlflow.log_metric(f"{prefix}_p95_latency", metrics["p95_ms"])
            mlflow.log_metric(f"{prefix}_throughput", metrics["throughput"])


if __name__ == "__main__":
    main()
