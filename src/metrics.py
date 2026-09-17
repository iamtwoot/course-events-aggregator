from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

events_provider_requests_total = Counter(
    "events_provider_requests_total",
    "Total requests to Events Provider API",
    ["endpoint", "status"],
)

events_provider_requests_duration_seconds = Histogram(
    "events_provider_requests_duration_seconds",
    "Events Provider API request duration",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)
