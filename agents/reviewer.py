"""
agents/reviewer.py
Provider: Claude Haiku (analytical + cheap + fast)
Role: QA — scores GDD 1-10, triggers revision loop if score < 7
"""
import json
from utils.router import call_model_with_fallback

SYSTEM_PROMPT = """You are a GDD quality reviewer. Evaluate feasibility, completeness, coherence.
Return ONLY valid JSON:
{
  "score": 8,
  "passed": true,
  "strengths": ["...", "..."],
  "issues": ["..."],
  "missing_sections": [],
  "recommendation": "brief overall verdict"
}
Rules: passed=true if score >= 7 and no critical missing sections."""


def run_reviewer(planner: dict, researcher: dict, writer: dict) -> dict:
    msg = (
        f"Planner output: {json.dumps(planner)}\n"
        f"Researcher output: {json.dumps(researcher)}\n"
        f"Writer output: {json.dumps(writer)}"
    )
    raw = call_model_with_fallback("reviewer", SYSTEM_PROMPT, msg)
    return json.loads(raw)
