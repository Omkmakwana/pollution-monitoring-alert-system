# Pollution Monitoring and Alert System

A full-stack air quality monitoring platform built with FastAPI, SQLite, and a live operations dashboard. The project ingests pollutant readings, calculates AQI, evaluates alert rules, tracks notifications, and exposes both REST APIs and a browser-based control surface for operators.

It is designed as a production-style academic and engineering project, with supporting lifecycle documentation covering planning through maintenance.

## Why This Project Exists

Urban air quality systems need more than raw sensor values. Operators need to answer practical questions quickly:

- Which stations are deteriorating right now?
- Where are the highest-risk locations?
- Which alerts are open and how severe are they?
- Are notification subscribers configured and active?
- What does the latest particulate trend look like for a selected station?

This system turns pollutant data into actionable monitoring signals through AQI computation, rule-based alerting, and a visual dashboard.

## Highlights

- FastAPI backend with structured validation and clear REST endpoints
- SQLite persistence through SQLAlchemy ORM
- AQI calculation for PM2.5 and PM10 with category classification
- Configurable alert rules by pollutant, threshold, duration, and severity
- Alert acknowledgment workflow and open-alert tracking
- Subscriber management for email and SMS channels
- Notification delivery with retry and backoff support
- Request logging with correlation id and timing metadata
- Health, liveness, and readiness endpoints
- Live operations dashboard with:
  - KPI summary cards
  - station intelligence rail
  - selected-station spotlight panel
  - interactive map
  - particulate trend chart
  - live alert feed
  - city-level insight cards
  - pollutant snapshot summary
- Demo data seeding for local dashboard population
- Automated API and unit tests with pytest

## Tech Stack

| Layer | Technology |
| --- | --- |
| API framework | FastAPI |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic 2 |
| Database | SQLite |
| Frontend | HTML, CSS, vanilla JavaScript |
| Charts | Chart.js |
| Mapping | Leaflet |
| Testing | pytest, httpx |
| Notifications | SMTP, Twilio |
| Containerization | Docker, Docker Compose |

## System Capabilities

### Monitoring

- Register and list monitoring stations
- Ingest pollutant readings for `PM2.5`, `PM10`, `CO`, `NO2`, `SO2`, and `O3`
- Retrieve recent station readings
- Compute and query the latest AQI record per station

### Alerting

- Create alert rules with threshold and duration windows
- Evaluate rules against incoming readings
- Open alerts when thresholds remain breached across the configured window
- Acknowledge alerts through the API
- Filter alerts by station, pollutant, status, and severity

### Notification Management

- Register subscribers for `email` or `sms`
- Prevent duplicate subscribers by `channel + destination`
- Retry failed deliveries with configurable backoff
- Support SMTP email and Twilio SMS integrations

### Dashboard Experience

- Overview metrics for network status and alert posture
- Ranked station cards with latest AQI, PM2.5, PM10, and update time
- Interactive map synchronized with station selection
- Recent particulate trend chart for the active station
- City summaries with open-alert counts and average AQI
- Pollutant network snapshot with average and peak values

## Project Structure

```text
pollution-monitoring-alert-system/
|-- app/
|   |-- alerts.py
|   |-- aqi.py
|   |-- config.py
|   |-- crud.py
|   |-- database.py
|   |-- logging_utils.py
|   |-- main.py
|   |-- models.py
|   |-- notifications.py
|   |-- schemas.py
|   `-- static/
|       |-- app.js
|       |-- index.html
|       `-- styles.css
|-- docs/
|-- tests/
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
`-- seed_demo_data.py
```

## Architecture Overview

1. Clients submit station, reading, rule, alert, and subscriber requests through the REST API.
2. Incoming readings are persisted in SQLite.
3. PM2.5 and PM10 readings are used to generate AQI records.
4. Alert rules are evaluated for threshold breaches across a time window.
5. New alerts trigger notification fan-out to active subscribers.
6. The dashboard consumes `/dashboard/summary` and station reading endpoints to render live operational views.

## Getting Started

### Local Development

#### 1. Create a virtual environment

```bash
python -m venv .venv
```

#### 2. Activate it

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Start the application

```bash
uvicorn app.main:app --reload
```

#### 5. Open the app

- Dashboard: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Demo Data for the Dashboard

To populate the dashboard with a realistic local dataset:

```bash
python seed_demo_data.py
```

To replace existing demo entries with a fresh seeded dataset:

```bash
python seed_demo_data.py --reset-demo
```

The seeder creates:

- demo stations across multiple cities
- historical PM2.5 and PM10 readings
- AQI records
- alert rules
- open alerts
- demo notification subscribers

## Configuration

The application is configured through environment variables.

| Variable | Purpose | Default |
| --- | --- | --- |
| `PMAS_DB_URL` | Database connection string | `sqlite:///./pmas.db` |
| `PMAS_API_KEY` | Optional API key for write endpoints | empty |
| `PMAS_LOG_LEVEL` | Application log level | `INFO` |
| `PMAS_DEFAULT_PAGE_SIZE` | Default list page size | `30` |
| `PMAS_MAX_PAGE_SIZE` | Maximum list page size | `100` |
| `PMAS_NOTIFICATION_RETRY_COUNT` | Retry attempts after first notification try | `2` |
| `PMAS_NOTIFICATION_RETRY_BACKOFF_SECONDS` | Retry backoff base in seconds | `0.5` |
| `PMAS_SMTP_HOST` | SMTP host for email delivery | empty |
| `PMAS_SMTP_PORT` | SMTP port | `587` |
| `PMAS_SMTP_USER` | SMTP username | empty |
| `PMAS_SMTP_PASSWORD` | SMTP password | empty |
| `PMAS_SMTP_USE_TLS` | Enable TLS for SMTP | `true` |
| `PMAS_EMAIL_FROM` | Sender address for emails | empty |
| `PMAS_TWILIO_ACCOUNT_SID` | Twilio account sid | empty |
| `PMAS_TWILIO_AUTH_TOKEN` | Twilio auth token | empty |
| `PMAS_TWILIO_FROM_PHONE` | Twilio sender phone number | empty |

