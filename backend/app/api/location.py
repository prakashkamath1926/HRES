from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from backend.app.core.schemas import LocationContext, IncidentState
from backend.app.core.config import settings
from backend.app.services.monitoring import get_or_create_active_incident, process_incident_updates
from backend.app.repositories.audit_log import add_audit_event
from backend.app.services.fortyguard_service import run_fortyguard_live_ingest
from backend.app.services.openmeteo_service import run_openmeteo_ingest

router = APIRouter(prefix="/location", tags=["location"])


class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    address: str | None = None
    source: str = "user"


@router.post("", response_model=IncidentState)
def set_monitored_location(payload: LocationRequest, background_tasks: BackgroundTasks):
    try:
        incident = get_or_create_active_incident()

        add_audit_event(
            incident.incident_id,
            "LOCATION_UPDATED",
            f"Monitored location updated: {payload.address or 'Custom Coordinates'} ({payload.latitude:.5f}, {payload.longitude:.5f})",
            {
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "address": payload.address,
                "source": payload.source
            }
        )

        # Always fetch Open-Meteo (free, no key)
        background_tasks.add_task(
            run_openmeteo_ingest,
            incident.incident_id,
            payload.latitude,
            payload.longitude,
            payload.address,
            True  # trigger_process=True (will also run after FortyGuard below)
        )

        # Fetch FortyGuard live if API key is configured
        api_key = settings.FORTYGUARD_API_KEY
        if api_key:
            background_tasks.add_task(
                run_fortyguard_live_ingest,
                incident.incident_id,
                api_key,
                payload.latitude,
                payload.longitude,
                payload.address
            )

        # Return current state immediately — background tasks update asynchronously
        from backend.app.repositories.incidents import get_incident_state
        return get_incident_state(incident.incident_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
