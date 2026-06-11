"""
agents/researcher.py
Provider: Gemini Flash (fast + factual)
Role: Market analysis — comparable games, gaps, risks, opportunities
"""
import json
from utils.router import call_model_with_fallback

SYSTEM_PROMPT = """Game market analyst. Research the market for this concept.
Return JSON only:
{
  "comparable_games": [{"title": "...", "revenue": "...", "why_relevant": "..."}],
  "market_gap": "...",
  "main_risk": "...",
  "main_opportunity": "...",
  "audience_size": "..."
}"""


def run_researcher(idea: str, planner: dict) -> dict:
    msg = f"Idea: {idea}\nPillars: {json.dumps(planner)}"
    raw = call_model_with_fallback("researcher", SYSTEM_PROMPT, msg)
    return json.loads(raw)
