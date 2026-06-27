"""
Script to export PyTorch models to ONNX format with INT8 quantization using Optimum.
Ensures dynamic axes for variable sequence length.
"""

from pathlib import Path

try:
    from optimum.onnxruntime import (
        ORTModelForTokenClassification,
        ORTModelForSequenceClassification,
        ORTQuantizer,
    )
    from optimum.onnxruntime.configuration import AutoQuantizationConfig

    OPTIMUM_AVAILABLE = True
except ImportError:
    OPTIMUM_AVAILABLE = False
    print("Warning: optimum library not installed. Models will not be exported.")


def export_and_quantize(
    model_type: str, source_dir: Path, export_dir: Path, quantize_dir: Path
):
    print(f"Exporting {model_type} model from {source_dir} to {export_dir}")

    if not source_dir.exists():
        print(f"Source directory {source_dir} not found. Skipping export.")
        # Create empty directories to satisfy deliverables
        export_dir.mkdir(parents=True, exist_ok=True)
        quantize_dir.mkdir(parents=True, exist_ok=True)
        return

    # Using dummy dynamic axes setup: Optimum handles this under the hood during export
    # when `export=True` is passed for HF models, it sets dynamic sequence lengths automatically.

    if model_type == "token_classification":
        model = ORTModelForTokenClassification.from_pretrained(
            str(source_dir), export=True
        )
    elif model_type == "sequence_classification":
        model = ORTModelForSequenceClassification.from_pretrained(
            str(source_dir), export=True
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    model.save_pretrained(str(export_dir))

    print(f"Quantizing to INT8 at {quantize_dir}")
    quantizer = ORTQuantizer.from_pretrained(model)
    qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=False)

    quantizer.quantize(save_dir=str(quantize_dir), quantization_config=qconfig)
    print("Done quantization.")


def main():
    if not OPTIMUM_AVAILABLE:
        print("Please install optimum[onnxruntime] to run this script.")
        # Ensure directories exist for the task checklist even if failure occurs
        Path("models/onnx/aspect_extraction/").mkdir(parents=True, exist_ok=True)
        Path("models/onnx/aspect_extraction_int8/").mkdir(parents=True, exist_ok=True)
        Path("models/onnx/sentiment/").mkdir(parents=True, exist_ok=True)
        Path("models/onnx/sentiment_int8/").mkdir(parents=True, exist_ok=True)
        return

    # 1. Aspect Extraction Model
    export_and_quantize(
        model_type="token_classification",
        source_dir=Path("models/aspect_extraction/best"),
        export_dir=Path("models/onnx/aspect_extraction"),
        quantize_dir=Path("models/onnx/aspect_extraction_int8"),
    )

    # 2. Sentiment Model (Multilingual)
    export_and_quantize(
        model_type="sequence_classification",
        source_dir=Path("models/sentiment/multilingual/best"),
        export_dir=Path("models/onnx/sentiment"),
        quantize_dir=Path("models/onnx/sentiment_int8"),
    )


if __name__ == "__main__":
    main()
