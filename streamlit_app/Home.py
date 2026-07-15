import streamlit as st

st.set_page_config(
    page_title="Multilingual ABSA Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("Welcome to Multilingual ABSA Platform 🌍")
    st.markdown("### Aspect-Based Sentiment Analysis for English, Hindi, and Hinglish")
    
    st.info("This is a modern, responsive Streamlit dashboard for enterprise AI inference.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="System Health", value="Healthy", delta="🟢 API Online")
    with col2:
        st.metric(label="Supported Languages", value="3", delta="En, Hi, Hinglish")
    with col3:
        st.metric(label="Active Models", value="ONNX", delta="1.0.0")
    with col4:
        st.metric(label="Recent Predictions", value="1,245", delta="+12 today")

    st.markdown("---")
    st.markdown("### Quick Actions")
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("🔍 Single Prediction", use_container_width=True):
            st.switch_page("pages/1_Predict.py")
    with colB:
        if st.button("📁 Batch Processing", use_container_width=True):
            st.switch_page("pages/2_Batch_Prediction.py")
    with colC:
        if st.button("📊 View Analytics", use_container_width=True):
            st.switch_page("pages/3_Analytics.py")

if __name__ == "__main__":
    main()
