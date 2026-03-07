from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models


def create_station(db: Session, name: str, city: str, latitude: float, longitude: float) -> models.Station:
    station = models.Station(name=name, city=city, latitude=latitude, longitude=longitude)
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


def list_stations(db: Session) -> list[models.Station]:
    return db.scalars(select(models.Station).order_by(models.Station.id)).all()


def list_stations_paginated(
    db: Session,
    skip: int,
    limit: int,
    city: str | None = None,
) -> list[models.Station]:
    stmt = select(models.Station)
    if city:
        stmt = stmt.where(models.Station.city == city)
    stmt = stmt.order_by(models.Station.id).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_station(db: Session, station_id: int) -> models.Station | None:
    return db.get(models.Station, station_id)


def create_reading(
    db: Session,
    station_id: int,
    pollutant: str,
    value: float,
    timestamp: datetime | None,
) -> models.Reading:
    reading = models.Reading(
        station_id=station_id,
        pollutant=pollutant,
        value=value,
        timestamp=timestamp or datetime.now(timezone.utc),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def latest_pollutant_reading(db: Session, station_id: int, pollutant: str) -> models.Reading | None:
    stmt = (
        select(models.Reading)
        .where(models.Reading.station_id == station_id, models.Reading.pollutant == pollutant)
        .order_by(desc(models.Reading.timestamp))
        .limit(1)
    )
    return db.scalars(stmt).first()


def create_aqi_record(db: Session, station_id: int, aqi: int, category: str) -> models.AQIRecord:
    record = models.AQIRecord(station_id=station_id, aqi=aqi, category=category)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def latest_aqi(db: Session, station_id: int) -> models.AQIRecord | None:
    stmt = (
        select(models.AQIRecord)
        .where(models.AQIRecord.station_id == station_id)
        .order_by(desc(models.AQIRecord.timestamp))
        .limit(1)
    )
    return db.scalars(stmt).first()


def create_alert_rule(
    db: Session,
    pollutant: str,
    threshold: float,
    duration_minutes: int,
    severity: str,
) -> models.AlertRule:
    rule = models.AlertRule(
        pollutant=pollutant,
        threshold=threshold,
        duration_minutes=duration_minutes,
        severity=severity,
        is_enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_alert_rules(db: Session) -> list[models.AlertRule]:
    return db.scalars(select(models.AlertRule).order_by(models.AlertRule.id)).all()


def list_enabled_rules_by_pollutant(db: Session, pollutant: str) -> list[models.AlertRule]:
    stmt = select(models.AlertRule).where(models.AlertRule.pollutant == pollutant, models.AlertRule.is_enabled.is_(True))
    return db.scalars(stmt).all()


def readings_in_window(
    db: Session,
    station_id: int,
    pollutant: str,
    duration_minutes: int,
) -> list[models.Reading]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
    stmt = (
        select(models.Reading)
        .where(
            models.Reading.station_id == station_id,
            models.Reading.pollutant == pollutant,
            models.Reading.timestamp >= cutoff,
        )
        .order_by(models.Reading.timestamp)
    )
    return db.scalars(stmt).all()


def latest_open_alert(db: Session, station_id: int, pollutant: str, severity: str) -> models.Alert | None:
    stmt = (
        select(models.Alert)
        .where(
            models.Alert.station_id == station_id,
            models.Alert.pollutant == pollutant,
            models.Alert.severity == severity,
            models.Alert.status == "open",
        )
        .order_by(desc(models.Alert.started_at))
        .limit(1)
    )
    return db.scalars(stmt).first()


def create_alert(db: Session, station_id: int, pollutant: str, severity: str, message: str) -> models.Alert:
    alert = models.Alert(station_id=station_id, pollutant=pollutant, severity=severity, message=message)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts(db: Session) -> list[models.Alert]:
    return db.scalars(select(models.Alert).order_by(desc(models.Alert.started_at))).all()


def list_alerts_paginated(
    db: Session,
    skip: int,
    limit: int,
    status: str | None = None,
    severity: str | None = None,
    pollutant: str | None = None,
    station_id: int | None = None,
) -> list[models.Alert]:
    stmt = select(models.Alert)
    if status:
        stmt = stmt.where(models.Alert.status == status)
    if severity:
        stmt = stmt.where(models.Alert.severity == severity)
    if pollutant:
        stmt = stmt.where(models.Alert.pollutant == pollutant)
    if station_id is not None:
        stmt = stmt.where(models.Alert.station_id == station_id)
    stmt = stmt.order_by(desc(models.Alert.started_at)).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def acknowledge_alert(db: Session, alert_id: int) -> models.Alert | None:
    alert = db.get(models.Alert, alert_id)
    if not alert:
        return None
    alert.status = "acknowledged"
    alert.ended_at = datetime.now(timezone.utc)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def create_subscriber(db: Session, name: str, channel: str, destination: str) -> models.NotificationSubscriber:
    subscriber = models.NotificationSubscriber(name=name, channel=channel, destination=destination, is_active=True)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


def get_subscriber_by_channel_and_destination(
    db: Session,
    channel: str,
    destination: str,
) -> models.NotificationSubscriber | None:
    normalized_destination = destination.lower() if channel == "email" else destination
    stmt = select(models.NotificationSubscriber).where(models.NotificationSubscriber.channel == channel)

    for item in db.scalars(stmt):
        item_destination = item.destination.lower() if channel == "email" else item.destination
        if item_destination == normalized_destination:
            return item
    return None


def list_subscribers(db: Session) -> list[models.NotificationSubscriber]:
    return db.scalars(select(models.NotificationSubscriber).order_by(models.NotificationSubscriber.id)).all()


def list_subscribers_paginated(
    db: Session,
    skip: int,
    limit: int,
    channel: str | None = None,
    is_active: bool | None = None,
) -> list[models.NotificationSubscriber]:
    stmt = select(models.NotificationSubscriber)
    if channel:
        stmt = stmt.where(models.NotificationSubscriber.channel == channel)
    if is_active is not None:
        stmt = stmt.where(models.NotificationSubscriber.is_active.is_(is_active))
    stmt = stmt.order_by(models.NotificationSubscriber.id).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def list_active_subscribers(db: Session, channel: str | None = None) -> list[models.NotificationSubscriber]:
    stmt = select(models.NotificationSubscriber).where(models.NotificationSubscriber.is_active.is_(True))
    if channel:
        stmt = stmt.where(models.NotificationSubscriber.channel == channel)
    return db.scalars(stmt.order_by(models.NotificationSubscriber.id)).all()


def create_notification_log(
    db: Session,
    alert_id: int,
    channel: str,
    destination: str,
    delivery_status: str,
    provider_message_id: str | None,
    error_message: str | None,
) -> models.NotificationLog:
    log = models.NotificationLog(
        alert_id=alert_id,
        channel=channel,
        destination=destination,
        delivery_status=delivery_status,
        provider_message_id=provider_message_id,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def open_alerts(db: Session) -> list[models.Alert]:
    stmt = select(models.Alert).where(models.Alert.status == "open").order_by(desc(models.Alert.started_at))
    return db.scalars(stmt).all()


def latest_station_summary(db: Session, station_id: int) -> dict[str, int | float | str | None]:
    latest_aqi_record = latest_aqi(db, station_id)
    latest_pm25_record = latest_pollutant_reading(db, station_id, "PM2.5")
    latest_pm10_record = latest_pollutant_reading(db, station_id, "PM10")

    return {
        "latest_aqi": latest_aqi_record.aqi if latest_aqi_record else None,
        "latest_category": latest_aqi_record.category if latest_aqi_record else None,
        "latest_pm25": latest_pm25_record.value if latest_pm25_record else None,
        "latest_pm10": latest_pm10_record.value if latest_pm10_record else None,
        "latest_reading_at": max(
            [
                item.timestamp
                for item in (latest_pm25_record, latest_pm10_record)
                if item is not None
            ],
            default=None,
        ),
    }


def recent_readings(db: Session, station_id: int, limit: int = 30) -> list[models.Reading]:
    stmt = (
        select(models.Reading)
        .where(models.Reading.station_id == station_id)
        .order_by(desc(models.Reading.timestamp))
        .limit(limit)
    )
    return db.scalars(stmt).all()


def dashboard_station_alert_counts(db: Session) -> dict[int, dict[str, int | str | None]]:
    counts: dict[int, dict[str, int | str | None]] = {}
    severity_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    for alert in open_alerts(db):
        current = counts.setdefault(alert.station_id, {"open_alert_count": 0, "dominant_severity": None})
        current["open_alert_count"] = int(current["open_alert_count"]) + 1

        dominant_severity = current["dominant_severity"]
        if dominant_severity is None or severity_rank.get(alert.severity, 0) > severity_rank.get(str(dominant_severity), 0):
            current["dominant_severity"] = alert.severity

    return counts


def dashboard_overview(db: Session) -> dict[str, int | float | str | datetime | None]:
    stations = list_stations(db)
    active_alert_items = open_alerts(db)
    active_subscribers = list_active_subscribers(db)
    aqi_records = [latest_aqi(db, station.id) for station in stations]
    available_aqis = [record.aqi for record in aqi_records if record is not None]

    worst_station_name = None
    max_aqi = max(available_aqis) if available_aqis else None
    if max_aqi is not None:
        for station, record in zip(stations, aqi_records, strict=False):
            if record and record.aqi == max_aqi:
                worst_station_name = station.name
                break

    return {
        "total_stations": len(stations),
        "active_stations": sum(1 for station in stations if station.is_active),
        "city_count": len({station.city for station in stations}),
        "total_subscribers": len(active_subscribers),
        "open_alerts": len(active_alert_items),
        "critical_alerts": sum(1 for alert in active_alert_items if alert.severity == "critical"),
        "average_aqi": round(sum(available_aqis) / len(available_aqis), 1) if available_aqis else None,
        "max_aqi": max_aqi,
        "worst_station_name": worst_station_name,
        "last_updated": datetime.now(timezone.utc),
    }


def dashboard_city_summaries(db: Session) -> list[dict[str, int | float | str | None]]:
    stations = list_stations(db)
    open_alert_items = open_alerts(db)
    alert_count_by_station: dict[int, int] = {}
    for alert in open_alert_items:
        alert_count_by_station[alert.station_id] = alert_count_by_station.get(alert.station_id, 0) + 1

    grouped: dict[str, dict[str, list[int] | int]] = {}
    for station in stations:
        city_summary = grouped.setdefault(station.city, {"aqis": [], "station_count": 0, "open_alerts": 0})
        city_summary["station_count"] = int(city_summary["station_count"]) + 1
        city_summary["open_alerts"] = int(city_summary["open_alerts"]) + alert_count_by_station.get(station.id, 0)

        latest_record = latest_aqi(db, station.id)
        if latest_record is not None:
            city_summary["aqis"].append(latest_record.aqi)

    results: list[dict[str, int | float | str | None]] = []
    for city, values in grouped.items():
        aqis = values["aqis"]
        average_aqi = round(sum(aqis) / len(aqis), 1) if aqis else None
        results.append(
            {
                "city": city,
                "station_count": int(values["station_count"]),
                "average_aqi": average_aqi,
                "open_alerts": int(values["open_alerts"]),
            }
        )

    return sorted(results, key=lambda item: (-int(item["open_alerts"]), str(item["city"])))


def dashboard_pollutant_snapshot(db: Session) -> list[dict[str, float | str | None]]:
    pollutants = ["PM2.5", "PM10"]
    stations = list_stations(db)
    snapshot: list[dict[str, float | str | None]] = []

    for pollutant in pollutants:
        values: list[float] = []
        for station in stations:
            latest_reading_record = latest_pollutant_reading(db, station.id, pollutant)
            if latest_reading_record is not None:
                values.append(latest_reading_record.value)

        snapshot.append(
            {
                "label": pollutant,
                "average_value": round(sum(values) / len(values), 1) if values else None,
                "peak_value": round(max(values), 1) if values else None,
            }
        )

    return snapshot
