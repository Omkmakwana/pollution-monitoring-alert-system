from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import alerts, crud, models, schemas
from app.aqi import calculate_aqi
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pollution Monitoring and Alert System", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/stations", response_model=schemas.StationRead, status_code=status.HTTP_201_CREATED)
def create_station(payload: schemas.StationCreate, db: Session = Depends(get_db)):
    station = crud.create_station(
        db,
        name=payload.name,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    return station


@app.get("/stations", response_model=list[schemas.StationRead])
def get_stations(db: Session = Depends(get_db)):
    return crud.list_stations(db)


@app.post("/readings", response_model=schemas.ReadingRead, status_code=status.HTTP_201_CREATED)
def create_reading(payload: schemas.ReadingCreate, db: Session = Depends(get_db)):
    station = crud.get_station(db, payload.station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    reading = crud.create_reading(
        db=db,
        station_id=payload.station_id,
        pollutant=payload.pollutant,
        value=payload.value,
        timestamp=payload.timestamp,
    )

    pm25 = crud.latest_pollutant_reading(db, payload.station_id, "PM2.5")
    pm10 = crud.latest_pollutant_reading(db, payload.station_id, "PM10")
    aqi, category = calculate_aqi(
        pm25.value if pm25 else None,
        pm10.value if pm10 else None,
    )
    crud.create_aqi_record(db, payload.station_id, aqi, category)

    alerts.evaluate_alerts_for_reading(db, reading)
    return reading


@app.get("/stations/{station_id}/aqi/latest", response_model=schemas.AQIRead)
def get_latest_aqi(station_id: int, db: Session = Depends(get_db)):
    station = crud.get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    latest = crud.latest_aqi(db, station_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No AQI data available")

    return schemas.AQIRead(
        station_id=latest.station_id,
        aqi=latest.aqi,
        category=latest.category,
        timestamp=latest.timestamp,
    )


@app.post("/alert-rules", response_model=schemas.AlertRuleRead, status_code=status.HTTP_201_CREATED)
def create_alert_rule(payload: schemas.AlertRuleCreate, db: Session = Depends(get_db)):
    return crud.create_alert_rule(
        db=db,
        pollutant=payload.pollutant,
        threshold=payload.threshold,
        duration_minutes=payload.duration_minutes,
        severity=payload.severity,
    )


@app.get("/alert-rules", response_model=list[schemas.AlertRuleRead])
def get_alert_rules(db: Session = Depends(get_db)):
    return crud.list_alert_rules(db)


@app.get("/alerts", response_model=list[schemas.AlertRead])
def get_alerts(db: Session = Depends(get_db)):
    return crud.list_alerts(db)


@app.post("/alerts/{alert_id}/ack", response_model=schemas.AlertRead)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = crud.acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.post("/subscribers", response_model=schemas.NotificationSubscriberRead, status_code=status.HTTP_201_CREATED)
def create_subscriber(payload: schemas.NotificationSubscriberCreate, db: Session = Depends(get_db)):
    existing = crud.get_subscriber_by_channel_and_destination(db, payload.channel, payload.destination)
    if existing:
        raise HTTPException(status_code=409, detail="Subscriber already exists for this channel and destination")

    return crud.create_subscriber(db, name=payload.name, channel=payload.channel, destination=payload.destination)


@app.get("/subscribers", response_model=list[schemas.NotificationSubscriberRead])
def get_subscribers(db: Session = Depends(get_db)):
    return crud.list_subscribers(db)


@app.get("/dashboard/summary", response_model=schemas.DashboardSummaryRead)
def get_dashboard_summary(db: Session = Depends(get_db)):
    stations = crud.list_stations(db)
    station_items: list[schemas.StationDashboardRead] = []

    for station in stations:
        summary = crud.latest_station_summary(db, station.id)
        station_items.append(
            schemas.StationDashboardRead(
                station_id=station.id,
                station_name=station.name,
                city=station.city,
                latitude=station.latitude,
                longitude=station.longitude,
                latest_aqi=summary["latest_aqi"],
                latest_category=summary["latest_category"],
                latest_pm25=summary["latest_pm25"],
                latest_pm10=summary["latest_pm10"],
            )
        )

    active_alerts = crud.open_alerts(db)
    return schemas.DashboardSummaryRead(
        stations=station_items,
        open_alerts=len(active_alerts),
        active_alerts=active_alerts,
    )


@app.get("/stations/{station_id}/readings/recent", response_model=list[schemas.ReadingRead])
def get_recent_readings(
    station_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    station = crud.get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return crud.recent_readings(db, station_id=station_id, limit=limit)
