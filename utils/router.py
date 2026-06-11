"""
utils/router.py — Multi-Provider Model Router

Routes each agent to the best model for its task:
  Planner    → Gemini Flash  (fast, structured JSON)
  Researcher → Gemini Flash  (fast, factual)
  Writer     → Claude Sonnet (best creative writing)
  Reviewer   → Claude Haiku  (analytical, cheap, fast)

Usage:
    from utils.router import call_model, AGENT_MAP
    response = call_model("writer", system_prompt, user_message)
"""

import os
import json
import google.generativeai as genai
from anthropic import Anthropic

# ─────────────────────────────────────────────
# API KEYS — set via env vars or paste directly
# ─────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY",   "YOUR_GEMINI_API_KEY_HERE")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY_HERE")

genai.configure(api_key=GEMINI_API_KEY)
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────
# AGENT → MODEL ROUTING TABLE
# Change any entry here to swap models globally
# ─────────────────────────────────────────────
AGENT_MAP = {
    "planner":    {"provider": "gemini",    "model": "gemini-1.5-flash-latest"},
    "researcher": {"provider": "gemini",    "model": "gemini-1.5-flash-latest"},
    "writer":     {"provider": "anthropic", "model": "claude-sonnet-4-5"},
    "reviewer":   {"provider": "anthropic", "model": "claude-haiku-4-5-20251001"},
}

# ─────────────────────────────────────────────
# PROVIDER CALL FUNCTIONS
# ─────────────────────────────────────────────

def _call_gemini(model_name: str, system_prompt: str, user_message: str) -> str:
    """Gemini call — forces JSON output via response_mime_type."""
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    response = model.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            response_mime_type="application/json",  # no JSONDecodeError
        ),
    )
    return response.text


def _extract_json(text: str) -> str:
    """Robustly extract JSON — strips markdown fences and any extra text."""
    import re
    text = re.sub(r'''```(?:json)?''',"", text).strip().rstrip("`").strip()
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end+1]
    return text


def _call_anthropic(model_name: str, system_prompt: str, user_message: str) -> str:
    """Anthropic call — extracts clean JSON from response."""
    response = anthropic_client.messages.create(
        model=model_name,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return _extract_json(response.content[0].text)


# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────

def call_model(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Route an agent call to the correct provider and model.

    Args:
        agent_name:    "planner" | "researcher" | "writer" | "reviewer"
        system_prompt: The agent's personality and output contract
        user_message:  The data/context to process

    Returns:
        Raw JSON string from the model
    """
    config = AGENT_MAP.get(agent_name)
    if not config:
        raise ValueError(f"Unknown agent: '{agent_name}'. Must be one of {list(AGENT_MAP.keys())}")

    provider = config["provider"]
    model    = config["model"]

    if provider == "gemini":
        return _call_gemini(model, system_prompt, user_message)
    elif provider == "anthropic":
        return _call_anthropic(model, system_prompt, user_message)
    else:
        raise ValueError(f"Unknown provider: '{provider}'")


# ─────────────────────────────────────────────
# OPTIONAL: FALLBACK WRAPPER
# If primary provider fails, falls back to the other
# ─────────────────────────────────────────────

def call_model_with_fallback(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Same as call_model but with automatic fallback to the other provider.
    Useful for demos where one quota might be exhausted.
    """
    config = AGENT_MAP[agent_name]
    primary_provider = config["provider"]

    try:
        return call_model(agent_name, system_prompt, user_message)
    except Exception as primary_err:
        fallback_provider = "anthropic" if primary_provider == "gemini" else "gemini"
        fallback_model    = "claude-haiku-4-5-20251001" if fallback_provider == "anthropic" else "gemini-1.5-flash-latest"
        print(f"  ⚠️  {primary_provider} failed ({primary_err}). Falling back to {fallback_provider}...")

        if fallback_provider == "gemini":
            return _call_gemini(fallback_model, system_prompt, user_message)
        else:
            return _call_anthropic(fallback_model, system_prompt, user_message)