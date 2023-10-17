from abc import ABC
from datetime import datetime, timedelta

from pytz import timezone

class Event(ABC):
    """Abstract base class for Event types.

    Event types provide a standardized interface for accessing common event
    attributes on top of the raw event format as defined by the various event
    systems' APIs.

    Event types do not need to implement every event attribute or property;
    they can be expanded as necessary for their application. However, each type
    should only define common event properties that can be interchanged with
    those of other event types.
    """

    # Collection of names of fields which must be set on the event object
    # in order for it to be valid for pushing to the API for this event type
    REQUIRED_FIELD_NAMES = set()

    # Collection of names of fields which are computed by the event system
    # and therefor should not be pushed via the API
    DERIVED_FIELD_NAMES = {
        'updated_at',
    }

    # The name of the field to use as the primary ID for this event type
    PRIMARY_ID_NAME = None

    def __init__(self, raw_event=None):
        """Create an empty Event object, or create an Event representation of
        raw event info.

        :param dict raw_event: The event info dictionary in raw format (as
            pulled from the respective events service API), defaults to None
        :type raw_event: dict, optional
        """
        if raw_event:
            self.raw = raw_event
        else:
            self.raw = {}

    def __repr__(self):
        primary_id = getattr(self, self.PRIMARY_ID_NAME)
        return super().__repr__().replace(
            "object", f"{primary_id}|'{self.title}'"
        )

    @property
    def primary_id(self):
        return getattr(self, self.PRIMARY_ID_NAME)

    @primary_id.setter
    def primary_id(self, value):
        if self.primary_id is not None: raise "Cannot change Primary ID."
        return setattr(self, self.PRIMARY_ID_NAME, value)

    def lookup(self, *keys):
        """A null-safe lookup to find nested attributes in the raw event.

        :params str keys: keys indicating a location to look up in the raw
            event. Each successive key will index into a nested dictionary.
        :return: The value at the given location, or None if no such value
            exists or if the key at any intermediary stage does not exist.
        """
        value = self.raw
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        return value

    def set(self, value, *keys):
        """Sets a value in the raw event data.

        :param object value: The value to set.
        :params str keys: keys indicating a location to store the value in the
            raw event. Each successive key will index into a nested dictionary.
        """
        if len(keys) == 0:
            return

        parent_location = self.raw
        for key in keys[:-1]:
            if key not in parent_location:
                parent_location[key] = {}
            parent_location = parent_location[key]

        parent_location[keys[-1]] = value

    @classmethod
    def build(cls, fields):
        """Construct a new event with the given field values.

        :param fields: mapping of field names to field values that the new
            event will be built with
        :type fields: dict
        :raises ValueError: if required fields are not given.
        :return: A new event object with all given fields set.
        :rtype: Event
        """
        missing_fields = cls.REQUIRED_FIELD_NAMES - fields.keys()
        if missing_fields:
            raise ValueError(f"REQUIRED_FIELD_NAMES missing: {missing_fields}")

        new_event = cls()
        for field, value in fields.items():
            if hasattr(new_event, field):
                setattr(new_event, field, value)
            else:
                print(f"Warning: {field} not present in {cls}")
        return new_event

    @classmethod
    def event_fields(cls):
        """Get the names of all properties belonging to a specific event class.

        :return: set of property names
        :rtype: set
        """
        return set(dir(cls)) - set(dir(Event))

    def translate_to(self, new_class):
        """Translate the event object to a different event format.

        :param new_class: the Event class to translate the event into
        :type new_class: class of Event
        :return: new event with all fields carried over (as  permitted)
        :rtype: Event
        """
        new_event_values = {
            field: getattr(self, field)
            for field in self.__class__.event_fields()
            if field not in new_class.DERIVED_FIELD_NAMES
        }
        return new_class.build(new_event_values)

    @classmethod
    def to_datetime(cls, raw_time):
        """Translates an event type's native time format into a python datetime.

        We define helpers in the base Event class to prevent the subclass
        helpers won't be counted as event_fields.

        :param raw_time: an object representing a time value, in whatever format
            the event type uses to store time values
        :return: a python datetime object representing the same time
        :rtype: datetime
        """
        raise NotImplementedError

    @classmethod
    def from_datetime(cls, dt):
        """Translates a datetime into the event type's native time format.

        We define helpers in the base Event class to prevent the subclass
        helpers won't be counted as event_fields.

        :param dt: a python datetime object representing a time
        :return: an object representing a time value, in whatever format
            the event type uses to store time values
        """
        raise NotImplementedError


