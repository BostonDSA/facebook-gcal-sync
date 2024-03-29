import argparse
import json
import os
import urllib
from datetime import date
from datetime import datetime
from pprint import pprint

import boto3

from event_connectors.actionnetwork import ActionNetwork
from event_connectors.airtable import Airtable
from event_models.events import EventDiffer

SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
SLACK_FOOTER_URL = os.environ['SLACK_FOOTER_URL']
SLACK_TOPIC_ARN = os.environ['SLACK_TOPIC_ARN']

# AWS Clients
SECRETSMANAGER = boto3.client('secretsmanager')
SNS = boto3.client('sns')

ACTION_NETWORK_GROUP_KEY_MAP = os.environ.get('ACTION_NETWORK_GROUP_KEY_MAP')
if not ACTION_NETWORK_GROUP_KEY_MAP:
    secret_id = os.environ.get('ACTION_NETWORK_SECRET_ID')
    raw_secret = SECRETSMANAGER.get_secret_value(SecretId=secret_id)
    ACTION_NETWORK_GROUP_KEY_MAP = json.loads(raw_secret['SecretString'])

AIRTABLE_PERSONAL_ACCESS_TOKEN = os.environ.get('AIRTABLE_PERSONAL_ACCESS_TOKEN')
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
if not AIRTABLE_PERSONAL_ACCESS_TOKEN and not AIRTABLE_BASE_ID:
    secret_id = os.environ['AIRTABLE_SECRET_ID']
    raw_secret = SECRETSMANAGER.get_secret_value(SecretId=secret_id)
    secret = json.loads(raw_secret['SecretString'])
    AIRTABLE_PERSONAL_ACCESS_TOKEN = secret['personal_access_token']
    AIRTABLE_BASE_ID = secret['base_id']

def event_time(time):
    try:
        return datetime.strptime(time['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
    except KeyError:
        return datetime.strptime(time['date'], '%Y-%m-%d').date()


def event_to_attachment(event, color='good'):
    htmlLink = event.get('htmlLink', 'https://calendar.google.com')
    summary = event.get('summary', '(No summary)')
    title = f'<{htmlLink}|{summary}>'
    text = event_to_text(event)
    attachment = {
        'color': color,
        'fallback': summary,
        'mrkdwn_in': ['pretext'],
        'text': text,
        'title': title,
    }
    return attachment


def event_to_text(event):
    # Get event time(s)
    start = event_time(event['start'])
    end = event_time(event['end'])
    if isinstance(start, datetime) and isinstance(end, datetime) \
            and start.date() == end.date():
        start = start.strftime('%b %-d from %-I:%M%p').lower().capitalize()
        end = end.strftime('%-I:%M%p').lower()
        text = f'{start} to {end}'
    elif isinstance(start, date) and isinstance(end, date) and start == end:
        start = start.strftime('%b %-d')
        text = f'{start}'
    elif start.year == end.year:
        start = start.strftime('%b %-d')
        end = end.strftime('%b %-d')
        text = f'{start} through {end}'
    else:
        start = start.strftime('%b %-d, %Y')
        end = end.strftime('%b %-d, %Y')
        text = f'{start} through {end}'

    # Get event location
    loc = event.get('location')
    if loc:
        mapsloc = urllib.parse.quote(loc)
        text += f' at <https://maps.google.com/maps?q={mapsloc}|{loc}>'

    return text


def slack_footer(user=None):
    footer = urllib.parse.urlparse(SLACK_FOOTER_URL).path.strip('/')
    footer = f'<{SLACK_FOOTER_URL}|{footer}>'
    if user:
        footer += f' | Posted by <@{user}>'
    return {'footer': footer}


def slack_message(results, channel=None, user=None):
    post = results.get('POST', {})
    put = results.get('PUT', {})
    delete = results.get('DELETE', {})
    created = [event_to_attachment(x, 'good') for x in post.values()]
    updated = [event_to_attachment(x, 'warning') for x in put.values()]
    deleted = [event_to_attachment(x, 'danger') for x in delete.values()]
    created_count = len(created)
    updated_count = len(updated)
    deleted_count = len(deleted)
    if created_count > 1:
        created[0]['pretext'] = \
            f'Added *{created_count}* facebook events to Google Calendar.'
    elif created_count == 1:
        created[0]['pretext'] = 'Added *1* facebook event to Google Calendar.'
    if updated_count > 1:
        updated[0]['pretext'] = \
            f'Updated *{updated_count}* facebook events on Google Calendar.'
    elif updated_count == 1:
        updated[0]['pretext'] = \
            'Updated *1* facebook event on Google Calendar.'
    if deleted_count > 1:
        deleted[0]['pretext'] = \
            f'Removed *{deleted_count}* facebook events from Google Calendar '\
            f'because the original facebook events no longer exist.'
    elif deleted_count == 1:
        deleted[0]['pretext'] = \
            f'Removed *1* facebook event from Google Calendar '\
            f'because the original facebook event no longer exists.'
    attachments = created + updated + deleted
    if any(attachments):
        attachments[-1].update(slack_footer(user))
    message = {
        'channel': channel,
        'attachments': attachments,
    }
    return message


def handler(event, *_):
    # Log Event
    print(f'EVENT {json.dumps(event)}')

    # Get args from event
    event = event or {}
    channel = event.get('channel') or SLACK_CHANNEL
    dryrun = event.get('dryrun') or False
    user = event.get('user')
    verbose = event.get('verbose') or False

    actionnetwork_events = []
    for actionnetwork_group, actionnetwork_key in ACTION_NETWORK_GROUP_KEY_MAP.items():
        if not actionnetwork_key: continue  # Skip any keys that have not yet been populated

        print(f"Fetching ActionNetwork events for: {actionnetwork_group}")
        actionnetwork = ActionNetwork(actionnetwork_key)
        actionnetwork_events.extend(actionnetwork.events())

    airtable = Airtable(AIRTABLE_PERSONAL_ACCESS_TOKEN, AIRTABLE_BASE_ID)
    airtable_events = airtable.events()

    differ = EventDiffer(
        events_from_source=actionnetwork_events,
        events_at_destination=airtable_events,
        verbose=verbose
    )
    differ.match_events()

    new_events = differ.events_to_add()

    updated_events = differ.events_to_update()
    changed_events = [e for e in updated_events if not e.removed]
    removed_events = [e for e in updated_events if e.removed]

    if verbose:
        print(f"All events retrieved from ActionNetwork: {actionnetwork_events}")
        print(f"New events: {new_events}")
        print(f"Changed events: {changed_events}")
        print(f"Removed events: {removed_events}")

    print(f"{len(actionnetwork_events)} events retrieved from ActionNetwork")
    print(f"{len(new_events)} new events")
    print(f"{len(changed_events)} changed events")
    print(f"{len(removed_events)} Removed events")

    if not dryrun:
        airtable.add_events(new_events)
        # Cancelled events are marked removed in Airtable by updating them
        airtable.update_events(changed_events + removed_events)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog = 'ActionNetwork',
                    description = 'Syncs events from ActionNetwork to Airtable')
    parser.add_argument('-s', '--sync', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    handler({
        'dryrun': not args.sync,
        'verbose': args.verbose,
        'user': 'U7P1MU20P',
        'channel': 'GB1SLKKL7',
    })
