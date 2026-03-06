# 02 - Analysis

## Functional Requirements
- Register and list stations.
- Ingest pollutant readings (PM2.5, PM10, CO, NO2, SO2, O3).
- Compute AQI from latest PM2.5 and PM10 readings.
- Define configurable alert rules by pollutant, threshold, duration, and severity.
- Generate and acknowledge alerts.

## Non-Functional Requirements
- API response time suitable for operational dashboard usage.
- Data integrity through transactional persistence.
- Maintainability via modular Python packages and tests.
- Security baseline through controlled payload validation.

## Risks and Mitigations
- Noisy sensors: add quality flags and future calibration policy.
- Intermittent connectivity: support delayed reads via payload timestamp.
- False alerts: enforce duration-based rule checks.
