from fastapi import APIRouter, HTTPException
from backend.app.core.schemas import IncidentState
from backend.app.services.simulation import run_simulation_scenario
from backend.app.services.monitoring import reset_active_incident

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/{scenario}", response_model=IncidentState)
def trigger_simulation(scenario: str):
    try:
        # Reset the scenario
        if scenario == "reset":
            reset_active_incident()
            from backend.app.services.monitoring import get_or_create_active_incident
            return get_or_create_active_incident()

        # Run specific scenario injection
        state = run_simulation_scenario(scenario)
        return state
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
