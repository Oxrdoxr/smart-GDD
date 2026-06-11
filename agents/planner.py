"""
agents/planner.py
Provider: Gemini Flash (fast + structured)
Role: Expands one-line idea into design pillars
"""
import json
from utils.router import call_model_with_fallback

SYSTEM_PROMPT = """Game design strategist. Expand a one-line idea into design pillars.
Return JSON only:
{
  "genre": "...",
  "core_loop": "...",
  "target_audience": "...",
  "platform": "...",
  "tone": "...",
  "pillars": ["...", "...", "..."],
  "unique_hook": "..."
}"""


def run_planner(idea: str) -> dict:
    raw = call_model_with_fallback("planner", SYSTEM_PROMPT, f"Game idea: {idea}")
    return json.loads(raw)
