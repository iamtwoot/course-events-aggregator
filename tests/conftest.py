import os

os.environ.setdefault(
    "POSTGRES_CONNECTION_STRING", "postgres://test:test@localhost:5432/test"
)
os.environ.setdefault("EVENTS_PROVIDER_BASE_URL", "http://events-provider.test")
os.environ.setdefault("EVENTS_PROVIDER_API_KEY", "test-key")
os.environ.setdefault("CAPASHINO_BASE_URL", "http://capashino.test")
os.environ.setdefault("CAPASHINO_API_KEY", "test-key")
