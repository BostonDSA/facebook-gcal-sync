import unittest.mock as mock
import requests
from src import actionnetwork
from fest import facebook
from datetime import datetime

TEST_KEY = 'test_key'

HEADER = {'OSDI-API-Token': TEST_KEY}


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


ACTION_NETWORK_EVENTS = [
    [
        {
            'identifiers': [
                'action_network_id:1',
                'facebook_id:1',
            ],
            'title': 'event_1',
            'name': 'event_1',
            'description': 'test',
            '_links': {
                'self': {'href': 'https://actionnetwork.org/api/v2/events/1'}
            }
        },
        {
            'identifiers': [
                'action_network_id:2',
            ],
            'title': 'ignored',
            '_links': {
                'self': {'href': 'https://actionnetwork.org/api/v2/events/2'}
            }
        },
    ],
    [
        {
            'identifiers': [
                'action_network_id:3',
                'facebook_id:2',
            ],
            'title': 'event_1',
            'name': 'event_1',
            'description': 'test',
            'modified_date': '2018-11-12T13:00:00-0500',
            '_links': {
                'self': {'href': 'https://actionnetwork.org/api/v2/events/3'}
            }
        },
    ]

]

FACEBOOK_EVENTS = [
    {
        'id': '1',
        'start_time': '2018-12-12T12:00:00-0500',
        'end_time': '2018-12-12T13:00:00-0500',
        'description': 'doesnt update because no modified time',
        'name': 'Event 1',
        'place': {
            'name': 'Boston Public Library',
            'location': {
                'city': 'Boston',
                'country': 'United States',
                'state': 'MA',
                'street': '700 Boylston St',
                'zip': '02116',
            },
        },
    },
    {
        'id': '2',
        'start_time': '2018-12-13T12:00:00-0500',
        'end_time': '2018-12-13T13:00:00-0500',
        'updated_time': '2018-11-13T13:00:00-0500',
        'description': 'updates',
        'name': 'Updated Event 2',
        'place': {
            'name': 'Boston Public Library',
            'location': {
                'city': 'Boston',
                'country': 'United States',
                'state': 'MA',
                'street': '700 Boylston St',
                'zip': '02116',
                'latitude': '100',
                'longitude': '150',
            },
        },
    },
    {
        'id': '3',
        'start_time': '2018-12-14T12:00:00-0500',
        'end_time': '2018-12-14T13:00:00-0500',
        'description': 'some description 3',
        'name': 'Event 3',
        'place': {
            'name': 'Boston Public Library',
            'location': {
                'city': 'Boston',
                'country': 'United States',
                'state': 'MA',
                'street': '700 Boylston St',
                'zip': '02116',
            },
        },
    },
    {
        'id': '4',
        'start_time': '2019-12-20T12:00:00-0500',
        'end_time': '2019-12-20T13:00:00-0500',
        'description': 'will not be created -- too far in advance',
        'name': 'Event 4',
        'place': {
            'name': 'Boston Public Library',
            'location': {
                'city': 'Boston',
                'country': 'United States',
                'state': 'MA',
                'street': '700 Boylston St',
                'zip': '02116',
            },
        },
    },
    {
        'id': '5',
        'start_time': '2019-08-14T12:00:00-0500',
        'end_time': '2019-08-14T13:00:00-0500',
        'description': 'some description 3',
        'name': 'Event 5',
        'place': {
            'name': 'Zoom meeting',
        },
    },
    {
        'id': '6',
        'description': 'not created with no time',
        'name': 'Event 6',
        'place': {
            'name': 'Somerville Public Library',
            'location': {
                'city': 'Somerville',
                'country': 'United States',
                'state': 'MA',
                'street': '700 Summer St',
                'zip': '02143',
            },
        },
    },
]


def fake_get(url, *args, **kwargs):
    if url == "https://actionnetwork.org/api/v2/":
        resp = {
            'motd': 'test',
            '_links': {
                'events': {
                    'href': 'https://actionnetwork.org/api/v2/events'
                }
            }
        }
        return MockResponse(resp, 200)
    elif url.startswith('https://actionnetwork.org/api/v2/events'):
        if 'page=2' in url:
            resp = {
                'total_pages': 2,
                'page': 2,
                '_links': {
                    'next': {
                        'href': 'https://actionnetwork.org/api/v2/events?page=3'
                    }
                },
                '_embedded': {
                    'osdi:events': ACTION_NETWORK_EVENTS[1]
                }
            }
            return MockResponse(resp, 200)
        else:
            resp = {
                'total_pages': 2,
                'page': 1,
                '_links': {
                    'next': {
                        'href': 'https://actionnetwork.org/api/v2/events?page=2'
                    }
                },
                '_embedded': {
                    'osdi:events': ACTION_NETWORK_EVENTS[0]
                }
            }
            return MockResponse(resp, 200)

    return MockResponse({}, 404)


@mock.patch('src.actionnetwork.datetime')
@mock.patch('src.actionnetwork.requests.post')
@mock.patch('src.actionnetwork.requests.put')
@mock.patch('src.actionnetwork.requests.get', side_effect=fake_get)
def test_sync(get, put, post, dt):
    dt.utcnow.return_value = datetime(year=2018, day=5, month=12, hour=0, minute=0)
    dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    mockf = mock.MagicMock()

    mockf.get_object.side_effect = [{'data': FACEBOOK_EVENTS}]
    mockf.get_objects.side_effect = [{x['id']: x for x in FACEBOOK_EVENTS}]

    page = facebook.FacebookPage(mockf, 'TestPage')

    client = actionnetwork.ActionNetwork(TEST_KEY)

    client.sync(page).execute()

    put.assert_called_once_with(
        'https://actionnetwork.org/api/v2/events/3',
        headers=HEADER,
        json={
            'name': 'Updated Event 2',
            'title': 'Updated Event 2',
            'origin_system': 'Facebook Sync',
            'description': 'updates',
            'start_date': '2018-12-13T12:00:00-0500',
            'identifiers': [
                'facebook_id:2'
            ],
            'location': {
                'venue': 'Boston Public Library',
                'postal_code': '02116',
                'locality': 'Boston',
                'location': {
                    'latitude': '100',
                    'longitude': '150',
                },
                'address_lines': [
                    '700 Boylston St',
                ],
            }
        },
    )

    post.assert_has_calls([
        mock.call(
            'https://actionnetwork.org/api/v2/events',
            json={
                'name': 'Event 3',
                'title': 'Event 3',
                'origin_system': 'Facebook Sync',
                'description': 'some description 3',
                'start_date': '2018-12-14T12:00:00-0500',
                'identifiers': [
                    'facebook_id:3',
                ],
                'location': {
                    'venue': 'Boston Public Library',
                    'postal_code': '02116',
                    'locality': 'Boston',
                    'address_lines': [
                        '700 Boylston St',
                    ],
                }
            },
            headers=HEADER,
        ),

        mock.call('https://actionnetwork.org/api/v2/events',
                  json={
                      'name': 'Event 5',
                      'title': 'Event 5',
                      'origin_system': 'Facebook Sync',
                      'description': 'some description 3',
                      'start_date': '2019-08-14T12:00:00-0500',
                      'identifiers': [
                          'facebook_id:5',
                      ],
                      'location': {
                          'venue': 'Zoom meeting',
                      }
                  },
                  headers=HEADER,
                  )], any_order=True)

    assert put.call_count == 1
    assert post.call_count == 2
    assert get.call_count == 3
