from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "endpoint_dashboard_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "endpoint_dashboard_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


def observe_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    status_label = str(status_code)
    HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status_code=status_label).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration_seconds)


def metrics_payload() -> bytes:
    return generate_latest()


METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST
