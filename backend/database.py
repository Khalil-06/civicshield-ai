"""
database.py — In-memory SQLite-backed store for incidents.
Uses a simple dict as the runtime store; persists to SQLite on write.
"""
import sqlite3
import json
import os
from typing import Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "civicshield.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            reporter_name TEXT DEFAULT 'Anonymous',
            category TEXT,
            analysis TEXT,
            fused_with TEXT,
            timestamp TEXT,
            is_unified INTEGER DEFAULT 0,
            supporting_reports TEXT DEFAULT '[]',
            fusion_confidence REAL,
            fusion_reason TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_incident(incident: dict):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO incidents
        (id, description, location, reporter_name, category, analysis,
         fused_with, timestamp, is_unified, supporting_reports, fusion_confidence, fusion_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident["id"],
        incident["description"],
        incident["location"],
        incident.get("reporter_name", "Anonymous"),
        incident.get("category"),
        json.dumps(incident.get("analysis")),
        incident.get("fused_with"),
        incident["timestamp"],
        1 if incident.get("is_unified") else 0,
        json.dumps(incident.get("supporting_reports", [])),
        incident.get("fusion_confidence"),
        incident.get("fusion_reason"),
    ))
    conn.commit()
    conn.close()


def load_all_incidents() -> List[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM incidents ORDER BY timestamp DESC").fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["analysis"] = json.loads(d["analysis"]) if d["analysis"] else None
        d["supporting_reports"] = json.loads(d["supporting_reports"]) if d["supporting_reports"] else []
        d["is_unified"] = bool(d["is_unified"])
        result.append(d)
    return result


def get_incident(incident_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["analysis"] = json.loads(d["analysis"]) if d["analysis"] else None
    d["supporting_reports"] = json.loads(d["supporting_reports"]) if d["supporting_reports"] else []
    d["is_unified"] = bool(d["is_unified"])
    return d


def update_incident(incident_id: str, updates: dict):
    incident = get_incident(incident_id)
    if not incident:
        return
    incident.update(updates)
    save_incident(incident)


def clear_all_incidents():
    conn = get_connection()
    conn.execute("DELETE FROM incidents")
    conn.commit()
    conn.close()


def get_dashboard_stats() -> dict:
    incidents = load_all_incidents()
    # Only count visible incidents (unified or unfused)
    visible = [i for i in incidents if not i.get("fused_with")]
    critical = sum(
        1 for i in visible
        if i.get("analysis") and i["analysis"].get("severity", "").lower() == "critical"
    )
    high = sum(
        1 for i in visible
        if i.get("analysis") and i["analysis"].get("priority_score", 0) >= 70
    )
    fused = sum(1 for i in incidents if i.get("fused_with"))
    return {
        "active_incidents": len(visible),
        "critical": critical,
        "high_priority": high,
        "reports_received": len(incidents),
        "fused_reports": fused,
    }
