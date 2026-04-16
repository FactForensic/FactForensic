import logging
import time
import re
import threading
import json
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# HF Bias Detection
# --------------------------------------------------------------------------- #
_hf_client = None


def get_hf_bias(text: str) -> str:
    """
    Get political bias label from HF model (detre/bias_detection).
    Returns 'Left', 'Center', or 'Right'. Falls back to 'Center' on any error.
    """
    global _hf_client
    if _hf_client is None:
        try:
            from gradio_client import Client
            _hf_client = Client("detre/bias_detection", verbose=False)
        except Exception as e:
            logger.error(f"Error initializing HF client: {e}")
            return "Center"
    try:
        result = _hf_client.predict(text=text[:2000], api_name="/predict_bias")
        if isinstance(result, dict):
            bias_label = str(result.get("label", "Center"))
            if bias_label in ["0", "LABEL_0", "Left"]:
                return "Left"
            elif bias_label in ["2", "LABEL_2", "Right"]:
                return "Right"
            else:
                return "Center"
        logger.warning(f"Unexpected HF bias result format: {result}")
        return "Center"
    except Exception as e:
        logger.error(f"Error predicting bias: {e}")
        return "Center"


# --------------------------------------------------------------------------- #
# Simple rate-limiter: Groq free tier = 6000 TPM for llama-3.1-8b-instant.
# Each request uses ~900-1200 tokens. Spacing calls 12s apart gives ~5/min,
# comfortably under the limit even with the largest articles.
# --------------------------------------------------------------------------- #
_groq_lock = threading.Lock()
_groq_last_call_time = 0.0
_GROQ_MIN_INTERVAL = 12  # seconds between consecutive Groq calls


def _groq_rate_limited_sleep():
    """Ensure at least _GROQ_MIN_INTERVAL seconds between consecutive Groq calls."""
    global _groq_last_call_time
    with _groq_lock:
        now = time.monotonic()
        elapsed = now - _groq_last_call_time
        if elapsed < _GROQ_MIN_INTERVAL:
            sleep_for = _GROQ_MIN_INTERVAL - elapsed
            logger.debug(f"Groq rate limiter: sleeping {sleep_for:.1f}s")
            time.sleep(sleep_for)
        _groq_last_call_time = time.monotonic()


def get_groq_objectivity_score(text: str) -> int | None:
    """
    Returns an objectivity score from 0 to 100 using Llama 3.1 8B via Groq.
    Returns None if the call fails.
    """
    api_key = getattr(settings, "GROQ_API_KEY", "")
    if not api_key:
        logger.warning("GROQ_API_KEY is not set in Django settings.")
        return None

    if not text or not text.strip():
        logger.warning("Empty text passed to objectivity scorer.")
        return None

    system_msg = (
        "You are a senior media analyst who scores journalistic objectivity.\n"
        "You MUST return ONLY a valid JSON object containing a short 'reasoning' string and a 'score' (an integer from 0 to 100).\n\n"
        "Calibration reference points (use these to anchor your scoring):\n"
        "  95 \u2014 AP or Reuters wire copy with zero editorializing\n"
        "  88 \u2014 Straight news report with minor framing choices\n"
        "  80 \u2014 News analysis with some interpretive language\n"
        "  72 \u2014 Investigative piece with clear perspective\n"
        "  60 \u2014 News with noticeable editorial slant\n"
        "  45 \u2014 Strongly opinionated reporting\n"
        "  30 \u2014 Editorial or opinion column\n"
        "  15 \u2014 Propaganda or heavily one-sided polemic\n\n"
        "Score each article independently. Do NOT default to any single number.\n"
        "Even small differences in tone, sourcing, or balance should shift the score."
    )

    # Truncate cleanly at sentence boundary
    truncated_text = _truncate_at_sentence(text, max_chars=6000)

    user_msg = (
        "Evaluate the objectivity of this article across five dimensions:\n"
        "1. Emotional Language Intensity (0=neutral, 20=highly emotional)\n"
        "2. Opinion vs Fact Ratio (0=purely factual, 20=mostly opinion)\n"
        "3. Balance of Viewpoints (0=balanced, 20=one-sided)\n"
        "4. Use of Verifiable Evidence (0=strong sourcing, 20=weak sourcing)\n"
        "5. Sensationalism (0=none, 20=extreme)\n\n"
        "Objectivity = 100 minus total subjectivity points.\n"
        "Return ONLY the final JSON object in this exact format. Keep reasoning under 10 words:\n"
        '{"reasoning": "short internal thought", "score": 85}\n\n'
        f"ARTICLE:\n{truncated_text}"
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    for attempt in range(1, 4):  # 3 attempts
        try:
            _groq_rate_limited_sleep()  # enforce spacing BEFORE every call

            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                temperature=0.0,
                top_p=1,
                max_tokens=60,
                response_format={"type": "json_object"},
            )

            response_content = chat_completion.choices[0].message.content.strip()
            logger.debug(f"[Groq raw response] attempt={attempt}: '{response_content}'")

            try:
                data = json.loads(response_content)
                score = data.get("score")
                if score is not None:
                    score = int(score)
            except Exception:
                score = None

            if score is not None:
                score = max(0, min(100, score))
                logger.info(f"Objectivity score: {score}")
                return score
            else:
                logger.warning(
                    f"Invalid JSON or no score found in Groq response: '{response_content}'"
                )

        except Exception as e:
            logger.error(f"Groq API error on attempt {attempt}/3: {e}")
            if attempt < 3:
                # Read the exact wait time from the 429 error, add 2s buffer
                wait = 2 ** attempt  # default fallback: 2s, 4s
                match = re.search(r"Please try again in ([\d.]+)s", str(e))
                if match:
                    wait = float(match.group(1)) + 2
                logger.info(f"Retrying in {wait:.1f}s...")
                time.sleep(wait)

    logger.error("All 3 Groq attempts failed. Returning None.")
    return None


def _truncate_at_sentence(text: str, max_chars: int = 6000) -> str:
    """
    Truncates text to max_chars at the nearest sentence boundary.
    Falls back to hard truncation if no sentence boundary is found.
    """
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    last_period = truncated.rfind(". ")

    if last_period != -1:
        return truncated[: last_period + 1]

    return truncated  # fallback: hard cut
