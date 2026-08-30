"""
Web Verification Service — Uses DuckDuckGo Instant Answer API
to cross-check reported events against public web data.
Free, no API key required.
"""
import logging
import requests
from urllib.parse import quote

logger = logging.getLogger("hres.webverify")

DDGS_URL = "https://api.duckduckgo.com/"


def web_verify_event(event_type: str, location_address: str | None, lat: float, lon: float) -> dict:
    """
    Search the web for corroboration of a reported event.
    Returns: { corroborated: bool, sources: list, summary: str, confidence_boost: float }
    """
    # Build search query based on event type
    queries = {
        "possible_fire": f"fire incident {location_address or f'{lat:.3f},{lon:.3f}'} today",
        "smoke_report": f"smoke fire report {location_address or f'{lat:.3f},{lon:.3f}'}",
        "heat": f"extreme heat warning {location_address or 'current location'} today",
        "road_block": f"road closure blockage {location_address or f'{lat:.3f},{lon:.3f}'} today",
    }
    query = queries.get(event_type, f"emergency {event_type} {location_address or ''}")

    result = {
        "corroborated": False,
        "sources": [],
        "summary": "No web corroboration found.",
        "query": query,
        "confidence_boost": 0.0,
        "false_alarm_risk": False,
    }

    try:
        params = {
            "q": query,
            "format": "json",
            "no_redirect": "1",
            "no_html": "1",
            "skip_disambig": "1",
        }
        resp = requests.get(DDGS_URL, params=params, timeout=8, headers={"User-Agent": "HRES/1.0"})
        resp.raise_for_status()
        data = resp.json()

        sources = []
        abstract = data.get("Abstract", "").strip()
        abstract_source = data.get("AbstractSource", "")
        abstract_url = data.get("AbstractURL", "")

        if abstract:
            sources.append({"text": abstract[:200], "source": abstract_source, "url": abstract_url})

        # Check related topics
        for topic in data.get("RelatedTopics", [])[:3]:
            if isinstance(topic, dict) and topic.get("Text"):
                sources.append({
                    "text": topic["Text"][:150],
                    "source": "DuckDuckGo",
                    "url": topic.get("FirstURL", ""),
                })

        # Heuristic: if we found relevant abstract or topics, treat as corroborated
        fire_keywords = ["fire", "smoke", "blaze", "flames", "emergency", "heat", "warning"]
        text_blob = " ".join([s["text"] for s in sources]).lower()
        keyword_hits = sum(1 for kw in fire_keywords if kw in text_blob)

        if keyword_hits >= 2:
            result["corroborated"] = True
            result["confidence_boost"] = min(0.25, keyword_hits * 0.05)
            result["summary"] = f"Web search found {len(sources)} related results (keywords: {keyword_hits} matches). Event appears corroborated."
        elif sources:
            result["summary"] = f"Web search returned {len(sources)} results but low keyword relevance."
            result["false_alarm_risk"] = True
        else:
            result["summary"] = "No web evidence found. May be unverified report."
            result["false_alarm_risk"] = True

        result["sources"] = sources[:3]

    except requests.exceptions.Timeout:
        result["summary"] = "Web verification timed out — skipping."
        logger.warning("DuckDuckGo web verify timed out")
    except Exception as e:
        result["summary"] = f"Web verification error: {str(e)}"
        logger.warning(f"Web verify error: {e}")

    return result


def generate_false_alarm_report(
    event_type: str,
    location: str,
    lat: float,
    lon: float,
    reported_at: str,
    web_result: dict,
) -> dict:
    """
    Generate a structured false alarm / misinformation report
    for potential referral to law enforcement.
    """
    return {
        "report_type": "FALSE_ALARM_REPORT",
        "event_type": event_type,
        "location": location,
        "coordinates": {"lat": lat, "lon": lon},
        "reported_at": reported_at,
        "web_verification": web_result,
        "severity": "MEDIUM",
        "estimated_resources_wasted": "2-4 responder-hours, 1 dispatch cycle",
        "recommended_action": "Log for pattern analysis. If repeated: refer to police for investigation under public nuisance / false emergency report statutes.",
        "law_enforcement_note": (
            "Spreading false emergency reports may constitute a criminal offence under applicable law. "
            "This report has been logged with timestamp, location, and originating source data for potential referral."
        ),
        "status": "FILED",
    }
