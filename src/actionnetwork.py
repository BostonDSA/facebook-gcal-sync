import pyactionnetwork
import requests
from events import ActionNetworkEvent

CREATION_WINDOW_DAYS = 365

class ActionNetwork(pyactionnetwork.ActionNetworkApi):
    def __init__(self, api_key):
        super().__init__(api_key)

    def _events(self, min_creation_time=None):
        """
        Pulls the first page of events from ActionNetwork, potentially filtered by the passed minimum creation time.

        :param min_creation_time: ISO-Formatted timestamp.  If passed, will only get events created after the specified time.
        :return:
        """
        url = self.resource_to_url('events')
        params = {}
        if min_creation_time is not None:
            params['filter'] = f"created_date gt '{min_creation_time}'"

        return requests.get(url, params=params, headers=self.headers).json()

    def raw_events(self, **kwargs):
        events_response = self._events(**kwargs)
        events = []
        events += events_response['_embedded']['osdi:events'] or []

        while events_response['page'] < events_response['total_pages']:
            print(f"Fetching event page {events_response['page']} out of {events_response['total_pages']}")
            events_response = requests.get(events_response['_links']['next']['href'], headers=self.headers).json()
            events += events_response['_embedded']['osdi:events'] or []

        return events

    def events(self, **kwargs):
        """Get events as ActionNetworkEvents, filter out unwanted events"""
        return [
            ActionNetworkEvent(raw_event)
            for raw_event in self.raw_events(**kwargs)
            if raw_event['origin_system'] != 'Facebook Sync'
        ]

    def event(self, event_id):
        url = self.resource_to_url('events')
        url += '/' + event_id
        return ActionNetworkEvent(requests.get(url, headers=self.headers).json())
