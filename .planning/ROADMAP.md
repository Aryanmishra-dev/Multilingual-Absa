# Roadmap: Multilingual ABSA

**Version:** 1.0
**Created:** 2026-06-22
**Core Value:** Accurately extract aspect terms and their sentiment from product reviews across English, Hindi, and Hinglish

## Phases

- [ ] **Phase 1: Project Scaffolding & Data Pipeline** - Foundation: project structure, dependency management, DVC, MLflow, data acquisition, preprocessing, language detection, and BIO alignment validation
- [ ] **Phase 2: Aspect Term Extraction Training** - Fine-tune XLM-RoBERTa for BIO token classification; establish Macro-F1 evaluation baseline
- [ ] **Phase 3: Sentiment Classification Training & Cross-Lingual Evaluation** - Fine-tune 4-class sentiment model; joint training with shared encoder; evaluate cross-lingual performance
- [ ] **Phase 4: ONNX Export & Inference API** - Export models to ONNX; build FastAPI inference endpoint with preprocessing pipeline
- [ ] **Phase 5: Docker & Deployment** - Containerize API and frontend; deploy to Railway and Vercel
- [ ] **Phase 6: Frontend Dashboard** - React dashboard with Recharts visualizations, KPI cards, and result export

## Phase Details

### Phase 1: Project Scaffolding & Data Pipeline
**Goal:** Developer can clone the repo, preprocess multilingual data with verified BIO alignment, and track experiments in MLflow
**Mode:** mvp
**Depends on:** Nothing (first phase)
**Requirements:** SCAFF-01, SCAFF-02, SCAFF-03, SCAFF-04, SCAFF-05, SCAFF-06, SCAFF-07, SCAFF-08, SCAFF-09, SCAFF-10
**Success Criteria** (what must be TRUE):
1. Developer can clone repo, create virtual env, install all dependencies with `pip install -e ".[dev]"`, and pre-commit hooks run on commit
2. Data download script fetches SemEval 2014 ABSA datasets (laptop + restaurant) and EDA notebook visualizes data/label/language distributions
3. Hinglish text is correctly normalized via `dhvani` and routed through language detection (English / Hindi / Hinglish)
4. BIO alignment function passes multilingual unit tests — correct label propagation for SentencePiece subword splits in English, Hindi, and Hinglish
5. DVC tracks all dataset versions and MLflow tracking server records experiment runs visible in the UI
**Plans:** TBD

### Phase 2: Aspect Term Extraction Training
**Goal:** Fine-tuned XLM-RoBERTa ATE model achieves baseline Macro-F1 on SemEval 2014 test split, with per-language and per-class metrics logged to MLflow
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** ATE-01, ATE-02, ATE-03, ATE-04, EVAL-01
**Success Criteria** (what must be TRUE):
1. ATE model fine-tuned with BIO tagging produces correct span-level predictions (B-ASP, I-ASP, O) on English test reviews
2. Subword-aware BIO alignment using `word_ids()` produces correct labels for SentencePiece tokenization across all three languages
3. Training runs logged to MLflow with all params, per-class precision/recall/F1, and model artifacts saved
4. Macro-F1 computed and reported as the primary evaluation metric per tag class (B-ASP, I-ASP, O) and per language
**Plans:** TBD

### Phase 3: Sentiment Classification Training & Cross-Lingual Evaluation
**Goal:** Working ASC model with weighted loss mitigates neutral class bias; cross-lingual evaluation shows per-language end-to-end F1
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** ASC-01, ASC-02, ASC-03, ASC-04, EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
1. ASC model predicts 4-class sentiment (positive/negative/neutral/conflict) per extracted aspect with accuracy matching published baselines
2. Weighted cross-entropy loss keeps per-class F1s within 10 points of each other (no single class dominates)
3. Joint training pipeline with shared XLM-RoBERTa encoder (ATE + ASC heads) logs both stages' metrics to a single MLflow run
4. Cross-lingual evaluation reports per-language Macro-F1 (English, Hindi, Hinglish) for the full ATE→ASC pipeline
5. Per-language confusion matrices visualize sentiment classification errors for each language
**Plans:** TBD

### Phase 4: ONNX Export & Inference API
**Goal:** Users can send product reviews to a REST API and receive aspect-sentiment pairs with confidence scores, served via ONNX Runtime
**Mode:** mvp
**Depends on:** Phase 3
**Requirements:** ONNX-01, ONNX-02, ONNX-03, ONNX-04, ONNX-05, ONNX-06
**Success Criteria** (what must be TRUE):
1. ATE and ASC models export as separate ONNX models and pass numerical parity tests against PyTorch (atol < 1e-4)
2. `POST /predict` endpoint accepts text input and returns structured JSON with aspect terms, sentiment labels, and confidence scores
3. Input pipeline automatically detects language (English/Hindi/Hinglish), normalizes Hinglish via dhvani, and tokenizes correctly
4. API returns clear error responses for empty text, inputs exceeding max length, and unsupported languages
**Plans:** TBD
### Phase 5: Docker & Deployment
**Goal:** The entire system runs via `docker-compose up` and is deployable to Railway (API) and Vercel (frontend)
**Mode:** mvp
**Depends on:** Phase 4
**Requirements:** DOCK-01, DOCK-02, DOCK-03, DOCK-04
**Success Criteria** (what must be TRUE):
1. `docker-compose up` starts the API with ONNX Runtime loaded and ready to serve inference requests
2. Multi-stage Dockerfile produces a slim production image (~200MB) with ONNX Runtime only (no PyTorch)
3. API deploys to Railway and responds correctly to `POST /predict` from a public URL
4. Frontend deploys to Vercel and is accessible via a public URL
**Plans:** TBD

### Phase 6: Frontend Dashboard
**Goal:** Users can submit reviews through a web dashboard, visualize aspect-sentiment distributions, and export results
**Mode:** mvp
**Depends on:** Phase 4 (API must exist; can parallelize with Phase 5)
**Requirements:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
1. Dashboard loads in browser and provides a text input for submitting reviews to the API
2. Aspect-sentiment distribution bar chart (Recharts) renders with correct counts from API response
3. Per-review result display highlights extracted aspect terms color-coded by sentiment (positive/green, negative/red)
4. Summary statistics KPI cards show total aspects, sentiment breakdown percentages, and language distribution
5. User can download analysis results as CSV or JSON files
**Plans:** TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Scaffolding & Data Pipeline | 0/0 | Not started | - |
| 2. Aspect Term Extraction Training | 0/0 | Not started | - |
| 3. Sentiment Classification Training & Cross-Lingual Evaluation | 0/0 | Not started | - |
| 4. ONNX Export & Inference API | 0/0 | Not started | - |
| 5. Docker & Deployment | 0/0 | Not started | - |
| 6. Frontend Dashboard | 0/0 | Not started | - |

---

*Roadmap created: 2026-06-22*
