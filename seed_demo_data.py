from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from app.aqi import calculate_aqi
from app.database import Base, SessionLocal, engine
from app.models import AQIRecord, Alert, AlertRule, NotificationSubscriber, Reading, Station


DEMO_STATIONS = [
    {"name": "PMAS Demo | Marine Drive", "city": "Mumbai", "latitude": 18.943, "longitude": 72.823},
    {"name": "PMAS Demo | Bandra Link", "city": "Mumbai", "latitude": 19.059, "longitude": 72.829},
    {"name": "PMAS Demo | Connaught Place", "city": "Delhi", "latitude": 28.631, "longitude": 77.216},
    {"name": "PMAS Demo | Lodhi Corridor", "city": "Delhi", "latitude": 28.593, "longitude": 77.219},
    {"name": "PMAS Demo | Tech Park", "city": "Bengaluru", "latitude": 12.971, "longitude": 77.594},
    {"name": "PMAS Demo | Riverfront", "city": "Ahmedabad", "latitude": 23.022, "longitude": 72.571},
]

DEMO_SUBSCRIBERS = [
    {"name": "City Ops", "channel": "email", "destination": "ops-demo@example.com"},
    {"name": "Environmental Desk", "channel": "email", "destination": "env-demo@example.com"},
]

DEMO_RULES = [
    {"pollutant": "PM2.5", "threshold": 90.0, "duration_minutes": 30, "severity": "high"},
    {"pollutant": "PM2.5", "threshold": 130.0, "duration_minutes": 30, "severity": "critical"},
    {"pollutant": "PM10", "threshold": 140.0, "duration_minutes": 30, "severity": "medium"},
]

READING_SERIES = {
    "PMAS Demo | Marine Drive": {
        "PM2.5": [42, 44, 48, 54, 61, 68, 76, 81],
        "PM10": [78, 82, 88, 94, 103, 108, 112, 118],
    },
    "PMAS Demo | Bandra Link": {
        "PM2.5": [58, 62, 70, 84, 93, 101, 116, 124],
        "PM10": [95, 101, 112, 126, 132, 141, 154, 162],
    },
    "PMAS Demo | Connaught Place": {
        "PM2.5": [112, 118, 126, 132, 141, 153, 161, 172],
        "PM10": [165, 172, 181, 194, 206, 218, 231, 244],
    },
    "PMAS Demo | Lodhi Corridor": {
        "PM2.5": [88, 92, 98, 105, 114, 119, 127, 133],
        "PM10": [134, 139, 146, 155, 166, 174, 185, 191],
    },
    "PMAS Demo | Tech Park": {
        "PM2.5": [28, 31, 29, 34, 37, 42, 45, 49],
        "PM10": [52, 55, 57, 61, 64, 71, 74, 79],
    },
    "PMAS Demo | Riverfront": {
        "PM2.5": [36, 39, 45, 52, 60, 66, 73, 82],
        "PM10": [68, 73, 81, 91, 98, 105, 117, 129],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the local PMAS database with dashboard demo data.")
    parser.add_argument("--reset-demo", action="store_true", help="Delete existing demo records before reseeding.")
    return parser.parse_args()


def clear_demo_data() -> None:
    with SessionLocal() as db:
        demo_station_ids = [
            station.id
            for station in db.query(Station).filter(Station.name.like("PMAS Demo | %")).all()
        ]

        if demo_station_ids:
            db.query(Alert).filter(Alert.station_id.in_(demo_station_ids)).delete(synchronize_session=False)
            db.query(AQIRecord).filter(AQIRecord.station_id.in_(demo_station_ids)).delete(synchronize_session=False)
            db.query(Reading).filter(Reading.station_id.in_(demo_station_ids)).delete(synchronize_session=False)
            db.query(Station).filter(Station.id.in_(demo_station_ids)).delete(synchronize_session=False)

        db.query(NotificationSubscriber).filter(NotificationSubscriber.destination.like("%-demo@example.com")).delete(
            synchronize_session=False
        )
        db.query(AlertRule).filter(
            ((AlertRule.pollutant == "PM2.5") & (AlertRule.threshold.in_([90.0, 130.0])))
            | ((AlertRule.pollutant == "PM10") & (AlertRule.threshold == 140.0))
        ).delete(synchronize_session=False)

        db.commit()


def existing_demo_present() -> bool:
    with SessionLocal() as db:
        return db.query(Station).filter(Station.name.like("PMAS Demo | %")).first() is not None


def seed_demo_data() -> None:
    Base.metadata.create_all(bind=engine)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    with SessionLocal() as db:
        stations_by_name: dict[str, Station] = {}
        for station_payload in DEMO_STATIONS:
            station = Station(**station_payload, is_active=True)
            db.add(station)
            db.flush()
            stations_by_name[station.name] = station

        for subscriber_payload in DEMO_SUBSCRIBERS:
            db.add(NotificationSubscriber(**subscriber_payload, is_active=True))

        for rule_payload in DEMO_RULES:
            db.add(AlertRule(**rule_payload, is_enabled=True))

        for station_name, pollutant_map in READING_SERIES.items():
            station = stations_by_name[station_name]
            pm25_values = pollutant_map["PM2.5"]
            pm10_values = pollutant_map["PM10"]

            for index, (pm25_value, pm10_value) in enumerate(zip(pm25_values, pm10_values, strict=True)):
                timestamp = now - timedelta(minutes=(len(pm25_values) - index) * 15)
                db.add(
                    Reading(
                        station_id=station.id,
                        pollutant="PM2.5",
                        value=pm25_value,
                        timestamp=timestamp,
                        quality_flag="valid",
                    )
                )
                db.add(
                    Reading(
                        station_id=station.id,
                        pollutant="PM10",
                        value=pm10_value,
                        timestamp=timestamp,
                        quality_flag="valid",
                    )
                )

                aqi, category = calculate_aqi(pm25_value, pm10_value)
                db.add(AQIRecord(station_id=station.id, aqi=aqi, category=category, timestamp=timestamp))

        db.flush()

        alerts_to_create = [
            {
                "station_name": "PMAS Demo | Connaught Place",
                "pollutant": "PM2.5",
                "severity": "critical",
                "message": "PM2.5 levels have remained above critical threshold for the last 30 minutes.",
                "started_at": now - timedelta(minutes=25),
            },
            {
                "station_name": "PMAS Demo | Lodhi Corridor",
                "pollutant": "PM10",
                "severity": "medium",
                "message": "PM10 levels are elevated and trending upward across the last observation window.",
                "started_at": now - timedelta(minutes=40),
            },
            {
                "station_name": "PMAS Demo | Bandra Link",
                "pollutant": "PM2.5",
                "severity": "high",
                "message": "PM2.5 concentrations remain high and require operator review.",
                "started_at": now - timedelta(minutes=18),
            },
        ]

        for alert_payload in alerts_to_create:
            station = stations_by_name[alert_payload.pop("station_name")]
            db.add(Alert(station_id=station.id, status="open", ended_at=None, **alert_payload))

        db.commit()


def main() -> None:
    args = parse_args()
    if args.reset_demo:
        clear_demo_data()

    if existing_demo_present():
        print("Demo data already exists. Run with --reset-demo to replace it.")
        return

    seed_demo_data()
    print("Demo dashboard data seeded successfully.")


if __name__ == "__main__":
    main()