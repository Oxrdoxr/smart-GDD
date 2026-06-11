"""
utils/gemini.py — Single Gemini call wrapper used by all agents
"""
import google.generativeai as genai
import os

# Set via env var or hardcode for local dev
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=API_KEY)

MODEL = "gemini-1.5-flash"


def call_gemini(system_prompt: str, user_message: str) -> str:
    """
    Single function all 4 agents use.
    response_mime_type='application/json' forces clean JSON — eliminates JSONDecodeError.
    """
    model = genai.GenerativeModel(
        model_name=MODEL,
        system_instruction=system_prompt,
    )
    response = model.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            response_mime_type="application/json",
        ),
    )
    return response.text
