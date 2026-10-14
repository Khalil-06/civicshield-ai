from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IncidentReport(BaseModel):
    description: str
    location: str
    reporter_name: Optional[str] = "Anonymous"
    category: Optional[str] = None


class AIAnalysis(BaseModel):
    incident_type: str
    severity: str
    risk_level: str
    summary: str
    priority_score: int
    reason: str
    recommended_actions: List[str]
    vulnerable_population_risk: str


class FusionResult(BaseModel):
    relationship: str           # "same_incident" | "likely_related" | "unrelated"
    confidence: float
    reason: str


class Incident(BaseModel):
    id: str
    description: str
    location: str
    reporter_name: str
    category: Optional[str]
    analysis: Optional[dict]
    fused_with: Optional[str] = None   # id of the parent unified incident
    timestamp: str
    is_unified: bool = False
    supporting_reports: List[str] = []  # ids of fused sub-reports
    fusion_confidence: Optional[float] = None
    fusion_reason: Optional[str] = None


class IncidentReportResponse(BaseModel):
    status: str
    incident_id: str
    analysis: dict
    fusion: Optional[dict] = None
    unified_incident_id: Optional[str] = None


class DashboardStats(BaseModel):
    active_incidents: int
    critical: int
    high_priority: int
    reports_received: int
    fused_reports: int
