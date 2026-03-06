# 06 - Testing

## Test Strategy
- Unit tests for AQI formula and category behavior.
- API tests for station creation, rule creation, reading ingestion, and alert generation.

## Acceptance Criteria
- AQI endpoint returns computed value after PM readings are posted.
- Alert created when rule threshold and duration condition are met.
- Alert can be acknowledged through API.

## Automation
- Framework: pytest.
- Command: `pytest -q`.
