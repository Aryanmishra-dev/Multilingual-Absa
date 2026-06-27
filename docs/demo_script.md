# Demo Script (3-Minute Walkthrough)

**00:00 — Open live dashboard**
*Action*: Navigate to the Vercel live URL. Show the clean React interface, explaining that the backend is powered by FastAPI and PostgreSQL.

**00:15 — Type English review, show aspect results**
*Action*: Paste the first review from `demo_single_reviews.txt`: "The phone has an amazing screen but the battery life is terrible."
*Narration*: "Let's start with a standard English review. Notice how the model doesn't just say 'Mixed Sentiment'. It highlights 'screen' as positive (green) and 'battery life' as negative (red)."

**00:40 — Type Hindi review, show language detection + aspects**
*Action*: Paste the Hindi review: "फोन की बैटरी अच्छी है लेकिन कैमरा बेकार है"
*Narration*: "Now, what makes this platform special is its multilingual support. I paste a Hindi review, and instantly the system detects Hindi. It successfully tags 'बैटरी' (battery) as positive and 'कैमरा' (camera) as negative."

**01:10 — Upload sample CSV, show batch processing + progress**
*Action*: Navigate to the Analytics tab and drag/drop `sample_reviews.csv`.
*Narration*: "For enterprise use, we have bulk processing. Behind the scenes, Celery workers take over. Watch the real-time polling update the progress bar seamlessly."

**01:50 — Show analytics charts (sentiment distribution)**
*Action*: Scroll down to view the rendered Recharts.
*Narration*: "Once completed, we get aggregated insights. Here's our Sentiment over time, Top Aspects across the batch, and our Language Distribution pie chart."

**02:20 — Show Grafana monitoring dashboard**
*Action*: Switch tabs to the Grafana dashboard (`localhost:3001` or deployed URL).
*Narration*: "Production reliability is crucial. Here we see our Prometheus metrics scraped from FastAPI: request rates, P95 latency consistently under 200ms, and Celery worker health."

**02:45 — Show HuggingFace Hub model page**
*Action*: Switch to the HuggingFace Hub repository.
*Narration*: "Finally, our optimized INT8 ONNX models are hosted publicly on HuggingFace Hub. Thank you for watching!"

