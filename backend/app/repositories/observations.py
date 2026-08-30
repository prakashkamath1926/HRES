import json
from datetime import datetime
from backend.app.core.schemas import (
    Observation, NormalizedEvent, LocationContext, DataMode, EventType
)
from backend.app.repositories.database import get_db_connection, execute_query


def add_observation(incident_id: str, obs: Observation):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    value_json = json.dumps(obs.value)
    raw_payload_json = json.dumps(obs.raw_payload) if obs.raw_payload else None

    execute_query(cursor,
        """
        INSERT OR REPLACE INTO observations (
            observation_id, incident_id, source, data_mode, event_type,
            latitude, longitude, address, location_source, location_timestamp,
            observed_at, received_at, value, confidence, raw_payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            obs.observation_id,
            incident_id,
            obs.source,
            obs.data_mode.value,
            obs.event_type.value,
            obs.location.latitude,
            obs.location.longitude,
            obs.location.address,
            obs.location.source,
            obs.location.timestamp,
            obs.observed_at,
            obs.received_at,
            value_json,
            obs.confidence,
            raw_payload_json
        ),
        dialect=dialect
    )
    conn.commit()
    conn.close()


def get_observations_for_incident(incident_id: str) -> list[Observation]:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor,
        """
        SELECT 
            observation_id, source, data_mode, event_type,
            latitude, longitude, address, location_source, location_timestamp,
            observed_at, received_at, value, confidence, raw_payload
        FROM observations
        WHERE incident_id = ?
        ORDER BY observed_at ASC, received_at ASC, observation_id ASC
        """,
        (incident_id,),
        dialect=dialect
    )
    rows = cursor.fetchall()
    conn.close()

    observations = []
    for r in rows:
        loc = LocationContext(
            latitude=r["latitude"],
            longitude=r["longitude"],
            address=r["address"],
            source=r["location_source"],
            timestamp=datetime.fromisoformat(r["location_timestamp"]) if isinstance(r["location_timestamp"], str) else r["location_timestamp"]
        )
        observations.append(
            Observation(
                observation_id=r["observation_id"],
                source=r["source"],
                data_mode=DataMode(r["data_mode"]),
                event_type=EventType(r["event_type"]),
                location=loc,
                observed_at=datetime.fromisoformat(r["observed_at"]) if isinstance(r["observed_at"], str) else r["observed_at"],
                received_at=datetime.fromisoformat(r["received_at"]) if isinstance(r["received_at"], str) else r["received_at"],
                value=json.loads(r["value"]),
                confidence=r["confidence"],
                raw_payload=json.loads(r["raw_payload"]) if r["raw_payload"] else None
            )
        )
    return observations


def add_normalized_event(incident_id: str, event: NormalizedEvent):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    value_json = json.dumps(event.value)
    supporting_obs_json = json.dumps(event.supporting_observations)
    web_verify_json = json.dumps(event.web_verification) if event.web_verification else None
    false_alarm_json = json.dumps(event.false_alarm_report) if event.false_alarm_report else None

    execute_query(cursor,
        """
        INSERT OR REPLACE INTO normalized_events (
            event_id, incident_id, event_type,
            latitude, longitude, address, location_source, location_timestamp,
            status, confidence, value, supporting_observations,
            web_verification, false_alarm_report
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.event_id, incident_id, event.event_type.value,
            event.location.latitude, event.location.longitude,
            event.location.address, event.location.source, event.location.timestamp,
            event.status, event.confidence, value_json, supporting_obs_json,
            web_verify_json, false_alarm_json
        ),
        dialect=dialect
    )
    conn.commit()
    conn.close()


def get_normalized_events_for_incident(incident_id: str) -> list[NormalizedEvent]:
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor,
        """
        SELECT
            event_id, event_type,
            latitude, longitude, address, location_source, location_timestamp,
            status, confidence, value, supporting_observations,
            web_verification, false_alarm_report
        FROM normalized_events
        WHERE incident_id = ?
        """,
        (incident_id,),
        dialect=dialect
    )
    rows = cursor.fetchall()
    conn.close()

    events = []
    for r in rows:
        loc = LocationContext(
            latitude=r["latitude"], longitude=r["longitude"],
            address=r["address"], source=r["location_source"],
            timestamp=datetime.fromisoformat(r["location_timestamp"]) if isinstance(r["location_timestamp"], str) else r["location_timestamp"]
        )
        # Safely handle columns that may be missing in older DB snapshots
        try:
            web_ver = json.loads(r["web_verification"]) if r["web_verification"] else None
        except (KeyError, IndexError, TypeError):
            web_ver = None
        try:
            false_alarm = json.loads(r["false_alarm_report"]) if r["false_alarm_report"] else None
        except (KeyError, IndexError, TypeError):
            false_alarm = None

        events.append(
            NormalizedEvent(
                event_id=r["event_id"],
                event_type=EventType(r["event_type"]),
                location=loc,
                status=r["status"],
                confidence=r["confidence"],
                value=json.loads(r["value"]),
                supporting_observations=json.loads(r["supporting_observations"]),
                web_verification=web_ver,
                false_alarm_report=false_alarm
            )
        )
    return events


def clear_normalized_events(incident_id: str):
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor,
        "DELETE FROM normalized_events WHERE incident_id = ?",
        (incident_id,),
        dialect=dialect
    )
    conn.commit()
    conn.close()
