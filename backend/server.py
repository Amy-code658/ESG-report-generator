"""
ESG REST API & Web Server
Step 2: API routes for form drafts, submissions, report generation, and exports
"""

import json
import mimetypes
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "frontend"  # folder containing the frontend build

# Make sibling project modules importable (esg_calculator.py lives one level up)
sys.path.append(str(PROJECT_ROOT))

try:
    from esg_calculator import (
        calculate_scope1_emissions, calculate_scope2_emissions,
        calculate_scope3_emissions, calculate_social_metrics,
        calculate_governance_metrics, calculate_esg_score,
    )
except ImportError:
    # Server still runs without this; submit/report routes fall back gracefully
    calculate_scope1_emissions = calculate_scope2_emissions = None
    calculate_scope3_emissions = calculate_social_metrics = None
    calculate_governance_metrics = calculate_esg_score = None

try:
    from ai_engine import synthesize_esg_report
except ImportError:
    synthesize_esg_report = None

try:
    from pdf_exporter import build_report_html
except ImportError:
    build_report_html = None

HOST = "0.0.0.0"
PORT = 8000

# In-memory "database" for drafts and finalized submissions
DRAFTS = {}
SUBMISSIONS = {}


def compute_esg_report(form_data: dict) -> dict:
    """Run the full calculation pipeline on raw form data, then synthesize narrative."""
    if not calculate_scope1_emissions:
        return {"error": "calculation modules unavailable"}

    scope1 = calculate_scope1_emissions(form_data.get("fuel_usage", {}))
    scope2 = calculate_scope2_emissions(**form_data.get("electricity", {}))
    scope3 = calculate_scope3_emissions(
        form_data.get("travel", {}), form_data.get("waste", {})
    )
    social = calculate_social_metrics(form_data.get("social", {}))
    governance = calculate_governance_metrics(form_data.get("governance", {}))
    scores = calculate_esg_score(scope1, scope2, scope3, social, governance)

    esg_data = {**scores, **scope1, **scope2, **scope3, **social, **governance}
    ai_report = synthesize_esg_report(esg_data) if synthesize_esg_report else {}

    return {"esg_data": esg_data, "ai_report": ai_report}


class ESGRequestHandler(BaseHTTPRequestHandler):
    """Routes ESG API requests to the correct handler based on method + path."""

    def _read_json_body(self) -> dict:
        """Parse the JSON body of a POST request, defaulting to an empty dict."""
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _send_json(self, status: int, payload: dict):
        """Send a JSON response with the given status code."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- POST routes ----
    def do_POST(self):
        if self.path == "/api/v1/esg/form/draft":
            self._save_draft()
        elif self.path == "/api/v1/esg/form/submit":
            self._submit_form()
        elif self.path == "/api/v1/esg/generate-report":
            self._regenerate_report()
        else:
            self._send_json(404, {"error": "Not found"})

    def _save_draft(self):
        """Save (or update) a form draft, keyed by draft_id."""
        data = self._read_json_body()
        draft_id = data.get("draft_id") or str(uuid.uuid4())
        DRAFTS[draft_id] = {
            "form_data": data.get("form_data", {}),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._send_json(200, {"draft_id": draft_id, "status": "saved"})

    def _submit_form(self):
        """Finalize a form submission and trigger AI report generation."""
        data = self._read_json_body()
        submission_id = str(uuid.uuid4())
        report = compute_esg_report(data.get("form_data", {}))

        SUBMISSIONS[submission_id] = {
            "form_data": data.get("form_data", {}),
            "report": report,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        self._send_json(201, {"submission_id": submission_id, "report": report})

    def _regenerate_report(self):
        """Re-run AI narrative synthesis for an existing submission."""
        data = self._read_json_body()
        submission_id = data.get("submission_id")
        submission = SUBMISSIONS.get(submission_id)
        if not submission:
            self._send_json(404, {"error": "Submission not found"})
            return

        esg_data = submission["report"].get("esg_data", {})
        ai_report = synthesize_esg_report(esg_data) if synthesize_esg_report else {}
        submission["report"]["ai_report"] = ai_report
        self._send_json(200, {"submission_id": submission_id, "ai_report": ai_report})

    # ---- GET routes ----
    def do_GET(self):
        if self.path == "/api/v1/esg/submissions":
            self._list_submissions()
        elif self.path.startswith("/api/v1/esg/export-html/"):
            self._export_html()
        elif self.path.startswith("/api/"):
            self._send_json(404, {"error": "Not found"})
        else:
            self._serve_static()  # anything not under /api/ is a frontend asset

    def _list_submissions(self):
        """Return a summary list of all past submissions."""
        summary = [
            {"submission_id": sid, "submitted_at": s["submitted_at"]}
            for sid, s in SUBMISSIONS.items()
        ]
        self._send_json(200, {"submissions": summary})

    def _export_html(self):
        """Export the full report as a rendered HTML page, by submission id."""
        submission_id = self.path.rsplit("/", 1)[-1]
        submission = SUBMISSIONS.get(submission_id)
        if not submission:
            self._send_json(404, {"error": "Submission not found"})
            return

        esg_data = submission["report"].get("esg_data", {})
        ai_report = submission["report"].get("ai_report", {})
        html = build_report_html(esg_data, ai_report) if build_report_html else "<p>Report unavailable</p>"

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self):
        """Serve a file from the frontend directory (defaults to index.html)."""
        request_path = self.path.split("?", 1)[0]
        if request_path == "/":
            request_path = "/index.html"

        file_path = (STATIC_DIR / request_path.lstrip("/")).resolve()

        # Block requests that try to escape the static directory (path traversal)
        if STATIC_DIR not in file_path.parents:
            self._send_json(403, {"error": "Forbidden"})
            return

        if not file_path.is_file():
            self._send_json(404, {"error": "File not found"})
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = HOST, port: int = PORT):
    """Start the threaded HTTP server (handles multiple requests concurrently)."""
    server = ThreadingHTTPServer((host, port), ESGRequestHandler)
    print(f"ESG server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    run_server()