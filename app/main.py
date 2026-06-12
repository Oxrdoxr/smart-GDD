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

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_state()

# ─────────────────────────────────────────────
# STEP 0 — API KEY GATE
# Each user enters their own keys — stored in session only
# ─────────────────────────────────────────────
def render_api_gate():
    st.markdown("# 🎮 GDD CREATOR")
    st.markdown("<p style='color:#388e3c;'>One sentence → Full <b>Game Design Document</b></p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔑 Enter Your API Keys")
    st.markdown(
        "<p style='color:#4a7c59; font-size:0.9rem;'>"
        "Your keys are stored only in your session — never saved or shared."
        "</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<div class='px-card done'>"
            "<b>🟢 Gemini API Key</b><br>"
            "<span style='font-size:0.8rem;color:#4a7c59'>Free at aistudio.google.com</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        gemini_key = st.text_input(
            "Gemini Key",
            type="password",
            placeholder="AIzaSy...",
            label_visibility="collapsed",
            key="gemini_input",
        )

    with col2:
        st.markdown(
            "<div class='px-card done'>"
            "<b>🟣 Anthropic API Key</b><br>"
            "<span style='font-size:0.8rem;color:#4a7c59'>Get at console.anthropic.com</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        anthropic_key = st.text_input(
            "Anthropic Key",
            type="password",
            placeholder="sk-ant-...",
            label_visibility="collapsed",
            key="anthropic_input",
        )

    st.markdown("&nbsp;")
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        confirm = st.button("▶ CONFIRM & START", use_container_width=True)

    if confirm:
        if not gemini_key.strip() or not anthropic_key.strip():
            st.warning("Please enter both API keys to continue.")
        else:
            # Store in session state — never written to disk
            st.session_state.gemini_api_key    = gemini_key.strip()
            st.session_state.anthropic_api_key = anthropic_key.strip()
            st.session_state.keys_confirmed    = True

            # Inject into environment so router.py picks them up
            os.environ["GEMINI_API_KEY"]    = gemini_key.strip()
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key.strip()

            # Re-initialize router with new keys
            import utils.router as router
            import google.generativeai as genai
            from anthropic import Anthropic
            genai.configure(api_key=gemini_key.strip())
            router.anthropic_client = Anthropic(api_key=anthropic_key.strip())

            st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.8rem; color:#4a7c59;'>"
        "🔒 <b>Privacy:</b> Keys live only in your browser session. "
        "Refreshing the page clears them completely."
        "<br><br>"
        "📖 Get a free Gemini key: <a href='https://aistudio.google.com' target='_blank' style='color:#388e3c'>aistudio.google.com</a> &nbsp;|&nbsp; "
        "Anthropic key: <a href='https://console.anthropic.com' target='_blank' style='color:#388e3c'>console.anthropic.com</a>"
        "</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# ROUTING
# ─────────────────────────────────────────────

# Check if keys already exist (env vars set by owner, or already confirmed this session)
keys_in_env = bool(os.getenv("GEMINI_API_KEY")) and bool(os.getenv("ANTHROPIC_API_KEY"))
keys_confirmed = st.session_state.get("keys_confirmed", False)

if not keys_in_env and not keys_confirmed:
    # Show API key gate
    render_api_gate()
else:
    # Keys available — show the app
    render_sidebar()

    st.markdown("# 🎮 GDD CREATOR")
    st.markdown("<p style='color:#388e3c;'>One sentence → Full <b>Game Design Document</b></p>", unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.pipeline_run:
        render_input(run_pipeline)
    else:
        render_results()