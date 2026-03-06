# 03 - Design

## Architecture
- Style: layered backend architecture.
- Presentation: FastAPI routes.
- Domain: AQI and alert evaluation services.
- Data: SQLAlchemy models + SQLite.

## Core Components
- `app/main.py`: API endpoints and workflow orchestration.
- `app/crud.py`: data access and queries.
- `app/aqi.py`: AQI computation rules.
- `app/alerts.py`: threshold-duration alert evaluation.
- `app/models.py`: relational schema definitions.

## Data Design
- `stations`: metadata per monitoring station.
- `readings`: pollutant values by station and timestamp.
- `aqi_records`: computed AQI history.
- `alert_rules`: operational threshold policy.
- `alerts`: generated incidents and closure state.

## Design Principles Applied
- Single responsibility across modules.
- Separation of concerns between API, domain logic, and persistence.
- Configurable policy via alert rules (no hardcoded thresholds).
