import logging

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

_flash = genai.GenerativeModel("gemini-1.5-flash")
_pro = genai.GenerativeModel("gemini-1.5-pro")


def generate(prompt: str, *, use_flash: bool = False) -> tuple[str, str, int, int]:
    """Call Gemini and return (text, model_name, tokens_in, tokens_out)."""
    model = _flash if use_flash else _pro
    model_name = "gemini-1.5-flash" if use_flash else "gemini-1.5-pro"

    response = model.generate_content(prompt)
    usage = getattr(response, "usage_metadata", None)
    tokens_in = getattr(usage, "prompt_token_count", 0) or 0
    tokens_out = getattr(usage, "candidates_token_count", 0) or 0

    return response.text, model_name, tokens_in, tokens_out
