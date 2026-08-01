"""
AI Report Synthesis Engine
Step 1: Google Gemini API integration (gemini-2.5-flash) via urllib.request
"""

import os
import json
import urllib.request
import urllib.error

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)


def get_api_key() -> str:
    """Read the Gemini API key from the environment (kept out of source code)."""
    return os.environ.get("GEMINI_API_KEY", "")


def call_gemini_api(prompt: str, api_key: str = None) -> str:
    """
    Send a text prompt to the Gemini API and return the generated response.

    Uses urllib.request directly, no external HTTP libraries required.
    Returns an empty string if no key is set or the call fails, so callers
    can detect this and fall back to rule-based synthesis (added in Step 3).
    """
    api_key = api_key or get_api_key()
    if not api_key:
        return ""

    # Gemini expects a "contents" list with role/parts structure
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    }

    url = f"{GEMINI_API_URL}?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            # Navigate the response structure to pull out the generated text
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError) as e:
        print(f"Gemini API call failed: {e}")
        return ""


# Example usage
if __name__ == "__main__":
    sample_prompt = "Say hello in one sentence."
    output = call_gemini_api(sample_prompt)
    print(output or "No API key set or call failed.")