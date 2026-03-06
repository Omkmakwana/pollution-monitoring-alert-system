# Pollution Monitoring and Alert System

A production-style MVP that follows software engineering principles across planning, analysis, design, development, implementation, testing, verification/validation, and maintenance.

## Features
- Station registration and listing
- Sensor reading ingestion for pollutants (PM2.5, PM10, CO, NO2, SO2, O3)
- Strong API validation for station coordinates and recent-reading limits
- API key protection for write operations (`X-API-Key`) when configured
- Pagination and filtering support on list endpoints
- Request logging with request-id correlation and timing
- Notification retries with configurable backoff
- AQI calculation (PM2.5 and PM10 with category)
- Configurable alert rules by pollutant and duration
- Alert generation and acknowledgment workflow
- Live dashboard (`/`) with station cards, map, chart, and alert feed
- Real notification channels: email (SMTP) and SMS (Twilio)
- Notification subscriber management via API with duplicate prevention
- FastAPI REST API with SQLite persistence
- Unit and API tests using pytest

## Project Structure
- `app/`: backend source code
- `app/static/`: dashboard UI assets
- `tests/`: test suite
- `docs/`: software engineering lifecycle documents
- `Dockerfile` and `docker-compose.yml`: containerized deployment

## Quick Start
1. Create and activate virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run API:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Open docs:
   - Dashboard: `http://127.0.0.1:8000/`
   - Swagger: `http://127.0.0.1:8000/docs`

## Notification Setup
Configure environment variables (locally or in Docker):

- `PMAS_API_KEY`, `PMAS_LOG_LEVEL`, `PMAS_DEFAULT_PAGE_SIZE`, `PMAS_MAX_PAGE_SIZE`
- `PMAS_NOTIFICATION_RETRY_COUNT`, `PMAS_NOTIFICATION_RETRY_BACKOFF_SECONDS`
- `PMAS_SMTP_HOST`, `PMAS_SMTP_PORT`, `PMAS_SMTP_USER`, `PMAS_SMTP_PASSWORD`, `PMAS_SMTP_USE_TLS`, `PMAS_EMAIL_FROM`
- `PMAS_TWILIO_ACCOUNT_SID`, `PMAS_TWILIO_AUTH_TOKEN`, `PMAS_TWILIO_FROM_PHONE`

If `PMAS_API_KEY` is set, include header `X-API-Key: <value>` for write endpoints.

Create subscribers:
- `POST /subscribers` with `channel: email` and destination email
- `POST /subscribers` with `channel: sms` and destination phone (`+<country_code><number>`)

## Example Flow
1. Create station: `POST /stations`
2. Create rule: `POST /alert-rules`
3. Ingest readings: `POST /readings`
4. Check AQI: `GET /stations/{station_id}/aqi/latest`
5. List alerts: `GET /alerts`
6. Acknowledge alert: `POST /alerts/{alert_id}/ack`
7. Add subscribers: `POST /subscribers`

## API Validation Notes
- `POST /stations` validates `latitude` (`-90` to `90`) and `longitude` (`-180` to `180`).
- `GET /stations/{station_id}/readings/recent` validates `limit` in range `1..100`.
- `POST /subscribers` validates destination by channel:
   - `email`: must be email-shaped (contains `@` and no edge `@`).
   - `sms`: must use E.164 style (`+<digits>`).
- Creating a subscriber with the same `channel + destination` returns `409 Conflict`.

## API Pagination and Filtering
- `GET /stations`: `skip`, `limit`, optional `city`
- `GET /alerts`: `skip`, `limit`, optional `status`, `severity`, `pollutant`, `station_id`
- `GET /subscribers`: `skip`, `limit`, optional `channel`, `is_active`
- `GET /alert-rules`: `skip`, `limit`

## Health and Readiness
- `GET /health`: basic health
- `GET /health/live`: liveness signal
- `GET /health/ready`: readiness with DB connectivity check

## Docker Compose
1. Optional: copy `.env.example` to `.env` and set credentials.
2. Build and run:
   ```bash
   docker compose up --build
   ```
3. Access:
   - Dashboard: `http://127.0.0.1:8000/`
   - Swagger: `http://127.0.0.1:8000/docs`

## Run Tests
```bash
pytest -q
```

## Lifecycle Documentation
- `docs/01-planning.md`
- `docs/02-analysis.md`
- `docs/03-design.md`
- `docs/04-development.md`
- `docs/05-implementation.md`
- `docs/06-testing.md`
- `docs/07-verification-validation.md`
- `docs/08-maintenance.md`
