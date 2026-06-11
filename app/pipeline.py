"""
pipeline.py — Orchestrates the 4-agent sequential pipeline
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import streamlit as st
import time
from agents.planner    import run_planner
from agents.researcher import run_researcher
from agents.writer     import run_writer
from agents.reviewer   import run_reviewer

MAX_REVISIONS = 1


def road_progress(placeholder, pct: int, msg: str):
    placeholder.markdown(f"""
    <div class='road-wrap'>
      <div style='font-family:"Press Start 2P",monospace;font-size:0.6rem;color:#fff;margin-bottom:5px;'>{msg}</div>
      <div class='road-track'>
        <div class='road-fill' style='width:{pct}%'></div>
        <span class='road-car'>🚗</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def run_pipeline(idea: str):
    prog = st.empty()

    road_progress(prog, 5,  "PLANNER AGENT...")
    st.session_state.planner_output = run_planner(idea)

    road_progress(prog, 30, "RESEARCHER AGENT...")
    st.session_state.researcher_output = run_researcher(idea, st.session_state.planner_output)

    while st.session_state.revision_count <= MAX_REVISIONS:
        rev = f" REV {st.session_state.revision_count}" if st.session_state.revision_count > 0 else ""
        road_progress(prog, 55, f"WRITER AGENT{rev}...")
        st.session_state.writer_output = run_writer(
            idea, st.session_state.planner_output, st.session_state.researcher_output
        )

        road_progress(prog, 82, "REVIEWER AGENT...")
        st.session_state.reviewer_output = run_reviewer(
            st.session_state.planner_output,
            st.session_state.researcher_output,
            st.session_state.writer_output,
        )

        if st.session_state.reviewer_output.get("passed", False):
            st.session_state.review_passed = True
            break
        st.session_state.revision_count += 1
        if st.session_state.revision_count > MAX_REVISIONS:
            break

    road_progress(prog, 100, "GDD COMPLETE! 🏆")
    time.sleep(0.8)
    st.session_state.pipeline_run = True
    prog.empty()
