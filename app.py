import os
import datetime
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from prompts import PROMPTS

load_dotenv()
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="PickWise - Product Recommendation Assistant", page_icon="🛒", layout="centered")

st.markdown("""
<style>
.block-container {max-width: 760px; padding-top: 2rem;}
h1 {font-weight: 800; letter-spacing: -0.5px;}
</style>
""", unsafe_allow_html=True)

st.title("🛒 PickWise")
st.caption("Tell me what you want to buy, your budget and how you'll use it. I'll help you choose.")

if not API_KEY:
    st.error("GROQ_API_KEY not found. Create a `.env` file next to app.py with: GROQ_API_KEY=your_key_here")
    st.stop()

client = Groq(api_key=API_KEY)

with st.sidebar:
    st.header("Test controls")
    model_name = st.text_input("Groq Model", value=DEFAULT_MODEL)
    version = st.radio("System prompt version", list(PROMPTS.keys()), index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.4, 0.1)
    with st.expander("View system prompt"):
        st.code(PROMPTS[version], language="markdown")
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Download transcript for assignment submission
if st.session_state.messages:
    log = f"PickWise test log | {version} | {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n"
    for m in st.session_state.messages:
        who = "USER" if m["role"] == "user" else "PICKWISE"
        log += f"[{who}]\n{m['content']}\n\n"
    st.sidebar.download_button("⬇️ Download transcript", log, file_name="pickwise_transcript.txt")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("e.g. Best laptop under Rs 50,000 for coding"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # System prompt is always injected server-side, never stored in editable chat history
    payload = [{"role": "system", "content": PROMPTS[version]}] + st.session_state.messages

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=model_name, messages=payload, temperature=temperature, max_tokens=700, stream=True
            )
            reply = st.write_stream(
                (c.choices[0].delta.content or "") for c in stream
            )
        except Exception as e:
            reply = f"⚠️ Error talking to Groq: {e}"
            st.error(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
