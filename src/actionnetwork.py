import pyactionnetwork
import fest.utils as utils
import requests
from datetime import datetime
from datetime import timedelta
from pytz import utc
from dateutil.parser import parse
import json

CREATION_WINDOW_DAYS = 365


class ActionNetwork(pyactionnetwork.ActionNetworkApi):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.logger = utils.logger(self)

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

    def get_events(self, **kwargs):
        return utils.Future(self.iter_events(**kwargs))

    def iter_events(self, **kwargs):
        events_response = self._events(**kwargs)

        yield from events_response['_embedded']['osdi:events'] or []

        while events_response['page'] < events_response['total_pages']:
            events_response = requests.get(events_response['_links']['next']['href'], headers=self.headers).json()
            yield from events_response['_embedded']['osdi:events'] or []

    def sync(self, page):
        return ActionNetworkSyncFuture(page.get_events(time_filter='upcoming'), page, self)

    def create_event(self, data):
        url = self.resource_to_url('events')
        return requests.post(url, headers=self.headers, json=data)

    def update_event(self, url, data):
        return requests.put(url, headers=self.headers, json=data)


def fb_start_date_before(fb_event, target_date):
    if 'start_time' not in fb_event: return False
    return parse(fb_event['start_time']) < target_date


class ActionNetworkSyncFuture:
    def __init__(self, request, page, action_network):
        self.request = request
        self.page = page
        self.action_network = action_network

    @classmethod
    def fb_to_action_network(cls, fb_event):
        event = {
            'name': fb_event['name'],
            'title': fb_event['name'],
            'origin_system': 'Facebook Sync',
            'description': fb_event['description'],
            'start_date': fb_event['start_time'],
            'identifiers': [
                f'facebook_id:{fb_event["id"]}',
            ],

        }
        if 'place' in fb_event:
            fb_place = fb_event['place']
            fb_location = {}
            if 'location' in fb_place:
                fb_location = fb_place['location']
            an_location = {}
            if 'name' in fb_place:
                an_location['venue'] = fb_place['name']
            if 'zip' in fb_location:
                an_location['postal_code'] = fb_location['zip']
            if 'latitude' in fb_location:
                an_location['location'] = {'latitude': fb_location['latitude'], 'longitude': fb_location['longitude']}
            if 'city' in fb_location:
                an_location['locality'] = fb_location['city']
            if 'street' in fb_location:
                an_location['address_lines'] = [fb_location['street']]
            event['location'] = an_location
        return event

    def execute(self, dryrun=False):
        # ActionNetwork doesn't support filtering events based on start time, so we can't match Facebook's upcoming
        # window here.  To get around this, we will only create ActionNetwork events CREATION_WINDOW_DAYS - 1 in advance
        # of the event happening, and only check existing events that were created in the last CREATION_WINDOW_DAYS.
        # If we didn't do this, we might accidentally create a duplicate ActionNetwork event if the existing one
        # was created too far in advance

        now = datetime.utcnow().replace(tzinfo=utc)

        action_network_load_minimum = now + timedelta(days=-CREATION_WINDOW_DAYS)

        # We will only create CREATION_WINDOW_DAYS - 1 in advance
        facebook_load_maximum = now + timedelta(days=(CREATION_WINDOW_DAYS - 1))

        # Get facebook events
        facebook_events = {x['id']: x for x in self.request.execute() if fb_start_date_before(x, facebook_load_maximum)}

        if not any(facebook_events):
            self.action_network.logger.info('NO-OP')
            return self

        # Get Action network events
        action_network_events = {
            next(id.split(':')[1] for id in x['identifiers'] if id.startswith('facebook_id:')): x
            for x in self.action_network.iter_events(
            min_creation_time=action_network_load_minimum.isoformat(),
        )
            if any(id.startswith('facebook_id:') for id in x['identifiers'])
        }

        create = []
        update = []

        # Get create/update/delete request payloads
        for facebook_id, event in facebook_events.items():
            if facebook_id not in action_network_events:
                create.append(ActionNetworkSyncFuture.fb_to_action_network(event))
            elif 'updated_time' in event and (
                    parse(event['updated_time']) > parse(action_network_events[facebook_id]['modified_date'])):
                update.append({
                    'facebook': ActionNetworkSyncFuture.fb_to_action_network(event),
                    'action_network': action_network_events[facebook_id]

                })

        self.action_network.logger.info(f'Creating {len(create)} events.')
        self.action_network.logger.info(f'Updating {len(update)} events.')

        if not dryrun:
            for update_data in update:
                self.action_network.update_event(update_data['action_network']['_links']['self']['href'],
                                                 update_data['facebook'])

            for create_data in create:
                self.action_network.create_event(create_data)

        return self
