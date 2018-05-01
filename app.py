import logging
import os

import click
import fest.cloud
import fest.graph
import fest.tribe
import requests

DEADMANSSNITCH_URL = os.getenv('DEADMANSSNITCH_URL')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger('fest.graph.GraphAPI').setLevel('DEBUG')
logging.getLogger('fest.cloud.CalendarAPI').setLevel('DEBUG')
logging.getLogger('fest.tribe.TribeAPI').setLevel('DEBUG')


def from_facebook_with_custom_fields(facebook_event):
    post = fest.tribe.WordPressPost.from_facebook(facebook_event)
    post.set_custom_field('body', 'View our list of events and get involved.')
    post.set_custom_field('header', 'Want to check out other events?')
    post.set_custom_field('link_text', 'View Events')
    post.set_custom_field('link_url', 'events')
    return post


fest.graph.FacebookEvent.to_wordpress = from_facebook_with_custom_fields


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(fest.__version__, '-v', '--version')
@click.option('-d', '--dryrun',
              help='Do not execute sync',
              is_flag=True)
@click.option('-f', '--force',
              help='Force patching without checking digest',
              is_flag=True)
def main(dryrun=None, force=None):
    """ Synchronize facebook with Google Calendar & WordPress. """
    # Connect to facebook/Google/WordPress
    graph = fest.graph.GraphAPI.from_env()
    cloud = fest.cloud.CalendarAPI.from_env()
    tribe = fest.tribe.TribeAPI.from_env()

    # BostonDSA facebook page
    page = graph.get_page(FACEBOOK_PAGE_ID)

    # BostonDSA Google calendar
    gcal = cloud.get_calendar(GOOGLE_CALENDAR_ID)

    # Get upcoming events
    upcoming = page.get_events(time_filter='upcoming')

    # Get canceled events
    canceled = page.get_events(time_filter='upcoming',
                               event_state_filter=['canceled'])

    # Event dictionary
    source_events = {'upcoming': upcoming, 'canceled': canceled}

    # Sync events
    gcal.sync_events(source_events, force=force, dryrun=dryrun)
    tribe.sync_events(source_events, force=force, dryrun=dryrun)

    # Report to Dead Man's Snitch
    requests.get(DEADMANSSNITCH_URL)


if __name__ == '__main__':
    main()
