# k6 Observability Automation

A hands-on performance engineering project using k6,
Python, Git, and GitHub Actions.

## Features
- Ramping virtual-user workload
- HTTP status validation
- p95 latency and error-rate thresholds
- JSON metrics export
- Python slow-request analysis
- CI/CD integration

## Run locally

```powershell
k6 run --out json=raw_metrics.json test.js
python log_parser.py
Pipeline trigger test.
