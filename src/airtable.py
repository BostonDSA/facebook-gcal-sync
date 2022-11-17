import pyairtable
from events import AirtableEvent

BASE_ID = "appt5WkXVfwvdG1nd"
TABLE_NAME = "Events"

class Airtable(pyairtable.Table):
    """Handles Airtable API interaction.

    All operations use AirtableEvent objects to represent the events that we
    will push or pull from the API. This is a wrapper class around the API that
    is responsible for translating AirtableEvent objects into (or from) a
    format the API requires and calling the API functions.
    """
    def __init__(self, api_key: str):
        super().__init__(api_key, BASE_ID, TABLE_NAME)

    def events(self) -> list[AirtableEvent]:
        return [AirtableEvent(event) for event in super().all()]

    def add_events(self, events_to_add: list[AirtableEvent]):
        self.batch_create([event.raw["fields"] for event in events_to_add])

    def update_events(self, events_to_update: list[AirtableEvent]):
        self.batch_update([event.raw for event in events_to_update])

    def delete_events(self, events_to_delete: list[AirtableEvent]):
        self.batch_delete([event.airtable_id for event in events_to_delete])
