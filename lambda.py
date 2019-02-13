import json
import logging
import os
import urllib
from datetime import date
from datetime import datetime

import boto3
import facebook
from google.oauth2 import service_account
from googleapiclient import discovery

import fest

FACEBOOK_PAGE_ID = os.environ['FACEBOOK_PAGE_ID']
FACEBOOK_SECRET = os.environ['FACEBOOK_SECRET']
GOOGLE_CALENDAR_ID = os.environ['GOOGLE_CALENDAR_ID']
GOOGLE_SECRET = os.environ['GOOGLE_SECRET']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
SLACK_FOOTER_ICON = os.environ['SLACK_FOOTER_ICON']
SLACK_FOOTER_URL = os.environ['SLACK_FOOTER_URL']
SLACK_TOPIC_ARN = os.environ['SLACK_TOPIC_ARN']

# AWS Clients
SECRETSMANAGER = boto3.client('secretsmanager')
SNS = boto3.client('sns')

# Get facebook/Google secrets
FACEBOOK_PAGE_TOKEN = \
    SECRETSMANAGER.get_secret_value(SecretId=FACEBOOK_SECRET)['SecretString']
GOOGLE_SERVICE_ACCOUNT = json.loads(
    SECRETSMANAGER.get_secret_value(SecretId=GOOGLE_SECRET)['SecretString']
)
GOOGLE_CREDENTIALS = service_account.Credentials.from_service_account_info(
    GOOGLE_SERVICE_ACCOUNT
)

# Get facebook/Google clients
GRAPHAPI = facebook.GraphAPI(FACEBOOK_PAGE_TOKEN)
CALENDARAPI = discovery.build(
    'calendar', 'v3',
    cache_discovery=False,
    credentials=GOOGLE_CREDENTIALS,
)


def handler(event, *_):
    # Log Event
    eventstr = json.dumps(event)
    print(f'EVENT {eventstr}')

    # Get args from event
    event = event or {}
    cal_id = event.get('calendarId') or GOOGLE_CALENDAR_ID
    channel = event.get('channel') or SLACK_CHANNEL
    dryrun = event.get('dryrun') or False
    page_id = event.get('pageId') or FACEBOOK_PAGE_ID
    user = event.get('user')

    # Initialize facebook page & Google Calendar
    page = fest.FacebookPage(GRAPHAPI, page_id)
    gcal = fest.GoogleCalendar(CALENDARAPI, cal_id)
    page.logger.setLevel('INFO')
    gcal.logger.setLevel('INFO')

    # Sync
    sync = gcal.sync(page, time_filter='upcoming').execute(dryrun=dryrun)

    # Get Slack message
    message = slack_message(sync.responses, channel, user)

    # Post and return
    if not dryrun and any(message['attachments']):
        SNS.publish(TopicArn=SLACK_TOPIC_ARN, Message=json.dumps(message))
    return message


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
    message = {'channel': channel, 'attachments': attachments}
    return message


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
    loc = event.get('location')
    loc = f'<https://maps.google.com/maps?q={urllib.parse.quote(loc)}|{loc}>'
    start = event_time(event['start'])
    end = event_time(event['end'])
    if isinstance(start, datetime) and isinstance(end, datetime) \
            and start.date() == end.date():
        start = start.strftime('%b %-d from %-I:%M%p').lower().capitalize()
        end = end.strftime('%-I:%M%p').lower()
        text = f'{start} to {end} at {loc}'
    elif isinstance(start, date) and isinstance(end, date) and start == end:
        start = start.strftime('%b %-d')
        text = f'{start} at {loc}'
    elif start.year == end.year:
        start = start.strftime('%b %-d')
        end = end.strftime('%b %-d')
        text = f'{start} through {end} at {loc}'
    else:
        start = start.strftime('%b %-d, %Y')
        end = end.strftime('%b %-d, %Y')
        text = f'{start} through {end} at {loc}'
    return text


def event_time(time):
    try:
        return datetime.strptime(time['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
    except KeyError:
        return datetime.strptime(time['date'], '%Y-%m-%d').date()


def slack_footer(user=None):
    footer = urllib.parse.urlparse(SLACK_FOOTER_URL).path.strip('/')
    footer = f'<{SLACK_FOOTER_URL}|{footer}>'
    if user:
        footer += f' | Posted by <@{user}>'
    return {'footer': footer, 'footer_icon': SLACK_FOOTER_ICON}


if __name__ == '__main__':
    print(handler({
        'dryrun': True,
        'user': 'U7P1MU20P',
        'channel': 'GB1SLKKL7',
    }))
