# 01 - Planning

## Chosen Process Model
- Model: V-Model with controlled iteration.
- Rationale: health-impacting alerts require strict traceability from requirements to testing.

## Goals
- Monitor pollution at stations in near real time.
- Calculate AQI and classify risk level.
- Trigger and track alerts when thresholds are crossed.

## Scope
- Included: station management, reading ingestion, AQI engine, alert rules, alert workflow, REST APIs, tests.
- Excluded (future): mobile app, GIS heatmap, ML forecasting, external SMS integration.

## Milestones
- M1: requirements baseline
- M2: architecture and data model
- M3: backend core services
- M4: integrated testing
- M5: release and maintenance handover
