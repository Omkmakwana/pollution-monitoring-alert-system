import logging
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app import alerts, crud, schemas
from app.aqi import calculate_aqi
from app.config import settings, validate_settings
from app.database import Base, engine, get_db
from app.logging_utils import RequestIdAdapter, configure_logging

configure_logging()
validate_settings()
Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)
app = FastAPI(title="Pollution Monitoring and Alert System", version="1.2.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started = perf_counter()
    request_logger = RequestIdAdapter(logger, {"request_id": request_id})
    request_logger.info("Request started", extra={"path": request.url.path, "method": request.method})

    response = await call_next(request)

    duration_ms = round((perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    request_logger.info(
        "Request completed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": jsonable_encoder(exc.errors()), "path": str(request.url.path)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", extra={"request_id": request.headers.get("X-Request-ID", "-")})
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "path": str(request.url.path)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/stations", response_model=schemas.StationRead, status_code=status.HTTP_201_CREATED)
def create_station(
    payload: schemas.StationCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    return crud.create_station(
        db,
        name=payload.name,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )


@app.get("/stations", response_model=list[schemas.StationRead])
def get_stations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    city: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.list_stations_paginated(db, skip=skip, limit=limit, city=city)


@app.post("/readings", response_model=schemas.ReadingRead, status_code=status.HTTP_201_CREATED)
def create_reading(
    payload: schemas.ReadingCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
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
    aqi, category = calculate_aqi(pm25.value if pm25 else None, pm10.value if pm10 else None)
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
def create_alert_rule(
    payload: schemas.AlertRuleCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    return crud.create_alert_rule(
        db=db,
        pollutant=payload.pollutant,
        threshold=payload.threshold,
        duration_minutes=payload.duration_minutes,
        severity=payload.severity,
    )


@app.get("/alert-rules", response_model=list[schemas.AlertRuleRead])
def get_alert_rules(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db),
):
    rules = crud.list_alert_rules(db)
    return rules[skip : skip + limit]


@app.get("/alerts", response_model=list[schemas.AlertRead])
def get_alerts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    pollutant: str | None = Query(default=None),
    station_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    return crud.list_alerts_paginated(
        db,
        skip=skip,
        limit=limit,
        status=status_filter,
        severity=severity,
        pollutant=pollutant,
        station_id=station_id,
    )


@app.post("/alerts/{alert_id}/ack", response_model=schemas.AlertRead)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    alert = crud.acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.post("/subscribers", response_model=schemas.NotificationSubscriberRead, status_code=status.HTTP_201_CREATED)
def create_subscriber(
    payload: schemas.NotificationSubscriberCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
):
    existing = crud.get_subscriber_by_channel_and_destination(db, payload.channel, payload.destination)
    if existing:
        raise HTTPException(status_code=409, detail="Subscriber already exists for this channel and destination")

    return crud.create_subscriber(db, name=payload.name, channel=payload.channel, destination=payload.destination)


@app.get("/subscribers", response_model=list[schemas.NotificationSubscriberRead])
def get_subscribers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    channel: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.list_subscribers_paginated(db, skip=skip, limit=limit, channel=channel, is_active=is_active)


@app.get("/dashboard/summary", response_model=schemas.DashboardSummaryRead)
def get_dashboard_summary(db: Session = Depends(get_db)):
    stations = crud.list_stations(db)
    station_alert_counts = crud.dashboard_station_alert_counts(db)
    station_items: list[schemas.StationDashboardRead] = []

    for station in stations:
        summary = crud.latest_station_summary(db, station.id)
        alert_state = station_alert_counts.get(station.id, {"open_alert_count": 0, "dominant_severity": None})
        station_items.append(
            schemas.StationDashboardRead(
                station_id=station.id,
                station_name=station.name,
                city=station.city,
                latitude=station.latitude,
                longitude=station.longitude,
                is_active=station.is_active,
                latest_aqi=summary["latest_aqi"],
                latest_category=summary["latest_category"],
                latest_pm25=summary["latest_pm25"],
                latest_pm10=summary["latest_pm10"],
                latest_reading_at=summary["latest_reading_at"],
                open_alert_count=int(alert_state["open_alert_count"]),
                dominant_severity=alert_state["dominant_severity"],
            )
        )

    active_alerts = crud.open_alerts(db)
    return schemas.DashboardSummaryRead(
        overview=crud.dashboard_overview(db),
        stations=station_items,
        open_alerts=len(active_alerts),
        active_alerts=active_alerts,
        cities=crud.dashboard_city_summaries(db),
        pollutant_snapshot=crud.dashboard_pollutant_snapshot(db),
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
