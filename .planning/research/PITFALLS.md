# Domain Pitfalls

**Domain:** Multilingual Aspect-Based Sentiment Analysis (ABSA)
**Project:** Multilingual-ABSA (English, Hindi, Hinglish — XLM-RoBERTa + ONNX)
**Researched:** 2026-06-22
**Overall confidence:** HIGH

---

## Critical Pitfalls

### Pitfall 1: WordPiece Tokenization Breaking BIO Span Boundaries

**What goes wrong:**
Aspect term extraction uses BIO tagging (B-ASP, I-ASP, O) at the token level. XLM-RoBERTa uses SentencePiece subword tokenization, which can split a single word into multiple subword tokens. When a multi-token aspect span like "battery life" is tokenized, the word "battery" might become `["battery"]` (fine), but "life" is fine too. However, for Romanized Hindi words like "bahut achha" (बहुत अच्छा = very good), SentencePiece may split "achha" into `["ach", "ha"]`. The BIO labels from word-level annotation now apply to subword tokens — and the `B-ASP` tag on "ach" with `I-ASP` on "ha" looks correct, BUT if the word splits across different original whitespace boundaries, alignment gets corrupted. More critically: if a word is the *last* word in an aspect span and gets split, the last subword token (e.g., `"##ha"`) might not be tagged `I-ASP` in the naive alignment, breaking the span.

**Why it happens:**
The standard practice in ABSA codebases is to align word-level BIO tags to subword tokens using a simple "first subword gets the original tag, subsequent subwords inherit I- prefix" strategy. But this is only correct if:
1. The original word was an `I-ASP` token (continuing an entity).
2. The split occurs entirely within a single entity.

If a word is B-ASP (start of entity) and gets split, the second subword should be I-ASP, not B-ASP again. Novice implementations assign B-ASP to both subwords, creating spurious entity starts. XLM-R's SentencePiece can also join characters in unexpected ways for Romanized Hindi, e.g., merging short words across spaces in rare cases.

**How to avoid:**
- Write a robust `align_labels_with_tokens` function that handles this correctly: first subword of a word gets the original label; all subsequent subwords of the same word get label `I-{label}` if the original was `B-{label}` or `I-{label}`, else `O`. Do NOT just replicate the label to all subwords.
- Use the Hugging Face `Tokenizer`'s built-in `word_ids()` method to map subword tokens back to their original word index.
- In the data preprocessing phase, verify alignment by round-tripping: tokenize → detokenize → compare against original text spans.
- Add a unit test that specifically tests cases like single-character aspect terms in Hindi and multi-subword Hindi words.

**Warning signs:**
- Aspect terms in model output are "broken" — showing only partial words (e.g., extracting "ach" instead of "achha").
- Evaluation metrics (seqeval F1) are suspiciously low on Hindi/Hinglish data compared to English.
- Training loss decreases but validation F1 plateaus early.

**Phase to address:**
Phase 3 (Data Pipeline) — build and test the alignment function before training begins. Validate on multilingual toy examples.

---

### Pitfall 2: Hinglish Code-Mixed Text Preprocessing Gotchas

**What goes wrong:**
Hinglish (Hindi written in Roman script mixed with English) has no standard spelling. The same Hindi word can appear in multiple romanized forms: "achha", "acha", "accha", "achchha". Whitespace tokenization is unreliable because Hinglish speakers sometimes attach Hindi particles to English words ("nahi_hai" instead of "nahi hai"). Language detection at the token level is necessary but non-trivial since many tokens are ambiguous (e.g., "to" could be English or Hindi "तो"). Existing standard NLP preprocessing (lowercasing, stemming, stopword removal) breaks Hinglish — it removes valid Hindi content words that look like English stopwords.

**Why it happens:**
Most NLP preprocessing libraries are designed for monolingual English. When applied to Hinglish, they:
- Remove "to", "do", "ka", "ki", "mein" as English stopwords — but these are valid Hindi postpositions and content words.
- Apply English-specific stemming (e.g., "PorterStemmer") which garbles romanized Hindi.
- Split on punctuation aggressively, which removes Hindi's inherent vowel diacritics when transliterated.

