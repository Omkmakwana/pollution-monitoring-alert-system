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
    }


def recent_readings(db: Session, station_id: int, limit: int = 30) -> list[models.Reading]:
    stmt = (
        select(models.Reading)
        .where(models.Reading.station_id == station_id)
        .order_by(desc(models.Reading.timestamp))
        .limit(limit)
    )
    return db.scalars(stmt).all()
