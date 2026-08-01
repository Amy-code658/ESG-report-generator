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


# Fixed set of sections the AI must return, matching report requirements
REPORT_SECTIONS = [
    "executive_summary",
    "environmental_narrative",
    "social_review",
    "governance_disclosure",
    "gri_alignment",
    "material_gap_analysis",
]


def build_report_prompt(esg_data: dict) -> str:
    """
    Build a prompt that instructs Gemini to return a strict JSON object
    covering all required ESG report sections, based on calculated metrics.
    """
    prompt = f"""
You are an ESG reporting analyst. Using the metrics below, write a corporate
sustainability report. Respond ONLY with valid JSON (no markdown, no extra
text) using exactly these keys:

- "executive_summary": 2-3 sentence high-level overview of ESG performance
- "environmental_narrative": discussion of emissions performance (Scope 1/2/3)
- "social_review": discussion of diversity, training, and safety performance
- "governance_disclosure": discussion of board, ethics, and cyber governance
- "gri_alignment": how the data aligns with GRI 302 (Energy), GRI 305
  (Emissions), and GRI 405 (Diversity & Equal Opportunity) standards
- "material_gap_analysis": key data gaps or risks that should be addressed

ESG Metrics:
{json.dumps(esg_data, indent=2)}
""".strip()

    return prompt


def parse_report_response(raw_text: str) -> dict:
    """
    Parse the model's JSON response into a dict, tolerating cases where
    Gemini wraps the JSON in markdown code fences.
    """
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Return empty strings for each section if parsing fails
        return {section: "" for section in REPORT_SECTIONS}


def generate_fallback_report(esg_data: dict) -> dict:
    """
    Rule-based narrative synthesis used when no Gemini API key is available.
    Builds each report section from simple templates driven by the metrics.
    """
    total_emissions = (
        esg_data.get("total_scope1_emissions_kgco2e", 0)
        + esg_data.get("market_based_kgco2e", 0)
        + esg_data.get("total_scope3_emissions_kgco2e", 0)
    )
    diversity = esg_data.get("diversity_pct", 0)
    board_independence = esg_data.get("board_independence_pct", 0)
    composite_score = esg_data.get("composite_esg_score", 0)

    # Pick a performance descriptor based on the composite score band
    if composite_score >= 75:
        performance_word = "strong"
    elif composite_score >= 50:
        performance_word = "moderate"
    else:
        performance_word = "developing"

    return {
        "executive_summary": (
            f"The organization achieved a composite ESG score of {composite_score}/100, "
            f"reflecting {performance_word} performance across environmental, social, "
            f"and governance dimensions."
        ),
        "environmental_narrative": (
            f"Total emissions across Scope 1, 2, and 3 activities were "
            f"{total_emissions:.0f} kgCO2e for the reporting period, covering direct "
            f"fuel use, purchased electricity, business travel, and waste."
        ),
        "social_review": (
            f"Workforce diversity stood at {diversity:.1f}%, with training and safety "
            f"metrics tracked to support employee development and wellbeing."
        ),
        "governance_disclosure": (
            f"The board maintained {board_independence:.1f}% independence, supported "
            f"by ethics policy compliance and periodic cyber risk audits."
        ),
        "gri_alignment": (
            "Reported metrics align with GRI 302 (Energy), GRI 305 (Emissions), and "
            "GRI 405 (Diversity & Equal Opportunity) disclosure requirements."
        ),
        "material_gap_analysis": (
            "Automated fallback report: verify data completeness for Scope 3 "
            "upstream categories and seek third-party assurance of disclosed figures."
        ),
    }


def synthesize_esg_report(esg_data: dict) -> dict:
    """
    Main entry point: try Gemini first, fall back to rule-based synthesis
    if no API key is set, the call fails, or the response can't be parsed.
    """
    prompt = build_report_prompt(esg_data)
    raw_output = call_gemini_api(prompt)

    if raw_output:
        report = parse_report_response(raw_output)
        if any(report.values()):  # parsing succeeded and sections are populated
            return report

    return generate_fallback_report(esg_data)


# Example usage
if __name__ == "__main__":
    sample_esg_data = {
        "total_scope1_emissions_kgco2e": 4402.0,
        "market_based_kgco2e": 2400.0,
        "total_scope3_emissions_kgco2e": 1424.0,
        "diversity_pct": 42.0,
        "board_independence_pct": 70.0,
        "composite_esg_score": 71.79,
    }

    report = synthesize_esg_report(sample_esg_data)
    print(json.dumps(report, indent=2))