### API Key Behavior

If `PMAS_API_KEY` is configured, write endpoints require:

```http
X-API-Key: <your-api-key>
```

## Core API Endpoints

| Area | Endpoint | Method | Purpose |
| --- | --- | --- | --- |
| Health | `/health` | GET | Basic health check |
| Health | `/health/live` | GET | Liveness probe |
| Health | `/health/ready` | GET | Readiness probe with DB connectivity |
| Stations | `/stations` | POST | Create a station |
| Stations | `/stations` | GET | List stations with pagination and city filter |
| Readings | `/readings` | POST | Ingest a pollutant reading |
| Readings | `/stations/{station_id}/readings/recent` | GET | Get recent readings for a station |
| AQI | `/stations/{station_id}/aqi/latest` | GET | Get latest AQI for a station |
| Rules | `/alert-rules` | POST | Create an alert rule |
| Rules | `/alert-rules` | GET | List alert rules |
| Alerts | `/alerts` | GET | List alerts with filtering |
| Alerts | `/alerts/{alert_id}/ack` | POST | Acknowledge an alert |
| Subscribers | `/subscribers` | POST | Create subscriber |
| Subscribers | `/subscribers` | GET | List subscribers with filtering |
| Dashboard | `/dashboard/summary` | GET | Return dashboard overview data |

## Validation and Behavior Notes

- Station latitude must be within `-90..90`
- Station longitude must be within `-180..180`
- Recent reading `limit` must be within `1..100`
- Subscribers are validated by channel type:
  - `email` must be email-shaped
  - `sms` must be E.164-style (`+<digits>`)
- Duplicate subscribers return `409 Conflict`
- AQI is derived from the latest PM2.5 and PM10 values available for a station
- Alert generation is driven by enabled rules and recent-reading windows

## Example API Flow

1. Create a station with `POST /stations`
2. Create an alert rule with `POST /alert-rules`
3. Ingest readings with `POST /readings`
4. Query AQI with `GET /stations/{station_id}/aqi/latest`
5. Review active alerts with `GET /alerts`
6. Acknowledge an alert with `POST /alerts/{alert_id}/ack`
7. Add notification subscribers with `POST /subscribers`
8. Open the dashboard at `/`

## Running Tests

```bash
pytest -q
```

The test suite covers:

- health checks
- station, reading, AQI, and alert flow
- subscriber validation and duplicate prevention
- pagination and filtering
- API key protection
- dashboard summary payload shape

## Docker Deployment

### Build and run with Docker Compose

```bash
docker compose up --build
```

The compose setup:

- builds the FastAPI app image from `Dockerfile`
- exposes port `8000`
- stores SQLite data in a named Docker volume
- passes notification-related environment variables into the container

After startup:

- Dashboard: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Operational Notes

- The dashboard auto-refreshes periodically while preserving selected station context
- The app logs request start and completion with request ids and response timing
- Write endpoints can be protected without changing the public read-only dashboard experience
- Notification integrations are optional; the application still runs without SMTP or Twilio credentials

## Lifecycle Documentation

This repository also includes lifecycle artifacts for the project:

- `docs/01-planning.md`
- `docs/02-analysis.md`
- `docs/03-design.md`
- `docs/04-development.md`
- `docs/05-implementation.md`
- `docs/06-testing.md`
- `docs/07-verification-validation.md`
- `docs/08-maintenance.md`

## Future Enhancements

- historical date-range analytics and reporting endpoints
- station activation and administrative management flows
- dashboard-side alert acknowledgment controls
- richer notification history and delivery analytics
- exportable reports for operations and compliance workflows
