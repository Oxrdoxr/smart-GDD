"""
Smart GDD Creator — Entry Point
Run: streamlit run app/main.py  (from project root)
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import streamlit as st
from pipeline import run_pipeline
from ui import render_sidebar, render_input, render_results
from utils.state import init_state

st.set_page_config(page_title="GDD Creator", page_icon="🎮", layout="wide")

css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_state()
render_sidebar()

st.markdown("# 🎮 GDD CREATOR")
st.markdown("<p style='color:#388e3c;'>One sentence → Full <b>Game Design Document</b></p>", unsafe_allow_html=True)
st.markdown("---")

keys_ready = st.session_state.get("keys_confirmed", False) or (
    bool(os.getenv("GEMINI_API_KEY")) and bool(os.getenv("ANTHROPIC_API_KEY"))
)

if not keys_ready:
    st.info("👈 Enter your API keys in the sidebar to get started.")
elif not st.session_state.pipeline_run:
    render_input(run_pipeline)
else:
    render_results()