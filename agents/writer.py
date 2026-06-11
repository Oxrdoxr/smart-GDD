"""
agents/writer.py
Provider: Claude Sonnet (best creative writing + narrative depth)
Role: Generates all 8 GDD sections — the most important agent
"""
import json
from utils.router import call_model_with_fallback

SYSTEM_PROMPT = """You are a senior game designer writing a Game Design Document.
Be creative, specific, and engaging. Write 2-4 sentences per field.
Return ONLY valid JSON — no markdown, no extra text:
{
  "story_summary":      "compelling narrative premise",
  "protagonist":        "name, backstory, motivation",
  "core_mechanic":      "detailed main gameplay loop",
  "progression_system": "how player grows and unlocks content",
  "level_design":       "3-act structure with specific examples",
  "ui_ux_notes":        "key UI screens and UX philosophy",
  "monetization":       "business model with rationale",
  "art_direction":      "visual style, color palette, mood, inspirations",
  "free_assets":        "3 specific free asset sources that match this art style"
}"""


def run_writer(idea: str, planner: dict, researcher: dict) -> dict:
    msg = (
        f"Game idea: {idea}\n\n"
        f"Design pillars: {json.dumps(planner, indent=2)}\n\n"
        f"Market research: {json.dumps(researcher, indent=2)}"
    )
    raw = call_model_with_fallback("writer", SYSTEM_PROMPT, msg)
    return json.loads(raw)
