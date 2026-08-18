from fastapi import Request

from src.services.events_provider_client import EventsProviderClient


def get_events_provider_client(request: Request) -> EventsProviderClient:
    return request.app.state.events_provider_client