**How to avoid:**
- **Do NOT use English stopword lists for Hinglish.** Instead, use token-level language identification (e.g., Microsoft's LID-tool or IndicLID) and apply language-specific preprocessing per token.
- Build a curated Hinglish stopword list that only removes truly noise-like tokens.
- Use a normalizer that maps common spelling variants to a canonical form (e.g., "achha"/"acha"/"accha" → "achha"). This can be a lookup table built from the training data statistics.
- Preserve emojis and punctuation patterns — they carry sentiment signal in Hinglish just like in English.
- Validate preprocessing on a held-out Hinglish sample and manually inspect tokenization quality.

**Warning signs:**
- The number of tokens after preprocessing is drastically lower for Hinglish than English text of similar length.
- Model performance on Hinglish is much worse than English despite similar training data size.
- Common Hinglish words appear as `[UNK]` tokens.

**Phase to address:**
Phase 3 (Data Pipeline) — implement Hinglish-specific preprocessing and normalization before model training.

---

### Pitfall 3: ONNX Export with Dynamic Axes Breaking on Combined Two-Stage Graph

**What goes wrong:**
The project requires combining *two* model stages (Aspect Term Extraction + Aspect Sentiment Classification) into a single ONNX graph. Stage 1 (token classification) outputs variable-length aspect spans. Stage 2 (sequence classification) takes the original text + each extracted aspect as input. Creating a single ONNX graph from this is challenging because:
1. Stage 1 output size depends on input length (dynamic).
2. The number of extracted aspects is variable (dynamic).
3. The combined graph requires control flow or dynamic slicing that ONNX opsets don't natively support well.

Attempting to export this with `torch.onnx.export` using `dynamic_axes` often results in shape inference errors — `Reshape` nodes get static shapes hardcoded during tracing, and inference fails when actual input shapes differ from the tracing input.

Additionally, when using `--no-dynamic-axes` with `optimum-cli`, the model rejects any input with sequence length different from the export dummy input.

**Why it happens:**
PyTorch's ONNX exporter uses tracing by default: it runs the model once with a dummy input and records the operations. If the model has data-dependent control flow (e.g., number of detected aspects varies), only the path taken during tracing is captured. The `dynamic_axes` parameter tells ONNX which dimensions are variable, but internal `Reshape` ops may still get static shapes inferred, leading to runtime dimension mismatches.

**How to avoid:**
- **Do NOT export both stages as a single monolithic ONNX graph for v1.** Export Stage 1 and Stage 2 as **separate ONNX models**. Chain them in the application layer (FastAPI). This avoids the dynamic control-flow issue entirely.
- For each individual export, do test with dynamic axes. The token classification model needs `{0: 'batch_size', 1: 'sequence_length'}` as dynamic. The sentiment classifier also needs `{0: 'batch_size', 1: 'sequence_length'}`.
- Use `optimum-cli export onnx` (or optimum.onnxruntime) for the standard HuggingFace architectures — it handles dynamic axes better than manual `torch.onnx.export`.
- Validate exports with shape inference: `python -m onnxruntime.transformers.shape_infer --input model.onnx`.

**Warning signs:**
- ONNX model loads but inference returns shape mismatch errors.
- `optimum-cli` export completes but `onnxruntime.InferenceSession` fails with "Non-zero status code" on Reshape ops.
- Error message contains "input_shape_size == size" in reshape_helper.h.

**Phase to address:**
Phase 6 (ONNX Export) — but the decision to use two separate ONNX models must be made during Phase 2 (Architecture Design) because it affects the API design and inference pipeline.

---

### Pitfall 4: Neutral Sentiment Class Dominance in Aspect Sentiment Classification

**What goes wrong:**
In real-world ABSA datasets (SemEval 2014-2016), most aspect mentions are neutral — users often describe product features factually ("the screen is 6.1 inches") rather than with explicit sentiment ("the screen is amazing"). This creates a severe class imbalance where neutral examples outnumber positive and negative by 3-18x (imbalance ratio). A model trained on this distribution learns to predict "neutral" for everything, achieving ~70% "accuracy" but 0% recall on minority classes.

The problem is compounded because "neutral" is also the hardest class to define: borderline cases between neutral/positive and neutral/negative are common, and annotation disagreement is highest for neutral.

**Why it happens:**
Standard cross-entropy loss optimizes overall accuracy. With 70% neutral examples, the optimal strategy is always predict neutral. Practitioners often don't check per-class F1 during training and are misled by seemingly good accuracy numbers. The project already specifies Macro-F1 as the metric, which helps — but the *training loss* still uses unweighted cross-entropy unless explicitly modified.

**How to avoid:**
- **Use weighted cross-entropy loss** with inverse class frequency weights. Compute: `weight_c = total_samples / (num_classes * samples_c)`. For the SemEval restaurant dataset this typically gives neutral ~0.3-0.5, positive ~1.0-1.2, negative ~1.5-3.0.
- Or use **class-balanced loss** (Cui et al. 2019) which uses effective number of samples per class.
- Consider **focal loss** for hard-to-classify neutral examples near decision boundaries.
- **Data augmentation** for minority classes: back-translation of positive/negative examples (English → German → English) to generate synthetic variations. For Hinglish, use IndicTrans2 for the translation step.
- Monitor per-class precision, recall, and F1 on the validation set every epoch — not just macro-F1. A diverging per-class F1 (e.g., neutral goes up while positive/negative stagnate) signals the imbalance is worsening.
- Stratified split for train/validation/test to maintain class distribution across splits.

**Warning signs:**
- Validation accuracy is high (~80%) but macro-F1 is much lower (~0.4-0.5).
- Confusion matrix shows most examples predicted as neutral.
- Per-class F1: neutral=0.8, positive=0.3, negative=0.1.

**Phase to address:**
Phase 4 (Model Training) — configure the loss function and evaluation callbacks before the first training run.

---

### Pitfall 5: Cross-Lingual Transfer Degradation (Capacity Dilution)

**What goes wrong:**
XLM-RoBERTa is trained on 100 languages, but the model's total capacity is fixed. Adding more languages during pretraining dilutes the capacity available per language — this is called the "curse of multilinguality" (Conneau et al., 2020). When fine-tuned on mixed English+Hindi+Hinglish data, the model may:
- Perform well on English (high-resource) but poorly on Hindi, especially for linguistically nuanced tasks like aspect extraction.
- Show degraded performance on low-resource languages compared to a monolingual Hindi model (e.g., IndicBERT).
- The degradation is worse for token-level tasks (like BIO tagging) than for sentence-level tasks (like sentiment classification) because token-level tasks require more language-specific knowledge.

The XLM-R paper shows that for low-resource languages like Swahili and Urdu, monolingual models outperform multilingual ones by 5-10 points on NER-like tasks. This directly applies to Hindi in ABSA.

**How to avoid:**
- **Do NOT assume XLM-R alone is sufficient.** Train and evaluate IndicBERT (AI4Bharat's Hindi-focused model) as a baseline. IndicBERT may outperform XLM-R on Hindi despite having fewer total parameters.
- Use **language-aware training**: sample training data to up-weight low-resource languages. XLM-R's exponential smoothing (α=0.3) in pretraining oversamples low-resource languages — replicate this during fine-tuning by controlling batch composition.
- **Language-adversarial training**: Add a gradient reversal layer that tries to predict the input language from the encoder output, forcing the encoder to learn language-invariant representations. This helps cross-lingual transfer.
- Evaluate **per-language** metrics, not just aggregate macro-F1. If Hindi is 15 points behind English, consider language-specific fine-tuning.
- For the **combined ONNX graph**: if using separate models per language, you can load XLM-R for English and IndicBERT for Hindi at inference time, but this doubles the deployment complexity.

**Warning signs:**
- Aggregate macro-F1 looks good but Hindi-only macro-F1 is significantly (10+ points) lower.
- Model extracts "battery" correctly in English but fails on "बैटरी" (battery in Hindi) in otherwise similar contexts.
- Training loss decreases for English batches but not for Hindi batches.

**Phase to address:**
Phase 4 (Model Training) — set up per-language evaluation from day one. Phase 7 (Evaluation) — deep error analysis by language.

---

### Pitfall 6: Metric Selection Pitfalls — Accuracy Misleads, Macro-F1 Can Hide Problems Too

**What goes wrong:**
The project correctly identifies Macro-F1 as the primary metric. However, two subtle mistakes still happen:
1. **Macro-F1 alone is insufficient.** Two models can have the same Macro-F1 but very different behavior — one might be balanced across classes, the other good on two classes and terrible on the third. Macro-F1 averages per-class F1s, so a model with F1s of [0.9, 0.9, 0.0] gets Macro-F1=0.6, same as one with [0.6, 0.6, 0.6].
2. **Inconsistent metric across pipeline stages.** Stage 1 (Aspect Extraction) uses seqeval F1 (span-based). Stage 2 (Sentiment Classification) uses macro-F1. These measure different things and improvements in one may not translate to improvements in the end-to-end pipeline.
3. **Exact match vs. partial match for spans.** Seqeval by default requires exact span matches. A prediction of "life" when the gold span is "battery life" counts as a complete miss (no partial credit). For multilingual ABSA where boundary detection is harder, this can underestimate real progress.

**Why it happens:**
Standard ML evaluation culture focuses on "the one metric." But ABSA is a multi-task pipeline with different evaluation needs. Teams optimize for the single reported number and miss regressions in other dimensions.

**How to avoid:**
- **Report a dashboard of metrics**, not just macro-F1:
  - Per-class F1 (positive, negative, neutral) for Stage 2
  - Per-language F1 (English, Hindi, Hinglish) for both stages
  - Span-level exact match F1 + span-level partial match F1 for Stage 1
  - Combined end-to-end F1 (correct aspect extraction *and* correct sentiment)
- For span evaluation in Stage 1, also compute **span micro-F1** (token-level, not entity-level) to get a finer-grained signal during training.
- Use **McNemar's test** or **paired bootstrap** to compare models — don't just compare point estimates.
- Include **confusion matrices** for Stage 2 in every MLflow run.

**Warning signs:**
- Model A has higher Macro-F1 but lower per-class F1 on positive and negative.
- Stage 1 F1 is high but end-to-end accuracy is low (aspect extraction errors cascade).
- Manual inspection reveals the model is making reasonable partial-span predictions that seqeval marks as wrong.

**Phase to address:**
Phase 4 (Model Training) — define the full metric set in training scripts before first run. Phase 7 (Evaluation) — build the dashboard.

---

### Pitfall 7: Data Leakage in Two-Stage ABSA Pipeline

**What goes wrong:**
In a two-stage ABSA pipeline (extract aspects → classify sentiment), data can leak between stages in subtle ways:
1. **Same-review leakage:** When splitting data, if reviews containing multiple aspects are split naively (row-level split), the same review text appears in both training and test sets (with different aspect annotations). The model memorizes review-level patterns rather than aspect-level patterns.
2. **Context leakage in sentence-pair formulation:** If Stage 2 uses the "[CLS] review [SEP] aspect [SEP]" format, the model can learn to ignore the aspect and just predict the majority sentiment for each review. It achieves high accuracy on seen reviews but fails on unseen ones.
3. **Aspect span information leakage:** If Stage 2 receives the *exact gold aspect spans* during training but *predicted aspect spans* during inference, performance drops sharply because the model never learned to handle noisy/partial aspect boundaries.

**Why it happens:**
Practitioners treat each (review, aspect, sentiment) triplet as an independent sample. But multiple triplets from the same review are not independent. Standard `train_test_split` shuffles rows without considering the review-level grouping. Stage 2 models trained with gold spans overfit to the precise boundaries and collapse on predicted spans.

**How to avoid:**
- **Split at the review level, not the (review, aspect)-pair level.** Ensure all aspects from one review go to the same split. Use `GroupShuffleSplit` in scikit-learn with review_id as the group.
- **For Stage 2 training, use gold aspect spans for loss computation but evaluate with predicted spans** to measure the actual inference performance (this is the "end-to-end" metric).
- Optional but recommended: add **aspect span dropout** during Stage 2 training — randomly replace a percentage of gold spans with slightly corrupted versions (trim words, substitute with synonyms) to make the model robust to Stage 1 errors.
- Log the number of unique reviews in each split to verify no cross-split contamination.

**Warning signs:**
- Stage 2 validation F1 is > 95% while Stage 1 validation F1 is < 80% — this is highly suspicious and usually indicates leakage.
- Model performs much worse on a held-out test set than on the validation set.
- The same review appears in both train and test splits after splitting.

**Phase to address:**
Phase 3 (Data Pipeline) — implement review-level splitting and verify no leakage before training. Phase 7 (Evaluation) — measure end-to-end metrics with predicted spans.

---

### Pitfall 8: ONNX Model Serving Latency — Unoptimized Inference in Production

**What goes wrong:**
Exporting to ONNX doesn't automatically make inference fast. Without optimization, an unoptimized ONNX model can be **slower than PyTorch eager mode** because:
1. The default ONNX Runtime `CPUExecutionProvider` doesn't apply graph optimizations unless explicitly configured.
2. The model is exported in FP32, which is 2x the memory bandwidth and compute of FP16.
3. No operator fusion is applied — each transformer layer remains as separate ops.
4. The inference API (FastAPI + Celery) adds serialization overhead: tokenization in Python, ONNX inference in C++, detokenization in Python — each crossing the GIL boundary.

For a 110M-parameter XLM-RoBERTa model, naive ONNX inference can take 50-150ms per request on CPU. With Celery task queuing, the end-to-end latency (queue wait + model inference + post-processing) can exceed 500ms, making the API feel slow.

**Why it happens:**
"Export to ONNX" is treated as a one-step checkbox. Teams assume ONNX = fast. But ONNX Runtime needs to be tuned: execution provider selection, graph optimization level, intra-op thread count, memory pattern optimization, and (for GPU) FP16 conversion.

**How to avoid:**
- **Benchmark inference latency at every stage of optimization:**
  - Baseline: PyTorch eager (FP32) on CPU
  - ONNX with default settings
  - ONNX with level 3 graph optimization (`SessionOptions.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL`)
  - ONNX with FP16 quantization (if using GPU)
  - ONNX with INT8 quantization (if latency on CPU is critical)
- Use `onnxruntime.transformers.optimizer` to apply transformer-specific fusions (attention fusion, layer norm fusion).
- Set `SessionOptions.intra_op_num_threads` to match available CPU cores.
- For GPU: set `providers=['CUDAExecutionProvider', 'CPUExecutionProvider']` and benchmark.
- **Profile with ONNX Runtime's built-in profiler**: `session_options.enable_profiling = True`.
- In FastAPI, use an **async** endpoint that offloads ONNX inference to a thread pool (to avoid blocking the event loop). OR use a sync endpoint with `run_in_executor` for Celery tasks.
- Consider model quantization: INT8 quantization can reduce latency 2-3x on CPU with < 1% F1 degradation for ABSA.

**Warning signs:**
- API response times are > 300ms for single review.
- CPU usage is at 100% during inference but throughput is low (< 5 req/s).
- ONNX model file size is > 400MB (XLM-RoBERTa-base is ~440MB in FP32; < 250MB after FP16; < 150MB after INT8).

**Phase to address:**
Phase 9 (API & Serving) — benchmark and optimize before deploying to production. Latency optimization should be a separate task with explicit targets (e.g., P99 latency < 200ms).

---

### Pitfall 9: Docker/Python Version Compatibility for ONNX Runtime

**What goes wrong:**
ONNX Runtime has strict version compatibility requirements with Python, CUDA, cuDNN, and ONNX opsets. The project uses Python 3.11+ and Docker for deployment. A common failure sequence:
1. Local development on macOS with Python 3.11 and `onnxruntime` (CPU) works fine.
2. Docker image built from `python:3.12-slim` with `pip install onnxruntime-gpu` fails at runtime with "ImportError: libcuda.so.1: cannot open shared object file."
3. Fix by switching to `nvidia/cuda:12.x-base` image — now CUDA is resolved but cuDNN version mismatch causes "error loading 'libcudnn_cnn_infer.so.8'".
4. Different ONNX opset version between export environment and serving environment causes graph parsing failures.

Additionally, `onnxruntime-gpu` and `onnxruntime` cannot coexist in the same Python environment. Installing one after the other silently breaks inference.

**How to avoid:**
- **Pin all version combinations explicitly in both `requirements.txt` and Dockerfile:**
  - Python version (3.11.x, not 3.12+ until ONNX Runtime confirms support)
  - ONNX Runtime version (e.g., `onnxruntime-gpu==1.20.1`)
  - CUDA version matching the ONNX Runtime build (e.g., CUDA 12.x for ORT 1.20)
  - cuDNN version matching CUDA
  - ONNX opset version used during export (e.g., opset 21 for ORT 1.20)
- **Use the same Docker base image for export and serving** to avoid opset mismatch: export model in the same environment where inference will run.
- **Use a multi-stage Docker build:**
  - Stage 1 (export): Install full PyTorch + transformers, export model.
  - Stage 2 (serving): Only install onnxruntime + tokenizers + FastAPI. Copy the exported .onnx files. Do NOT install PyTorch in the serving image.
- **CI check**: build the Docker image and run `python -c "import onnxruntime; print(onnxruntime.__version__)"` as a smoke test.

**Warning signs:**
- Docker build succeeds but runtime raises `ImportError` or `OSError` about shared libraries.
- `onnxruntime.InferenceSession` creation fails after Docker deployment (works locally).
- Model runs but produces NaN outputs on GPU (cuDNN version mismatch).

**Phase to address:**
Phase 5 (Docker) — set up the Dockerfile with pinned versions. Phase 6 (ONNX Export) — ensure the export environment matches the Docker serving environment.

---

### Pitfall 10: DVC Dataset Management Mistakes

**What goes wrong:**
DVC is used to version datasets, but common mistakes make it effectively useless:
1. **Not running `dvc repro` after data changes.** Models are trained on stale data while experiments claim they used "the latest."
2. **Committed large raw data files directly to DVC without `.dvcignore`.** The DVC cache grows unbounded because temp files, checkpoints, and `.DS_Store` files get tracked.
3. **Using DVC with a local cache only.** No remote storage configured — if the laptop dies, all dataset versions are lost. DVC becomes a false sense of versioning.
4. **Not associating DVC commits with git tags.** When looking at an MLflow run, there's no way to tell which exact dataset version was used. The `.dvc` file hash references a cache entry, but without git tags, navigating history requires manual git log inspection.
5. **Tracking model checkpoints in DVC + MLflow simultaneously.** This creates duplication and confusion about the source of truth for model artifacts.

**Why it happens:**
DVC is easy to set up incorrectly. `dvc init` followed by `dvc add data/` works out of the box — but the critical practices (remote setup, tagging, pipeline definitions, `.dvcignore`) are documentation steps that get skipped in the rush to start modeling.

**How to avoid:**
- **Set up DVC remote on day 1** (S3, GCS, or Hugging Face Dataset viewer). Verify with `dvc push` that data uploads.
- **Create a `.dvcignore` file** ignoring: `*.pkl`, `*.pt`, `*.onnx`, `*.bin`, `__pycache__/`, `.DS_Store`, `*.tmp`, `checkpoints/`.
- **Tag every DVC data change with a git tag.** Convention: `data-v1.0`, `data-v1.1`, etc. This makes it possible to correlate MLflow runs to dataset versions.
- **Use `dvc.yaml` to define the preprocessing pipeline** so that `dvc repro` automatically tracks data → processed data → features → model artifacts.
- **Use MLflow as the primary model registry** and DVC only for datasets. Don't track model checkpoints in both.
- Run `dvc gc` periodically to prune old cache entries.
- In training scripts, log the DVC data version: `mlflow.log_param("data_version", subprocess.check_output(["git", "describe", "--tags", "--dirty"]).decode().strip())`.

**Warning signs:**
- Running `dvc status` shows many "changed" files that shouldn't have changed.
- DVC cache directory (`~/.dvc/cache` or `.dvc/cache`) is > 50GB with no clear cause.
- MLflow runs show similar metrics but cannot be reproduced because the data version is unknown.
- `dvc push` fails or was never configured.

**Phase to address:**
Phase 2 (Scaffolding) — set up DVC properly with remote, .dvcignore, and conventions. Revisit in Phase 5 (Docker) to ensure CI handles DVC.

---

### Pitfall 11: Training/Inference Skew Between PyTorch Fine-Tuning and ONNX Runtime

**What goes wrong:**
A model that achieves macro-F1 0.81 during PyTorch evaluation (in the training script) drops to macro-F1 0.72 when loaded through ONNX Runtime, with no obvious errors. The ONNX inference produces valid outputs — they're just systematically different from PyTorch.

This happens because:
1. **Dropout is not disabled during ONNX trace export.** If the model isn't in `model.eval()` mode before export, dropout layers are baked into the ONNX graph, applying stochastic dropout during inference.
2. **LayerNorm numerical differences** between PyTorch and ONNX Runtime (FP32 accumulation rounding).
3. **Attention mask handling** differs: PyTorch's attention masking uses a large negative value (-10000.0) in some implementations, while ONNX Runtime's optimized attention fusion may clip or round these differently.
4. **Tokenizer inconsistency** — if the tokenizer used for ONNX inference is a different version or was re-loaded separately, subword splits may differ slightly from the training setup.

**How to avoid:**
- **Always call `model.eval()` before `torch.onnx.export()`**. Verify by checking `model.training` is `False`.
- **Use `torch.no_grad()` context** during export as an additional safety net.
- **Export with opset >= 14** and test that PyTorch → ONNX numerical difference is < 1e-4 for the same input.
- **Compare logits directly**: pass the same input through PyTorch (eval mode) and ONNX Runtime, compute `torch.max(torch.abs(logits_pt - logits_ort))`. Fix any discrepancies > 1e-3 before deploying.
- For the tokenizer: save tokenizer to disk at training time (`tokenizer.save_pretrained(model_path)`) and load the exact same files in the ONNX inference pipeline — don't re-download from the Hub.
- For attention masks: verify the attention mask values in ONNX by inspecting the graph or testing with masked vs unmasked inputs.

**Warning signs:**
- ONNX evaluation F1 is consistently 2-8 points lower than PyTorch evaluation F1 on the same test set.
- ONNX predictions for "obviously positive" sentences like "This is great!" sometimes come back as neutral.
- Running the same input through PyTorch and ONNX produces different logit distributions (check with `np.max(np.abs(diff))`).

**Phase to address:**
Phase 6 (ONNX Export) — the export validation should include a numerical correctness test comparing PyTorch and ONNX outputs.

---

### Pitfall 12: Celery + Redis Overhead for ABSA Inference (Misarchitected Async Pipeline)

**What goes wrong:**
The project plan includes Celery + Redis for the inference API. For ABSA inference (which is not a real-time streaming task but also not a batch-processing task), Celery adds unnecessary complexity:
1. Each inference request goes: FastAPI → Redis queue → Celery worker → deserialize → ONNX inference → serialize → Redis result → FastAPI response. This is 2 extra serialization hops and queue latency.
2. If the Celery worker pool is configured poorly (e.g., 4 workers with 1 concurrent task each), only 4 inference requests can run simultaneously, massively underutilizing CPU.
3. Redis becomes a bottleneck: model inputs/outputs are large (tokenized sequences ~512 ints, output logits ~3-6 floats per token), and Redis serialization adds overhead.
4. Error handling becomes complex: what happens when Redis queue backs up? When a Celery task crashes mid-inference? When the result expires before the client polls?

For a v1 product with < 100 concurrent users, Celery is overkill. For a product expected to handle > 1000 requests/minute, the API needs proper load shedding and autoscaling, which Celery alone doesn't provide.

**How to avoid:**
- **For v1: Remove Celery.** Use a simple FastAPI async endpoint with `BackgroundTasks` or direct ONNX inference in a thread pool. This reduces latency by 40-60% and eliminates Redis as a dependency.
- If Celery is kept for explicit reasons (e.g., planned batch processing, long-running jobs), configure it properly:
  - Use `prefork` pool with `concurrency=N` where N <= CPU core count.
  - Set `worker_prefetch_multiplier=1` to prevent worker starvation.
  - Use Redis with `visibility_timeout` set appropriately and handle retries.
  - Profile the end-to-end latency *with Celery overhead* before claiming it's production-ready.
- **Defer Celery to Phase 3+** when there's evidence of need (e.g., users request batch CSV uploads, or inference time exceeds 10 seconds for complex operations).

**Warning signs:**
- API response time is > 1 second for a single review when ONNX inference takes 100ms — the extra 900ms is queue + serialization overhead.
- Redis queue grows during light load (a sign of underprovisioned workers or blocking tasks).
- Debugging inference failures requires checking Redis, Celery logs, and FastAPI logs simultaneously.

**Phase to address:**
Phase 2 (Architecture) — decide if Celery is truly needed for v1. Phase 9 (API & Serving) — benchmark with and without Celery.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| **Hardcoding dataset paths** | Quick prototype | Brittle pipeline, can't reproduce experiments on other machines | Never — use DVC + env vars from the start |
| **Skipping ONNX export validation** | Faster dev iteration | Silent 5-10% F1 drop in production with no debugging path | Never — always compare PyTorch vs ONNX logits numerically |
| **Training only on English, "adding Hindi later"** | Faster first demo | Model architecture may need changes for Hinglish tokenization; retrain from scratch | Only if the goal is a pure English v0.1 demo with planned rebuild |
| **Using accuracy instead of macro-F1 for checkpoint selection** | "Simpler" metric | Saves models that perform well on neutral but fail on positive/negative | Never — this decision is already reversed in the project plan |
| **Single combined ONNX graph instead of two separate models** | "Cleaner" deployment | Debugging, optimization, and per-model updates become harder | Acceptable only if a clear end-to-end latency target requires it AND testing validates correctness |
| **Celery for "production readiness" in v1** | Feels more architectural | 40-60% unnecessary latency, Redis dependency, operational complexity | Acceptable only if batch inference is a v1 requirement |
| **Not setting up DVC remote** | Quick local setup | No backup, no team collaboration, false reproducibility | Only for personal prototypes, never for team projects |
| **Ignoring Hinglish preprocessing** | Faster data loading | Model performs at chance level on 33% of the target language distribution | Never — 1/3 of the data is Hinglish |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **Hugging Face Transformers + ONNX** | Using `torch.onnx.export` directly without Optimum | Use `optimum-cli export onnx` which handles architecture-specific configurations, dynamic axes, and opsets correctly |
| **Celery + FastAPI** | Returning Celery task IDs to the client and making the client poll | Use synchronous inference (with thread pool) for v1; add async/celery only if batch processing is required |
| **DVC + Git** | Committing `.dvc` files without also committing code changes that use the data version | Always commit `.dvc` files + `dvc.lock` + code changes in the same git commit — this makes `git checkout` reproducible |
| **MLflow + DVC** | Logging dataset hash in MLflow as a free-form string | Log the DVC git tag and `dvc.yaml` hash as MLflow params — makes experiment reproduction deterministic |
| **Docker + ONNX Runtime GPU** | Using `python:3.12-slim` as base image and `pip install onnxruntime-gpu` | Use `nvidia/cuda:12.x-runtime-ubuntu22.04` as base; CUDA and cuDNN must match ONNX Runtime's build |
| **PostgreSQL + ABSA results** | Storing aspect lists and sentiment as JSON strings with no schema validation | Use Pydantic models for the API response and store structured data with proper types (e.g., ARRAY of sentiment objects) |
| **Railway/Vercel + ONNX** | Assuming Railway's free tier can load a 440MB ONNX model | Verify RAM limits (Railway free: 512MB). An XLM-R ONNX model + runtime can exceed this. Test with a quantized model or upgrade plan. |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| **ONNX model loaded per API request** | Increasing latency over time; memory leak | Load the model once at app startup into a global `InferenceSession` | Immediately — every request creates a new session |
| **FP32 ONNX on CPU** | High latency (50-150ms per inference) | Quantize to INT8 with `onnxruntime.quantization.quantize_dynamic` | At > 10 requests/second on a single CPU |
| **Celery worker pool exhaustion** | Requests queue up, timeouts increase | Set `worker_concurrency` = CPU count; use autoscaling; bypass Celery for single-inference requests | At ~6 concurrent requests with 4 workers/1 task each |
| **Tokenizer re-initialization per request** | 5-10ms overhead per request | Cache the tokenizer in a global variable; pre-compile fast tokenizer | Immediately — this is always unnecessary overhead |
| **Large batch processing without chunking** | OOM on long reviews (1024+ tokens) | Set `max_length=128` for XLM-R; truncate reviews to reasonable length; process long reviews in chunks | With reviews longer than 512 tokens |
| **PostgreSQL as inference cache** | Reads are fast, writes cause latency spikes | Use Redis for inference caching (not PostgreSQL); keep PostgreSQL for persistent storage only | At high write volumes (> 100 writes/second) |
| **Multiple ONNX sessions for the same model** | Memory grows linearly with worker count | Share a single session across processes (ONNX Runtime is thread-safe after initialization) | With > 1 Celery worker loading its own session |
| **No response compression for API** | Large JSON payloads (10-50KB per review with all aspects) | Enable GZIP compression in FastAPI middleware (`GZipMiddleware`) | At > 100 responses/second over limited bandwidth |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| **Exposing raw model predictions without validation** | Output could contain offensive or PII content extracted from reviews | Add output sanitization; consider a human review loop for deployment |
| **No rate limiting on inference endpoint** | Attackers could drain API credits or cause DoS | Add `slowapi` or Cloudflare rate limiting to the inference endpoint |
| **Loading user-provided text into the model without sanitization** | Prompt injection or adversarial inputs could cause unexpected behavior | Apply input length limits, character set validation, and content moderation |
| **Storing full review text in PostgreSQL without access controls** | PII exposure if database is breached | Encrypt review text at rest; enforce least-privilege database access |
| **Exposing MLflow UI without authentication** | Training data statistics, model weights, and experiment details exposed | Use MLflow authentication or deploy on a private network; never expose the tracking server publicly |
| **Celery result backend (Redis) without authentication** | Anyone on the network can read or modify inference results | Set `REDIS_PASSWORD` and use TLS for Redis connections |
| **ONNX model file without integrity check** | Model could be swapped with a malicious version | Compute and verify SHA-256 checksum before loading the model |
| **Loading model checkpoints from untrusted sources** | Backdoored model weights could execute arbitrary code during training | Only use Hugging Face Hub models from verified organizations; scan with `picklescan` |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| **Showing raw model confidence scores (0.73)** | Users don't know if 0.73 is good or bad | Map scores to human labels: "confident," "uncertain," "needs review" with thresholds |
| **Returning empty aspects for mixed-language reviews** | User thinks the model is broken for their language | Fall back to document-level sentiment if aspect extraction fails; show "aspect analysis not available for this language" |
| **No explanation for sentiment predictions** | User can't trust the output | Show the tokens that most influenced the prediction (attention weights or LIME explanation) — especially useful for debugging "wrong" predictions |
| **Inconsistent handling of emojis in Hinglish** | Sentiment of emoji-heavy reviews is wrong | Pass emojis through to the model; don't strip them. Many Hinglish reviews use emojis as primary sentiment signals |
| **No latency feedback for long reviews** | User clicks "analyze" and nothing happens for 5+ seconds | Show progress indicator: "Tokenizing...", "Analyzing aspects...", "Classifying sentiment..." |
| **Language not auto-detected** | User has to select language manually | Auto-detect language from the review text; show detected language to user; allow override |

---

## "Looks Done But Isn't" Checklist

- [ ] **ONNX Export:** The model exports without errors BUT numerical output differs from PyTorch by > 1e-3. Run the numerical comparison test — this is not optional.
- [ ] **DVC Setup:** `dvc init` ran successfully BUT no remote storage is configured. Verify with `dvc remote list`.
- [ ] **Training Pipeline:** The training loop runs BUT per-class F1 is not logged to MLflow. Only macro-F1 is not enough to debug imbalance.
- [ ] **Inference API:** The API returns sentiment BUT uses gold aspect spans from the dataset, not the model's own extraction. End-to-end metrics will be inflated.
- [ ] **Docker Compose:** `docker-compose up` starts all services BUT the CPU runs at 100% because ONNX model is in FP32 on CPU. Add quantization to the CI pipeline.
- [ ] **CI Pipeline:** Tests pass BUT they use tiny toy data (10 sentences) that doesn't stress the ONNX export or cross-lingual components. Add at least one Hinglish test case.
- [ ] **Evaluation Dashboard:** Charts render BUT confusion matrices are missing. Without them, class-level performance issues are invisible.
- [ ] **Code-Mixed Support:** The model accepts Hinglish text BUT token-level language identification is not used in preprocessing. English stopwords are being stripped from Hindi tokens.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| **BIO alignment broken** | MEDIUM | 1. Fix `align_labels_with_tokens()` 2. Reprocess dataset 3. Retrain both stages 4. Compare pre/post F1 |
| **Hinglish preprocessing wrong** | MEDIUM | 1. Add token-level LID 2. Rebuild Hinglish normalizer 3. Reprocess dataset 4. Retrain |
| **ONNX dynamic axes error** | LOW | 1. Export as two separate models 2. Update inference code 3. No retraining needed |
| **Neutral class dominance** | LOW-MEDIUM | 1. Add weighted loss or focal loss 2. Retrain Stage 2 only 3. Compare per-class F1 |
| **Cross-lingual degradation** | MEDIUM | 1. Add language-adversarial training 2. Train IndicBERT baseline 3. Compare per-language metrics |
| **Data leakage** | HIGH — need to redo data splits and retrain | 1. Fix data splitting code 2. Reprocess all splits 3. Retrain both stages 4. Re-evaluate |
| **ONNX latency** | LOW | 1. Enable graph optimizations 2. Quantize to INT8 3. Benchmark and tune thread count |
| **Docker version mismatch** | LOW | 1. Pin exact versions 2. Rebuild Docker image 3. Test with `python -c "import onnxruntime"` |
| **DVC mistakes** | LOW-MEDIUM | 1. Set up remote 2. Add .dvcignore 3. Run `dvc gc` to clean cache 4. Tag dataset versions |
| **PyTorch/ONNX numeric mismatch** | LOW | 1. Fix export (eval mode, opset) 2. Re-export 3. Verify with numerical comparison test |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| BIO alignment (P1) | Phase 3 (Data Pipeline) | Unit test: tokenize → align → detokenize for multilingual toy examples |
| Hinglish preprocessing (P2) | Phase 3 (Data Pipeline) | Manual inspection of 100 Hinglish samples after preprocessing |
| ONNX export dynamic axes (P3) | Phase 2 (Architecture) + Phase 6 (ONNX Export) | Numerical comparison: PyTorch vs ONNX logits < 1e-3 |
| Neutral class imbalance (P4) | Phase 4 (Model Training) | Per-class F1 logged to MLflow in every training run |
| Cross-lingual degradation (P5) | Phase 4 (Model Training) | Per-language F1 in evaluation dashboard |
| Metric selection (P6) | Phase 4 (Model Training) | Metric dashboard includes per-class, per-language, span, and end-to-end metrics |
| Data leakage (P7) | Phase 3 (Data Pipeline) | `assert len(set(train_reviews) & set(test_reviews)) == 0` |
| ONNX latency (P8) | Phase 9 (API & Serving) | Benchmark with target: P99 latency < 200ms |
| Docker/version compatibility (P9) | Phase 5 (Docker) | CI smoke test: build + run ONNX inference on a single input |
| DVC management (P10) | Phase 2 (Scaffolding) | `dvc remote list` returns configured remote; `dvc status` shows clean |
| PyTorch/ONNX skew (P11) | Phase 6 (ONNX Export) | Numerical diff test in export script |
| Celery overhead (P12) | Phase 2 (Architecture) | Benchmark: latency with Celery vs without for single request |

---

## Sources

- Conneau et al. (2020) "Unsupervised Cross-lingual Representation Learning at Scale" (XLM-R paper) — curse of multilinguality, capacity dilution trade-off
- Šmíd & Král (2025) "Cross-lingual aspect-based sentiment analysis: A survey on tasks, approaches, and challenges" — Information Fusion, Vol 120
- Hugging Face Transformers documentation — `word_ids()` for BIO alignment, ONNX export with Optimum
- PyTorch ONNX exporter GitHub issues (#110801) — dynamic axes tracing problems with TransformerEncoder
- ONNX Runtime documentation — version compatibility matrix, graph optimization levels, quantization guide
- Microsoft LID-tool — token-level language identification for code-mixed text
- GLUECoS benchmark (Khanuja et al.) — evaluation benchmark for code-switched NLP across English-Hindi
- SemEval 2014-2016 Task 4 - ABSA datasets — class imbalance ratios documented in multiple papers
- "NeutralABSA" (Waingankar & Patel) — techniques for improving neutral sentiment classification using class-weighted training
- DVC documentation — best practices for remote setup, .dvcignore, pipeline definitions
- Docker + ONNX Runtime compatibility notes from microsoft/onnxruntime Dockerfiles README
- "Hinglish helps users engage with a wider audience on social media, but poses challenges for NLP" — ETGovernment, June 2024
- Multiple GitHub issues (pytorch/pytorch#110801, microsoft/onnxruntime#26309) — ONNX export and Python version constraints
- Personal experience / known issues from projects combining multilingual transformers with production ONNX deployment

---

*Pitfalls research for: Multilingual-ABSA (English, Hindi, Hinglish)*
*Researched: 2026-06-22*
