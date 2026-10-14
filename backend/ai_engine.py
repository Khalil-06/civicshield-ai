"""
ai_engine.py — Gemini-powered incident analysis with local fallback.
"""
import os
import json
import random
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Try to initialise the Gemini client
_client = None
_gemini_available = False

try:
    from google import genai
    if GEMINI_API_KEY:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        _gemini_available = True
except Exception:
    _gemini_available = False


# ── Fallback data ──────────────────────────────────────────────────────────────

FALLBACK_ANALYSES = {
    "fire": {
        "incident_type": "Fire",
        "severity": "Critical",
        "risk_level": "High",
        "summary": "Possible fire incident detected near the reported location. Smoke or flames reported by citizen.",
        "priority_score": 92,
        "reason": "High priority: fire incidents near populated or vulnerable areas require immediate response to prevent injury and property loss.",
        "recommended_actions": [
            "Alert fire department immediately",
            "Evacuate people within the affected radius",
            "Keep bystanders at a safe distance",
            "Coordinate with medical services for potential casualties",
        ],
        "vulnerable_population_risk": "High",
    },
    "medical": {
        "incident_type": "Medical Emergency",
        "severity": "High",
        "risk_level": "High",
        "summary": "Medical emergency reported. Immediate medical attention may be required.",
        "priority_score": 85,
        "reason": "Medical emergencies can deteriorate rapidly. Fast response reduces mortality risk.",
        "recommended_actions": [
            "Dispatch emergency medical services",
            "Clear the immediate area",
            "Provide first aid if trained personnel are present",
        ],
        "vulnerable_population_risk": "High",
    },
    "flood": {
        "incident_type": "Flood",
        "severity": "High",
        "risk_level": "High",
        "summary": "Flooding reported in the area. Water levels may be rising.",
        "priority_score": 80,
        "reason": "Flooding can block evacuation routes and endanger lives rapidly.",
        "recommended_actions": [
            "Warn residents in the flood zone",
            "Deploy water-rescue teams if needed",
            "Redirect traffic from flooded roads",
            "Open emergency shelters",
        ],
        "vulnerable_population_risk": "Medium",
    },
    "accident": {
        "incident_type": "Road Accident",
        "severity": "High",
        "risk_level": "Medium",
        "summary": "Road accident reported. Injuries and traffic disruption likely.",
        "priority_score": 75,
        "reason": "Road accidents can involve multiple casualties and require ambulance and traffic management.",
        "recommended_actions": [
            "Dispatch ambulance to the scene",
            "Alert traffic police",
            "Set up diversion routes",
            "Secure the accident scene",
        ],
        "vulnerable_population_risk": "Medium",
    },
    "default": {
        "incident_type": "Public Safety Incident",
        "severity": "Medium",
        "risk_level": "Medium",
        "summary": "Citizen report flagged for review. Situation requires assessment by responders.",
        "priority_score": 65,
        "reason": "Moderate priority assigned pending further verification by human responders.",
        "recommended_actions": [
            "Review report and verify with additional sources",
            "Dispatch patrol to assess the situation",
            "Monitor for escalation",
        ],
        "vulnerable_population_risk": "Low",
    },
}


def _fallback_analysis(description: str, location: str) -> dict:
    """Return a plausible local analysis when Gemini is unavailable."""
    desc_lower = description.lower()
    if any(w in desc_lower for w in ["fire", "smoke", "flame", "burn"]):
        result = dict(FALLBACK_ANALYSES["fire"])
    elif any(w in desc_lower for w in ["medical", "injury", "hurt", "unconscious", "collapse", "ambulance"]):
        result = dict(FALLBACK_ANALYSES["medical"])
    elif any(w in desc_lower for w in ["flood", "water", "rain", "inundat"]):
        result = dict(FALLBACK_ANALYSES["flood"])
    elif any(w in desc_lower for w in ["accident", "crash", "collision", "vehicle"]):
        result = dict(FALLBACK_ANALYSES["accident"])
    else:
        result = dict(FALLBACK_ANALYSES["default"])

    # Add slight variation so repeated demo submissions look realistic
    result["priority_score"] = min(100, result["priority_score"] + random.randint(-3, 3))
    result["summary"] = f"{result['summary']} Location: {location}."
    result["_fallback"] = True
    return result


# ── Main analysis function ─────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are CivicShield AI, a civic emergency intelligence assistant.

Analyze this citizen emergency report and return ONLY valid JSON — no markdown, no explanation.

Citizen report:
{description}

Location:
{location}

Required JSON format:
{{
    "incident_type": "Fire|Medical Emergency|Road Accident|Flood|Crime|Infrastructure Failure|Environmental Hazard|Other",
    "severity": "Low|Medium|High|Critical",
    "risk_level": "Low|Medium|High",
    "summary": "A concise 1-2 sentence summary of what is happening",
    "priority_score": <integer 0-100>,
    "reason": "Human-readable explanation of why this priority score was assigned",
    "recommended_actions": ["action 1", "action 2", "action 3"],
    "vulnerable_population_risk": "None|Low|Medium|High"
}}

Rules:
- priority_score must be an integer between 0 and 100
- Do not fabricate confirmed facts beyond what is reported
- These are decision-support recommendations for human responders, NOT autonomous emergency decisions
- If the report mentions schools, hospitals, or elderly/child areas, increase vulnerable_population_risk
"""


def analyze_incident(description: str, location: str) -> dict:
    """
    Run Gemini analysis on a citizen report.
    Falls back to local heuristics if Gemini is unavailable.
    """
    if not _gemini_available or not _client:
        return _fallback_analysis(description, location)

    try:
        prompt = ANALYSIS_PROMPT.format(description=description, location=location)
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)

        # Ensure priority_score is int
        result["priority_score"] = int(result.get("priority_score", 50))
        result["_fallback"] = False
        return result

    except Exception as e:
        print(f"[ai_engine] Gemini error: {e}. Using fallback.")
        result = _fallback_analysis(description, location)
        result["_fallback"] = True
        return result