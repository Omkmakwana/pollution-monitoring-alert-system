# 05 - Implementation

## Deployment Blueprint
- Runtime: Uvicorn serving FastAPI app.
- Database: SQLite for local MVP deployment.
- Entry point: `uvicorn app.main:app --reload`.

## Environment Setup
- Create virtual environment.
- Install dependencies from `requirements.txt`.
- Start service and verify `/health` endpoint.

## Operational Runbook (MVP)
- Create station and rules first.
- Start ingesting readings.
- Monitor latest AQI and generated alerts.
- Acknowledge alerts after operator review.
