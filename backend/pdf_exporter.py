"""
Printable PDF & Document Exporter
Step 1: HTML-to-PDF report template (executive header, score pills,
metric cards, GRI alignment table, priority gap badges)
"""

# Embedded CSS keeps this a single, dependency-light file
REPORT_CSS = """
<style>
    body { font-family: Helvetica, Arial, sans-serif; color: #1a1a1a; margin: 40px; }
    .header { border-bottom: 3px solid #2c5f2d; padding-bottom: 12px; margin-bottom: 20px; }
    .header h1 { margin: 0; font-size: 24px; }
    .header .date { color: #666; font-size: 12px; }

    /* Composite score shown as a rounded "pill" badge */
    .score-pill {
        display: inline-block; padding: 6px 16px; border-radius: 20px;
        font-weight: bold; font-size: 18px; color: white; margin-top: 8px;
    }

    /* Metric cards laid out in a row, one per ESG pillar */
    .metric-cards { display: flex; gap: 12px; margin: 20px 0; }
    .metric-card {
        flex: 1; border: 1px solid #ddd; border-radius: 8px;
        padding: 14px; text-align: center; background: #fafafa;
    }
    .metric-card .label { font-size: 11px; color: #666; text-transform: uppercase; }
    .metric-card .value { font-size: 22px; font-weight: bold; margin-top: 4px; }

    .section { margin: 24px 0; }
    .section h2 { font-size: 16px; border-left: 4px solid #2c5f2d; padding-left: 8px; }
    .section p { font-size: 13px; line-height: 1.5; color: #333; }

    /* GRI standards alignment table */
    table.gri { width: 100%; border-collapse: collapse; margin-top: 8px; }
    table.gri th, table.gri td {
        border: 1px solid #ddd; padding: 8px; font-size: 12px; text-align: left;
    }
    table.gri th { background: #2c5f2d; color: white; }

    /* Priority badges used in the material gap analysis section */
    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 11px; font-weight: bold; color: white; margin: 3px 4px 3px 0;
    }
</style>
"""

# Priority level -> badge color, for material gap analysis
PRIORITY_COLORS = {"High": "#c0392b", "Medium": "#d98e04", "Low": "#2c5f2d"}


def _score_color(score: float) -> str:
    """Map a 0-100 score to a red/orange/green hex color band."""
    if score >= 75:
        return "#2c5f2d"   # green - strong
    if score >= 50:
        return "#d98e04"   # orange - moderate
    return "#c0392b"       # red - needs improvement


def _render_metric_cards(scores: dict) -> str:
    """Build the row of Environmental / Social / Governance score cards."""
    cards = ""
    for label, key in [
        ("Environmental", "environmental_score"),
        ("Social", "social_score"),
        ("Governance", "governance_score"),
    ]:
        value = scores.get(key, 0)
        cards += f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value" style="color:{_score_color(value)}">{value}</div>
        </div>"""
    return f'<div class="metric-cards">{cards}</div>'


def _render_gri_table() -> str:
    """Build the GRI 302 (Energy), 305 (Emissions), 405 (Diversity) table."""
    rows = [
        ("GRI 302", "Energy", "Scope 1 fuel and Scope 2 electricity data captured"),
        ("GRI 305", "Emissions", "Scope 1, 2 (location & market-based), and Scope 3 reported"),
        ("GRI 405", "Diversity & Equal Opportunity", "Workforce and executive diversity ratios reported"),
    ]
    body = "".join(
        f"<tr><td>{code}</td><td>{title}</td><td>{desc}</td></tr>"
        for code, title, desc in rows
    )
    return f'<table class="gri"><tr><th>Standard</th><th>Topic</th><th>Alignment</th></tr>{body}</table>'


def _render_gap_badges(gaps: list) -> str:
    """Build a color-coded badge for each material gap, by priority level."""
    badges = ""
    for gap in gaps:
        color = PRIORITY_COLORS.get(gap.get("priority", "Medium"), "#999")
        badges += (
            f'<span class="badge" style="background:{color}">'
            f'{gap["priority"]}: {gap["description"]}</span>'
        )
    return badges


def build_report_html(esg_data: dict, ai_report: dict, gaps: list = None,
                       company_name: str = "Company Name", report_date: str = "") -> str:
    """
    Assemble the full HTML report: header + score pill, metric cards,
    narrative sections, GRI alignment table, and priority gap badges.
    This HTML string is what gets converted to PDF in the next step.
    """
    composite = esg_data.get("composite_esg_score", 0)

    # Default sample gaps if the caller doesn't supply any
    gaps = gaps or [
        {"description": "Scope 3 upstream data incomplete", "priority": "High"},
        {"description": "No third-party emissions assurance", "priority": "Medium"},
    ]

    return f"""
    <html>
    <head>{REPORT_CSS}</head>
    <body>
        <div class="header">
            <h1>{company_name} - ESG Report</h1>
            <div class="date">{report_date}</div>
            <div class="score-pill" style="background:{_score_color(composite)}">
                Composite ESG Score: {composite}/100
            </div>
        </div>

        {_render_metric_cards(esg_data)}

        <div class="section">
            <h2>Executive Summary</h2>
            <p>{ai_report.get("executive_summary", "")}</p>
        </div>
        <div class="section">
            <h2>Environmental Narrative</h2>
            <p>{ai_report.get("environmental_narrative", "")}</p>
        </div>
        <div class="section">
            <h2>Social Review</h2>
            <p>{ai_report.get("social_review", "")}</p>
        </div>
        <div class="section">
            <h2>Governance Disclosure</h2>
            <p>{ai_report.get("governance_disclosure", "")}</p>
        </div>

        <div class="section">
            <h2>GRI Standards Alignment</h2>
            {_render_gri_table()}
        </div>

        <div class="section">
            <h2>Material Gap Analysis</h2>
            <p>{ai_report.get("material_gap_analysis", "")}</p>
            {_render_gap_badges(gaps)}
        </div>
    </body>
    </html>
    """


# Example usage
if __name__ == "__main__":
    sample_esg_data = {
        "environmental_score": 83.55,
        "social_score": 39.25,
        "governance_score": 88.67,
        "composite_esg_score": 71.79,
    }
    sample_ai_report = {
        "executive_summary": "The organization achieved a composite ESG score of 71.79/100.",
        "environmental_narrative": "Total emissions across Scope 1, 2, and 3 were tracked in detail.",
        "social_review": "Workforce diversity stood at 42.0%.",
        "governance_disclosure": "The board maintained 70.0% independence.",
        "material_gap_analysis": "Verify data completeness for Scope 3 upstream categories.",
    }

    html_output = build_report_html(sample_esg_data, sample_ai_report, report_date="2026-08-01")
    with open("sample_report.html", "w") as f:
        f.write(html_output)
    print("HTML report template generated: sample_report.html")