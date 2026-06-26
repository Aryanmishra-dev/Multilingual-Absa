Most sentiment tools fail on Hindi reviews. I built one that doesn't.

The Indian market is flooded with product reviews in Hindi and Hinglish. Yet, most out-of-the-box sentiment models either fail entirely or just give a generic "Positive/Negative" for the whole text. 

I wanted to know exactly *what* users liked and disliked. So I built an end-to-end Multilingual Aspect-Based Sentiment Analysis (ABSA) platform. 

Instead of document-level sentiment, it extracts specific entities (e.g. "battery", "बैटरी") and scores them individually. 

By fine-tuning XLM-RoBERTa on a heavily curated dataset and leveraging cross-lingual transfer learning, the model generalized to Hindi incredibly well! I then quantized the pipeline down to ONNX INT8 to run inference at a blazing ~185ms on cheap CPU servers.

Key Metrics:
- EN Macro-F1: 78.1%
- HI Macro-F1: 67.8%
- Latency: < 200ms

Stack: FastAPI, Celery, React, PostgreSQL, Docker, Prometheus, and Evidently AI for drift detection.

Live Demo: [Link here]

Full project on GitHub — link in comments.
What other Indian language NLP problems should I tackle next?

#NLP #MachineLearning #Python #DataScience #MLOps #HindiNLP #OpenSource #BuildInPublic
