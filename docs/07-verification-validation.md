# 07 - Verification and Validation

## Verification (Build the system right)
- Requirements mapped to API contracts and test cases.
- Code-level verification through typed interfaces and test assertions.
- Data model verification through relational constraints and mandatory fields.

## Validation (Build the right system)
- Scenario validation for sustained high pollutant values leading to alerts.
- Operator workflow validation for acknowledgment of active alerts.
- Health endpoint validation for service operability.

## Traceability Snapshot
- Requirement: sustained threshold breach detection.
- Design element: duration-aware rule in `app/alerts.py`.
- Test evidence: API alert generation tests.
