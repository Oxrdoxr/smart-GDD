"""
utils/state.py — Streamlit session state initializer
"""
import streamlit as st


def init_state():
    defaults = {
        "pipeline_run":      False,
        "revision_count":    0,
        "game_idea":         "",
        "planner_output":    None,
        "researcher_output": None,
        "writer_output":     None,
        "reviewer_output":   None,
        "review_passed":     False,
        "current_step":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
