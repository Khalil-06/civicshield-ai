"""
incident_fusion.py — Detects whether a new incident is related to existing ones
and groups them into a unified incident using Gemini (with local fallback).
"""
import json
import re
from typing import Optional
from backend.ai_engine import _client, _gemini_available

FUSION_PROMPT = """You are CivicShield AI Incident Fusion Engine.

Your job is to determine if a NEW citizen report describes the SAME real-world emergency as an EXISTING incident.

EXISTING INCIDENT:
Description: {existing_desc}
Location: {existing_loc}
Incident Type: {existing_type}

NEW REPORT:
Description: {new_desc}
Location: {new_loc}

Evaluate:
1. Are these describing the same event? (same physical location, same type of emergency)
2. Could they be related but from different perspectives?
3. Are they clearly different incidents?

Return ONLY valid JSON — no markdown:
{{
    "relationship": "same_incident|likely_related|unrelated",
    "confidence": <float 0.0-1.0>,
    "reason": "brief human-readable explanation of why these are or aren't the same incident"
}}

Be conservative: only fuse when confidence >= 0.65.
"same_incident" means very likely the same event (confidence >= 0.80).
"likely_related" means possibly connected (confidence 0.65-0.79).
"unrelated" means different events.
"""


def _local_fusion_check(existing: dict, new_desc: str, new_loc: str) -> dict:
    """
    Simple keyword + location heuristic fusion when Gemini is unavailable.
    """
    existing_desc = (existing.get("description") or "").lower()
    existing_loc = (existing.get("location") or "").lower()
    existing_type = ""
    if existing.get("analysis"):
        existing_type = (existing["analysis"].get("incident_type") or "").lower()

    new_desc_l = new_desc.lower()
    new_loc_l = new_loc.lower()

    # Location similarity: share at least one significant word
    existing_loc_words = set(w for w in re.split(r"\W+", existing_loc) if len(w) > 3)
    new_loc_words = set(w for w in re.split(r"\W+", new_loc_l) if len(w) > 3)
    location_overlap = existing_loc_words & new_loc_words

    # Keyword sets per type
    fire_kw = {"fire", "smoke", "flame", "burn", "evacuat", "blaze"}
    flood_kw = {"flood", "water", "rain", "overflow"}
    medical_kw = {"medical", "injured", "ambulance", "hospital", "hurt", "collapse"}
    accident_kw = {"accident", "crash", "collision", "vehicle"}

    def type_match(a: str, b: str) -> bool:
        for kws in [fire_kw, flood_kw, medical_kw, accident_kw]:
            if any(k in a for k in kws) and any(k in b for k in kws):
                return True
        return False

    same_type = type_match(existing_desc + " " + existing_type, new_desc_l)

    if location_overlap and same_type:
        confidence = 0.82
        relationship = "same_incident"
        reason = (
            f"Both reports mention similar location keywords ({', '.join(list(location_overlap)[:3])}) "
            f"and describe the same type of emergency ({existing_type or 'inferred'})."
        )
    elif location_overlap or same_type:
        confidence = 0.68
        relationship = "likely_related"
        reason = (
            "Reports share either a similar location or similar incident type but not both. "
            "Possible connection — human verification recommended."
        )
    else:
        confidence = 0.15
        relationship = "unrelated"
        reason = "No significant location or incident-type overlap detected."

    return {"relationship": relationship, "confidence": confidence, "reason": reason}


def check_fusion(existing_incident: dict, new_description: str, new_location: str) -> dict:
    """
    Returns a fusion result dict: { relationship, confidence, reason }
    """
    if not _gemini_available or not _client:
        return _local_fusion_check(existing_incident, new_description, new_location)

    try:
        existing_analysis = existing_incident.get("analysis") or {}
        prompt = FUSION_PROMPT.format(
            existing_desc=existing_incident.get("description", ""),
            existing_loc=existing_incident.get("location", ""),
            existing_type=existing_analysis.get("incident_type", "Unknown"),
            new_desc=new_description,
            new_loc=new_location,
        )
        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)
        result["confidence"] = float(result.get("confidence", 0.0))
        return result

    except Exception as e:
        print(f"[incident_fusion] Gemini error: {e}. Using local fallback.")
        return _local_fusion_check(existing_incident, new_description, new_location)


def find_best_fusion_match(existing_incidents: list, new_description: str, new_location: str) -> Optional[dict]:
    """
    Search all top-level unified/unfused incidents for the best fusion match.
    Returns: { "incident": <incident_dict>, "fusion": <fusion_result> } or None
    """
    best_match = None
    best_confidence = 0.64  # minimum threshold

    for incident in existing_incidents:
        # Only try to fuse against top-level incidents (not already fused sub-reports)
        if incident.get("fused_with"):
            continue

        fusion = check_fusion(incident, new_description, new_location)

        if fusion["relationship"] in ("same_incident", "likely_related"):
            if fusion["confidence"] > best_confidence:
                best_confidence = fusion["confidence"]
                best_match = {"incident": incident, "fusion": fusion}

    return best_match
