import json
import os
import urllib
from datetime import datetime

import boto3

SNS = boto3.client('sns')

SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
SLACK_FOOTER_URL = os.environ['SLACK_FOOTER_URL']
SLACK_TOPIC_ARN = os.environ['SLACK_TOPIC_ARN']


def get_alarm_attachments(footer, ts):
    attachment = {
        'author_name': 'Google Calendar Sync',
        'text': 'Failed to sync facebook events with Google Calendar.',
        'color': 'danger',
        'footer': footer,
        'ts': ts,
    }
    return [attachment]


def get_ok_attachments(footer, ts):
    attachment = {
        'author_name': 'Google Calendar Sync',
        'text': 'Syncing facebook events is working again.',
        'color': 'good',
        'footer': footer,
        'ts': ts,
    }
    return [attachment]


def handle_record(record):
    # Parse SNS message JSON
    alarm = json.loads(record['Sns']['Message'])

    # Assemble footer for Slack message
    footer = urllib.parse.urlparse(SLACK_FOOTER_URL).path.strip('/')
    footer = f'<{SLACK_FOOTER_URL}|{footer}>'
    ts = alarm['StateChangeTime']
    ts = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f%z').timestamp()

    # Assemble message
    message = {'channel': SLACK_CHANNEL}

    if alarm['NewStateValue'] == 'ALARM':
        message['attachments'] = get_alarm_attachments(footer, ts)

    elif alarm['NewStateValue'] == 'OK':
        message['attachments'] = get_ok_attachments(footer, ts)

    post_message(message)


def post_message(message):
    # Post message to Slack via SNS
    print(f'MESSAGE {json.dumps(message)}')
    SNS.publish(
        TopicArn=SLACK_TOPIC_ARN,
        Message=json.dumps(message),
        MessageAttributes={
            'type': {
                'DataType': 'String',
                'StringValue': 'chat',
            },
            'id': {
                'DataType': 'String',
                'StringValue': 'postMessage',
            },
        },
    )


def handler(event, *_):
    print(f'EVENT {json.dumps(event)}')
    for record in event['Records']:
        handle_record(record)
