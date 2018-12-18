import json
import os
import urllib
from datetime import datetime

import boto3

SLACK_AUTHOR_ICON = os.environ['SLACK_AUTHOR_ICON']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
SLACK_FOOTER_ICON = os.environ['SLACK_FOOTER_ICON']
SLACK_FOOTER_URL = os.environ['SLACK_FOOTER_URL']
SLACK_TOPIC_ARN = os.environ['SLACK_TOPIC_ARN']
SNS = boto3.client('sns')


def handler(event, *_):
    for record in event['Records']:
        alarm = json.loads(record['Sns']['Message'])
        footer = urllib.parse.urlparse(SLACK_FOOTER_URL).path.strip('/')
        footer = f'<{SLACK_FOOTER_URL}|{footer}>'
        ts = alarm['StateChangeTime']
        ts = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f%z').timestamp()
        if alarm['NewStateValue'] == 'ALARM':
            message = json.dumps({
                'channel': SLACK_CHANNEL,
                'attachments': [
                    {
                        'author_name': 'Google Calendar Sync',
                        'author_icon': SLACK_AUTHOR_ICON,
                        'text':
                            'Failed to sync facebook events with Google '
                            'Calendar after several attempts.',
                        'color': 'danger',
                        'footer': footer,
                        'footer_icon': SLACK_FOOTER_ICON,
                        'ts': ts,
                    },
                ],
            })
            print(f'MESSAGE {message}')
            SNS.publish(TopicArn=SLACK_TOPIC_ARN, Message=message)
        elif alarm['NewStateValue'] == 'OK':
            message = json.dumps({
                'channel': SLACK_CHANNEL,
                'attachments': [
                    {
                        'author_name': 'Google Calendar Sync',
                        'author_icon': SLACK_AUTHOR_ICON,
                        'text': 'Syncing facebook events is working again.',
                        'color': 'good',
                        'footer': footer,
                        'footer_icon': SLACK_FOOTER_ICON,
                        'ts': ts,
                    },
                ],
            })
            print(f'MESSAGE {message}')
            SNS.publish(TopicArn=SLACK_TOPIC_ARN, Message=message)
