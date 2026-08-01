"""Production-grade SQLite database access layer for the ESG application.

This module provides a small, dependency-free persistence layer built on the
Python standard-library :mod:`sqlite3` module. It centralizes database
initialization, upsert write operations, and read helpers used by the ESG
application workflows.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().with_name("esg_app.db")


def _get_connection() -> sqlite3.Connection:
    """Create and configure a SQLite connection with dict-like row access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _serialize_json(value: Optional[Any]) -> Optional[str]:
    """Serialize a Python object into a JSON string for persistence."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _deserialize_json(value: Optional[str]) -> Optional[Any]:
    """Deserialize a JSON string back into Python data when present."""
    if value in (None, ""):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def init_db() -> None:
    """Initialize the database schema if it does not yet exist."""
    connection = _get_connection()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                facility_location TEXT,
                fiscal_year INTEGER NOT NULL,
                quarter TEXT DEFAULT 'Annual',
                reporting_boundary TEXT DEFAULT 'Operational Control',
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS esg_data (
                submission_id TEXT PRIMARY KEY,
                environmental_data TEXT,
                social_data TEXT,
                governance_data TEXT,
                calculated_metrics TEXT,
                FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                submission_id TEXT NOT NULL,
                title TEXT NOT NULL,
                executive_summary TEXT,
                environmental_narrative TEXT,
                social_narrative TEXT,
                governance_narrative TEXT,
                gri_alignment TEXT,
                gap_analysis TEXT,
                esg_score REAL,
                status TEXT DEFAULT 'final',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def save_submission(
    id_str: str,
    company_name: str,
    facility_location: str,
    fiscal_year: int,
    quarter: str,
    reporting_boundary: str,
    status: str = "draft",
) -> None:
    """Insert a new submission or update an existing one using an UPSERT pattern."""
    connection = _get_connection()
    try:
        connection.execute(
            """
            INSERT INTO submissions (
                id,
                company_name,
                facility_location,
                fiscal_year,
                quarter,
                reporting_boundary,
                status,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                company_name = excluded.company_name,
                facility_location = excluded.facility_location,
                fiscal_year = excluded.fiscal_year,
                quarter = excluded.quarter,
                reporting_boundary = excluded.reporting_boundary,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                id_str,
                company_name,
                facility_location,
                fiscal_year,
                quarter,
                reporting_boundary,
                status,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def save_esg_data(
    submission_id: str,
    env_data: dict,
    soc_data: dict,
    gov_data: dict,
    calculated_metrics: dict,
) -> None:
    """Persist ESG section payloads as JSON strings using a write-through UPSERT."""
    connection = _get_connection()
    try:
        connection.execute(
            """
            INSERT INTO esg_data (
                submission_id,
                environmental_data,
                social_data,
                governance_data,
                calculated_metrics
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(submission_id) DO UPDATE SET
                environmental_data = excluded.environmental_data,
                social_data = excluded.social_data,
                governance_data = excluded.governance_data,
                calculated_metrics = excluded.calculated_metrics
            """,
            (
                submission_id,
                _serialize_json(env_data),
                _serialize_json(soc_data),
                _serialize_json(gov_data),
                _serialize_json(calculated_metrics),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_submission(submission_id: str) -> Optional[dict]:
    """Fetch one submission together with its ESG payloads and deserialize JSON content."""
    connection = _get_connection()
    try:
        row = connection.execute(
            """
            SELECT
                s.id,
                s.company_name,
                s.facility_location,
                s.fiscal_year,
                s.quarter,
                s.reporting_boundary,
                s.status,
                s.created_at,
                s.updated_at,
                e.environmental_data,
                e.social_data,
                e.governance_data,
                e.calculated_metrics
            FROM submissions AS s
            LEFT JOIN esg_data AS e ON e.submission_id = s.id
            WHERE s.id = ?
            """,
            (submission_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["environmental_data"] = _deserialize_json(result.get("environmental_data"))
        result["social_data"] = _deserialize_json(result.get("social_data"))
        result["governance_data"] = _deserialize_json(result.get("governance_data"))
        result["calculated_metrics"] = _deserialize_json(result.get("calculated_metrics"))
        return result
    finally:
        connection.close()


def save_report(
    report_id: str,
    submission_id: str,
    title: str,
    exec_summary: str,
    env_narrative: str,
    soc_narrative: str,
    gov_narrative: str,
    gri_alignment: dict,
    gap_analysis: list,
    esg_score: float,
) -> None:
    """Insert or update a report record while serializing nested JSON payloads."""
    connection = _get_connection()
    try:
        connection.execute(
            """
            INSERT INTO reports (
                id,
                submission_id,
                title,
                executive_summary,
                environmental_narrative,
                social_narrative,
                governance_narrative,
                gri_alignment,
                gap_analysis,
                esg_score,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'final')
            ON CONFLICT(id) DO UPDATE SET
                submission_id = excluded.submission_id,
                title = excluded.title,
                executive_summary = excluded.executive_summary,
                environmental_narrative = excluded.environmental_narrative,
                social_narrative = excluded.social_narrative,
                governance_narrative = excluded.governance_narrative,
                gri_alignment = excluded.gri_alignment,
                gap_analysis = excluded.gap_analysis,
                esg_score = excluded.esg_score,
                status = excluded.status
            """,
            (
                report_id,
                submission_id,
                title,
                exec_summary,
                env_narrative,
                soc_narrative,
                gov_narrative,
                _serialize_json(gri_alignment),
                _serialize_json(gap_analysis),
                esg_score,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_report_by_submission(submission_id: str) -> Optional[dict]:
    """Fetch a report associated with a submission and deserialize JSON fields."""
    connection = _get_connection()
    try:
        row = connection.execute(
            """
            SELECT
                id,
                submission_id,
                title,
                executive_summary,
                environmental_narrative,
                social_narrative,
                governance_narrative,
                gri_alignment,
                gap_analysis,
                esg_score,
                status,
                created_at
            FROM reports
            WHERE submission_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (submission_id,),
        ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["gri_alignment"] = _deserialize_json(result.get("gri_alignment"))
        result["gap_analysis"] = _deserialize_json(result.get("gap_analysis"))
        return result
    finally:
        connection.close()


def get_all_submissions() -> List[dict]:
    """Return every submission ordered from newest to oldest by update timestamp."""
    connection = _get_connection()
    try:
        rows = connection.execute(
            """
            SELECT
                id,
                company_name,
                facility_location,
                fiscal_year,
                quarter,
                reporting_boundary,
                status,
                created_at,
                updated_at
            FROM submissions
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def add_audit_log(submission_id: str, action: str, details: str = "") -> None:
    """Append an audit event for a given submission."""
    connection = _get_connection()
    try:
        connection.execute(
            """
            INSERT INTO audit_logs (submission_id, action, details)
            VALUES (?, ?, ?)
            """,
            (submission_id, action, details),
        )
        connection.commit()
    finally:
        connection.close()


def get_audit_logs() -> List[dict]:
    """Return all audit log records ordered by timestamp descending."""
    connection = _get_connection()
    try:
        rows = connection.execute(
            """
            SELECT id, submission_id, action, details, timestamp
            FROM audit_logs
            ORDER BY timestamp DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
