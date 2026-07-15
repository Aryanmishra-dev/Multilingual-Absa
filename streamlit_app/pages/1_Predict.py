import streamlit as st
import pandas as pd
from api.client import APIClient

st.set_page_config(page_title="Single Prediction", page_icon="🔍", layout="wide")

st.title("Single Text Prediction 🔍")
st.markdown("Analyze sentiment for individual reviews across English, Hindi, and Hinglish.")

client = APIClient()

with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        text_input = st.text_area("Enter review text:", height=150, placeholder="E.g., The battery life is amazing but the screen is too dim.")
    with col2:
        language = st.selectbox("Language", ["auto", "en", "hi", "hinglish"], index=0)
        predict_button = st.button("Analyze Sentiment", type="primary", use_container_width=True)

if predict_button and text_input:
    with st.spinner("Analyzing..."):
        result = client.predict(text_input, language)
        if result:
            st.success(f"Processed in {result.get('processing_time_ms', 0)} ms")
            st.subheader("Results")
            
            aspects = result.get("aspects", [])
            if not aspects:
                st.info("No aspects detected in this text.")
            else:
                for idx, asp in enumerate(aspects):
                    sentiment = asp.get("sentiment", "unknown")
                    color = "green" if sentiment == "positive" else "red" if sentiment == "negative" else "gray"
                    
                    st.markdown(
                        f"""
                        <div style="padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px; border-left: 5px solid {color};">
                            <h4>Aspect: {asp.get('aspect', 'N/A')}</h4>
                            <p><strong>Sentiment:</strong> <span style="color:{color};">{sentiment.upper()}</span></p>
                            <p><strong>Confidence:</strong> {asp.get('confidence', 0):.2f}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