class AirtableEvent(Event):
    REQUIRED_FIELD_NAMES = {
        'actionnetwork_id',
        'title',
        'description',
    }
    PRIMARY_ID_NAME = 'airtable_id'

    @property
    def airtable_id(self):
        return self.lookup('id')

    @airtable_id.setter
    def airtable_id(self, airtable_id):
        self.set(airtable_id, 'id')

    @property
    def updated_at(self):
        return self.lookup('fields', 'modified')

    @property
    def actionnetwork_id(self):
        return self.lookup('fields', 'actionnetwork_id')

    @actionnetwork_id.setter
    def actionnetwork_id(self, actionnetwork_id):
        self.set(actionnetwork_id, 'fields',  'actionnetwork_id')

    @property
    def title(self):
        return self.lookup('fields', 'Event Title')

    @title.setter
    def title(self, title):
        self.set(title, 'fields', 'Event Title')

    @property
    def description(self):
        return self.lookup('fields', 'Description')

    @description.setter
    def description(self, description):
        self.set(description, 'fields', 'Description')

    @property
    def start(self):
        return AirtableEvent.to_datetime(self.lookup('fields', 'Start Time'))

    @start.setter
    def start(self, start):
        start_str = AirtableEvent.from_datetime(start)
        return self.set(start_str, 'fields', 'Start Time')

    @property
    def end(self):
        return AirtableEvent.to_datetime(self.lookup('fields', 'End Time'))

    @end.setter
    def end(self, end):
        return self.set(AirtableEvent.from_datetime(end), 'fields', 'End Time')

    @classmethod
    def to_datetime(cls, raw_time):
        # This function must be null-safe because raw_time will be None if
        # we are creating the object from scratch.
        if raw_time is None:
            dt = None
        else:
            dt = datetime.fromisoformat(raw_time)
        return dt

    @classmethod
    def from_datetime(cls, dt):
        return dt.isoformat()

    @property
    def location(self):
        return self.lookup('fields', 'Location')

    @location.setter
    def location(self, location):
        return self.set(location, 'fields', 'Location')

class ActionNetworkEvent(Event):
    PRIMARY_ID_NAME = 'actionnetwork_id'

    @property
    def actionnetwork_id(self):
        for identifier in self.lookup('identifiers'):
            if identifier.startswith('action_network:'):
                return identifier[len('action_network:'):]

    @property
    def updated_at(self):
        return self.lookup('modified_date')

    @property
    def title(self):
        return self.lookup('title')

    @property
    def description(self):
        return self.lookup('description')

    @property
    def start(self):
        raw_start = self.lookup('start_date')
        return ActionNetworkEvent.to_datetime(raw_start)

    @property
    def end(self):
        raw_end = self.lookup('end_date')
        if raw_end is None:
            end = self.start + timedelta(hours=1)
        else:
            end = ActionNetworkEvent.to_datetime(raw_end)
        return end

    @classmethod
    def to_datetime(cls, raw_time):
        # ActionNetwork seems to give us timestamps with a trailing 'Z' which
        # indicates UTC, but the times are whatever the user entered, verbatim,
        # regardless of timezone. Strip the Z to get valid ISO
        naieve_time = datetime.fromisoformat(raw_time[:-1])
        # Assume that the user entered eastern time. If this turns out to
        # be unreliable, we can look into deriving timezone from location.
        # If an event is virtual (no location) ActionNetwork requires the
        # user to enter a timezone manually, but this does not seem to
        # appear in the API response
        return timezone('US/Eastern').localize(naieve_time)

    @property
    def location(self):
        loc = self.lookup('location')

        venue = loc['venue'] if 'venue' in loc else ''
        addr = ' '.join(loc['address_lines']) if 'address_lines' in loc else ''
        city = loc['locality'] if 'locality' in loc else ''
        state = loc['region'] if 'region' in loc else ''
        zipcode = loc['postal_code'] if 'postal_code' in loc else ''

        str_loc = f'{venue}, {addr}, {city} {state}, {zipcode}'

        # I didn't find any flag that indicates the event is online.
        # Online events seemed to have the same lat/long, so we tried using that,
        # but it wasn't always true, so some of our online event locations were just commas.
        # Instead we'll try checking if they have no address.
        if venue == '' and addr == '' and city == '' and state == '' and zipcode == '':
            str_loc = 'Online'

        return str_loc


