"""
main.py — CivicShield AI FastAPI backend
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models import IncidentReport
from backend.ai_engine import analyze_incident
from backend.incident_fusion import find_best_fusion_match
from backend.database import (
    init_db,
    save_incident,
    load_all_incidents,
    get_incident,
    update_incident,
    clear_all_incidents,
    get_dashboard_stats,
)

# ── App init ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="CivicShield AI",
    description="AI-powered Community Emergency Intelligence Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


# ── Demo scenario data ────────────────────────────────────────────────────────

DEMO_REPORTS = [
    {
        "description": "Large amount of smoke rising near Government School. The smoke is very thick and people nearby are covering their faces.",
        "location": "Government School, Zone A",
        "reporter_name": "Priya Sharma",
        "category": "Fire",
    },
    {
        "description": "Possible fire behind the school building in Zone A. I can see flames through the fence.",
        "location": "Zone A School Campus",
        "reporter_name": "Rahul Mehta",
        "category": "Fire",
    },
    {
        "description": "Students are being moved away from the school area due to smoke coming from the back of the building.",
        "location": "Government School, Zone A",
        "reporter_name": "Fatima Khan",
        "category": "Fire",
    },
    {
        "description": "People are reporting heavy smoke near the Zone A school. Emergency vehicles should be sent immediately.",
        "location": "Zone A, near school",
        "reporter_name": "Anonymous",
        "category": "Fire",
    },
    {
        "description": "Traffic is slowing down significantly on the main road due to emergency activity near Zone A. Lots of people standing on the road watching.",
        "location": "Main Road, Zone A junction",
        "reporter_name": "Kiran Patel",
        "category": "Road Accident",
    },
]


# ── Helper ────────────────────────────────────────────────────────────────────

def _build_incident_dict(report: IncidentReport, analysis: dict, report_id: str) -> dict:
    return {
        "id": report_id,
        "description": report.description,
        "location": report.location,
        "reporter_name": report.reporter_name or "Anonymous",
        "category": report.category,
        "analysis": analysis,
        "fused_with": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "is_unified": False,
        "supporting_reports": [],
        "fusion_confidence": None,
        "fusion_reason": None,
    }


def _promote_to_unified(incident: dict) -> dict:
    """Mark an existing incident as a unified (parent) incident."""
    incident["is_unified"] = True
    return incident


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {
        "project": "CivicShield AI",
        "version": "2.0.0",
        "status": "online",
        "message": "Community Emergency Intelligence Platform",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}


@app.post("/incidents/analyze")
def analyze_only(report: IncidentReport):
    """
    Analyze a report with AI but do NOT save it to the database.
    Used for quick preview on the report form.
    """
    analysis = analyze_incident(report.description, report.location)
    return {
        "status": "analyzed",
        "analysis": analysis,
        "disclaimer": "AI-generated recommendation — human verification required.",
    }


@app.post("/incidents")
def submit_incident(report: IncidentReport):
    """
    Submit a new citizen report:
    1. AI analysis
    2. Fusion check against existing incidents
    3. Save (as sub-report if fused, otherwise as new incident)
    """
    report_id = str(uuid.uuid4())
    analysis = analyze_incident(report.description, report.location)
    new_incident = _build_incident_dict(report, analysis, report_id)

    existing = load_all_incidents()
    # Only attempt fusion against top-level incidents
    top_level = [i for i in existing if not i.get("fused_with")]

    fusion_result = None
    unified_incident_id = None

    if top_level:
        match = find_best_fusion_match(top_level, report.description, report.location)
        if match:
            fusion_result = match["fusion"]
            parent = match["incident"]

            # Mark the new report as fused
            new_incident["fused_with"] = parent["id"]
            new_incident["fusion_confidence"] = fusion_result["confidence"]
            new_incident["fusion_reason"] = fusion_result["reason"]

            # Update the parent incident's supporting list
            supporting = parent.get("supporting_reports", [])
            supporting.append(report_id)
            parent["supporting_reports"] = supporting
            parent["is_unified"] = True

            # Recalculate priority: bump score if many reports corroborate
            count = len(supporting) + 1  # +1 for parent itself
            if parent.get("analysis"):
                base_score = parent["analysis"].get("priority_score", 50)
                # Each additional corroborating report adds up to 2 points (capped at 100)
                boost = min(10, (count - 1) * 2)
                parent["analysis"]["priority_score"] = min(100, base_score + boost)
                parent["analysis"]["corroborating_reports"] = count

            update_incident(parent["id"], parent)
            unified_incident_id = parent["id"]

    save_incident(new_incident)

    return {
        "status": "received",
        "incident_id": report_id,
        "analysis": analysis,
        "fusion": fusion_result,
        "unified_incident_id": unified_incident_id,
        "disclaimer": "AI-generated recommendation — human verification required.",
    }


@app.get("/incidents")
def list_incidents():
    """Return all incidents ordered by priority (highest first)."""
    incidents = load_all_incidents()
    # Sort: unified incidents first, then by priority score
    def sort_key(i):
        score = 0
        if i.get("analysis"):
            score = i["analysis"].get("priority_score", 0)
        return (0 if not i.get("fused_with") else 1, -score)

    incidents.sort(key=sort_key)
    return {"incidents": incidents}


@app.get("/incidents/{incident_id}")
def get_incident_by_id(incident_id: str):
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/dashboard/stats")
def dashboard_stats():
    return get_dashboard_stats()


@app.post("/demo/load")
def load_demo():
    """
    Load the pre-built demo emergency scenario.
    Clears existing incidents first, then processes all demo reports
    through the full analysis + fusion pipeline.
    """
    clear_all_incidents()

    results = []
    for report_data in DEMO_REPORTS:
        report = IncidentReport(**report_data)
        result = submit_incident(report)
        results.append(result)

    stats = get_dashboard_stats()
    return {
        "status": "demo_loaded",
        "reports_processed": len(results),
        "stats": stats,
        "results": results,
    }


@app.delete("/incidents/reset")
def reset_incidents():
    """Clear all incidents (admin/demo use)."""
    clear_all_incidents()
    return {"status": "cleared", "message": "All incidents have been removed."}