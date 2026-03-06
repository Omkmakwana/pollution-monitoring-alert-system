# 08 - Maintenance

## Maintenance Types
- Corrective: bug fixes in ingestion and alert rules.
- Adaptive: support additional pollutants and policy changes.
- Perfective: performance optimization and dashboard integration.
- Preventive: dependency updates and security patches.

## Maintenance Plan
- Weekly dependency and vulnerability review.
- Monthly backup and restore test of operational database.
- Quarterly review of threshold policies with domain experts.
- Continuous log monitoring for abnormal ingestion behavior.

## Operational Controls
- Monitor API request logs using request-id correlation for error triage.
- Review failed notification logs and retry behavior trends weekly.
- Rotate API keys quarterly when `PMAS_API_KEY` is enabled.
- Validate readiness endpoint (`/health/ready`) from deployment probes.

## Automation
- CI pipeline runs automated tests on each push and pull request.
- Regression checks include API behavior, AQI calculations, and validation flows.
