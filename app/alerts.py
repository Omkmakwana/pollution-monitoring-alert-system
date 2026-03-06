from sqlalchemy.orm import Session

from app import crud, models
from app.notifications import notify_subscribers_for_alert


def evaluate_alerts_for_reading(db: Session, reading: models.Reading) -> list[models.Alert]:
    rules = crud.list_enabled_rules_by_pollutant(db, reading.pollutant)
    created_alerts: list[models.Alert] = []

    for rule in rules:
        window_readings = crud.readings_in_window(
            db=db,
            station_id=reading.station_id,
            pollutant=reading.pollutant,
            duration_minutes=rule.duration_minutes,
        )
        if not window_readings:
            continue

        threshold_breached = all(item.value >= rule.threshold for item in window_readings)
        if not threshold_breached:
            continue

        existing = crud.latest_open_alert(
            db=db,
            station_id=reading.station_id,
            pollutant=reading.pollutant,
            severity=rule.severity,
        )
        if existing:
            continue

        message = (
            f"{reading.pollutant} threshold exceeded at station {reading.station_id}. "
            f"Threshold: {rule.threshold}, Duration: {rule.duration_minutes} min."
        )
        new_alert = crud.create_alert(
                db=db,
                station_id=reading.station_id,
                pollutant=reading.pollutant,
                severity=rule.severity,
                message=message,
            )
        created_alerts.append(new_alert)
        notify_subscribers_for_alert(db, new_alert)

    return created_alerts
