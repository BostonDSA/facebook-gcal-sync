import logging
import os

import click
import fest.cloud
import fest.graph
import fest.tribe
import requests

DEADMANSSNITCH_URL = os.getenv('DEADMANSSNITCH_URL')
GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger('fest.graph.GraphAPI').setLevel('DEBUG')
logging.getLogger('fest.cloud.CalendarAPI').setLevel('DEBUG')
logging.getLogger('fest.tribe.TribeAPI').setLevel('DEBUG')


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(fest.__version__, '-v', '--version')
@click.option('-d', '--dryrun',
              help='Do not execute sync',
              is_flag=True)
@click.option('-f', '--force',
              help='Force patching without checking digest',
              is_flag=True)
def main(dryrun, force):
    # Connect to facebook/Google/WordPress
    graph = fest.graph.GraphAPI.from_env()
    cloud = fest.cloud.CalendarAPI.from_env()
    tribe = fest.tribe.TribeAPI.from_env()

    # Sync BostonDSA events
    page = graph.get_page('BostonDSA')
    events = page.get_events(time_filter='upcoming')
    cloud.sync_events(GOOGLE_CALENDAR_ID, events, force=force, dryrun=dryrun)
    tribe.sync_events(events, force=force, dryrun=dryrun)

    # Report to Dead Man's Snitch
    requests.get(DEADMANSSNITCH_URL)


if __name__ == '__main__':
    main()
