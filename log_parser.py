
import json
import sys
from pathlib import Path
from statistics import mean

SUMMARY_FILE = Path("k6_results.json")
RAW_FILE = Path("raw_metrics.json")
SLOW_THRESHOLD_MS = 500.0


def load_summary():
    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"Missing {SUMMARY_FILE}. Run the k6 test first."
        )

    with SUMMARY_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def load_raw_metrics():
    """Read k6's newline-delimited JSON metric output."""
    records = []

    if not RAW_FILE.exists():
        print(f"Warning: {RAW_FILE} not found.")
        return records

    with RAW_FILE.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON at line {line_number}.")

    return records


def metric_values(summary):
    metrics = summary.get("metrics", {})

    requests = metrics.get("http_reqs", {}).get("values", {})
    failures = metrics.get("http_req_failed", {}).get("values", {})
    duration = metrics.get("http_req_duration", {}).get("values", {})

    return {
        "total_requests": int(requests.get("count", 0)),
        "error_rate_pct": float(failures.get("rate", 0)) * 100,
        "avg_latency_ms": float(duration.get("avg", 0)),
        "p95_latency_ms": float(duration.get("p(95)", 0)),
    }


def find_slow_requests(records):
    slow = []

    for record in records:
        if (
            record.get("type") != "Point"
            or record.get("metric") != "http_req_duration"
        ):
            continue

        data = record.get("data", {})
        tags = data.get("tags", {})
        duration = float(data.get("value", 0))

        if duration > SLOW_THRESHOLD_MS:
            slow.append({
                "time": data.get("time", "unknown"),
                "duration_ms": round(duration, 2),
                "status": tags.get("status", "unknown"),
                "method": tags.get("method", "unknown"),
                "url": tags.get("url", "unknown"),
            })

    return slow


def print_report(metrics, slow_requests):
    print("\n" + "=" * 52)
    print("       K6 PERFORMANCE TEST REPORT")
    print("=" * 52)
    print(f"Total HTTP requests : {metrics['total_requests']}")
    print(f"Error rate          : {metrics['error_rate_pct']:.2f}%")
    print(f"Average latency     : {metrics['avg_latency_ms']:.2f} ms")
    print(f"P95 latency         : {metrics['p95_latency_ms']:.2f} ms")
    print(f"Slow requests       : {len(slow_requests)}")
    print(f"Slow threshold      : > {SLOW_THRESHOLD_MS:.0f} ms")

    if not slow_requests:
        print("\nNo individual requests exceeded the threshold.")
    else:
        print("\nSlow request details:")
        for item in slow_requests[:20]:
            print(
                f"- {item['duration_ms']:.2f} ms | "
                f"HTTP {item['status']} | "
                f"{item['method']} | {item['url']} | "
                f"{item['time']}"
            )

        if len(slow_requests) > 20:
            print(f"... and {len(slow_requests) - 20} more.")

    print("=" * 52)


# Optional future extension:
#
# def generate_rca_with_llm(slow_requests, api_key):
#     Send a small, sanitized sample of slow_requests to an
#     approved Gemini or OpenAI API using its official SDK.
#     Ask for exactly three evidence-based RCA hypotheses.
#     Do not send credentials, personal data, or production secrets.
#     Treat the result as hypotheses, not a proven root cause.
#
# Add API authentication, timeouts, and error handling before use.


def main():
    try:
        summary = load_summary()
        records = load_raw_metrics()
        metrics = metric_values(summary)
        slow_requests = find_slow_requests(records)
        print_report(metrics, slow_requests)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
