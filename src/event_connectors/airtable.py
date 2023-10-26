import pyairtable
from src.event_models.events import AirtableEvent

TABLE_NAME = "Events"

class Airtable(pyairtable.Table):
    """Handles Airtable API interaction.

    All operations use AirtableEvent objects to represent the events that we
    will push or pull from the API. This is a wrapper class around the API that
    is responsible for translating AirtableEvent objects into (or from) a
    format the API requires and calling the API functions.
    """
    def __init__(self, personal_access_token: str, base_id: str):
        super().__init__(personal_access_token, base_id, TABLE_NAME)

    def events(self) -> list[AirtableEvent]:
        return [AirtableEvent(event) for event in super().all()]

    def add_events(self, events_to_add: list[AirtableEvent]):
        self.batch_create([event.raw["fields"] for event in events_to_add])

    def update_events(self, events_to_update: list[AirtableEvent]):
        self.batch_update([event.raw for event in events_to_update])