class EventDiffer():
    """Computes the difference between sets of events of different classes.

    EventDiffer produces change sets, or event lists which, if applied to the
    'destination' system, will bring its' event store into sync with the
    'source' list.

    Note: We differentiate the lists of events, and the classes of those events,
    by 'source' vs. 'destination'. While these event lists could be arbitrary,
    these names mirror our main use-case where the event lists/classes reflect
    the state of events stored in 3rd party systems. The names also the
    direction we compute the diff in - we are computing the diff relative to
    the existing events in the 'destination' list.
    """
    def __init__(
        self,
        events_from_source,
        events_at_destination,
        destination_class=AirtableEvent
    ):
        """Create an EventDiffer.

        :param events_from_source: list of events to generate the diff for
        :type events_from_source: List[Event]
        :param events_at_destination: the baseline events to compare against
        :type events_at_destination: List[Event]
        :param destination_class: The class to build new destination events
            with, in case there are no existing destination events to match
            against. defaults to AirtableEvent
        :type destination_class: class, optional
        """
        self.events_from_source = events_from_source
        self.source_class = self._event_class(events_from_source)

        self.events_at_destination = events_at_destination
        if events_at_destination:
            self.destination_class = self._event_class(events_at_destination)
        else:
            self.destination_class = destination_class

        # We expect that the destination events store the primary ID value from
        # the source events as a common ID that can be used to compare events
        self.common_id_name = self.source_class.PRIMARY_ID_NAME

    @staticmethod
    def _event_class(events):
        """Determine the event type for a list of events.

        :param events: list of events to evaluate
        :type events: List[Event]
        :raises ValueError: if there are multiple event types found
        :return: the type of the events
        :rtype: class
        """
        unique_types = {e.__class__ for e in events}
        if len(unique_types) > 1:
            raise ValueError(
                "Expected a single event class per event list - multiple found"
            )
        return unique_types.pop()

    def _events_by_common_id(self, events):
        return {
            getattr(e, self.common_id_name): e
            for e in events
            # Ignore events with no common ID value
            # (such as events entered manually into the destination system)
            if getattr(e, self.common_id_name) is not None
        }

    def diff_events(self):
        """Compute the diffs and store in instance variables.

        Must be run before accessing the change sets (events_to_add, etc).
        """
        source_events = self._events_by_common_id(self.events_from_source)
        dest_events = self._events_by_common_id(self.events_at_destination)

        not_in_destination = []
        updated_pairs = []
        for common_id, source_event in source_events.items():
            if common_id in dest_events:
                dest_event = dest_events.pop(common_id)
                if dest_event.updated_at < source_event.updated_at:
                    updated_pairs.append([dest_event, source_event])
            else:
                not_in_destination.append(source_event)

        self.new_source_events = not_in_destination
        self.updated_source_dest_event_pairs = updated_pairs
        self.dest_events_removed_from_source = list(dest_events.values())

    def events_to_add(self):
        """Events that do not exist in the destination and can be added to
        bring it into alignment with the source.

        :return: list of destination-type events
        """
        return [
            source_event.translate_to(self.destination_class)
            for source_event in self.new_source_events
        ]

    def events_to_update(self):
        """Events that exist in both the source and destination and can be
        updated in the destination to bring it into alignment with the source.

        :return: list of destination-type events
        """
        events_to_update = []
        for dest_event, source_event in self.updated_source_dest_event_pairs:
            event = source_event.translate_to(self.destination_class)
            event.primary_id = dest_event.primary_id
            events_to_update.append(event)
        return events_to_update

    def events_to_delete(self):
        """Events that do not exist in the source and can be removed from the
        destination to bring it into alignment with the source.

        :return: list of destination-type events
        """
        return self.dest_events_removed_from_source
