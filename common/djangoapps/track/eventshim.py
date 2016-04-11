"""
EventShims that create
"""


class DottedPathMapping(object):
    """
    Dictionary-like object for creating keys of dotted paths.

    If a key is created that ends with a dot, it will be treated as a path
    prefix.  Any value whose prefix matches the dotted path can be used
    as a key for that value, but only the most specific match will
    be used.
    """

    def __init__(self, registry=None):
        self._match_registry = {}
        self._prefix_registry = {}
        self.update(registry or {})

    def __contains__(self, key):
        try:
            _ = self[key]
            return True
        except KeyError:
            return False

    def __getitem__(self, key):
        if key in self._match_registry:
            return self._match_registry[key]
        for prefix in sorted(self._prefix_registry, reverse=True):
            if key.startswith(prefix):
                return self._prefix_registry[key]
        raise KeyError('Key {} not found in {}'.format(key, type(self)))

    def __setitem__(self, key, value):
        if key.endswith('.'):
            self._prefix_registry[key] = value
        else:
            self._match_registry[key] = value

    def __delitem__(self, key):
        if key.endswith('.'):
            del self._prefix_registry[key]
        else:
            del self._match_registry[key]

    def get(self, key, default=None):
        try:
            self[key]
        except KeyError:
            return default

    def update(self, dict_):
        for key, value in dict_:
            self[key] = value

    def keys(self):
        return self._match_registry.keys() + self._prefix_registry.keys()

class EventShimMeta(type):
    """
    Adds a registry to the base of a class hierarchy, and adds descendant classes
    to the registry, if they define a `shim_name` attribute
    """

    def __new__(mcs, name, bases, class_dict):
        # pylint: disable=protected-access
        cls = type.__new__(mcs, name, bases, class_dict)
        if bases == (dict,):
            cls._registry = DottedPathMapping()
            mcs.base = cls
        if 'shim_name' in class_dict:
            mcs.base._registry[class_dict['shim_name']] = cls
        return cls


class EventShim(dict):
    """
    Creates a shim to modify analytics events based on event type.

    To use the event shim, instantiate it using the `EventShim.create_shim()`
    classmethod with the event dictionary as the sole argument, and then call
    `event_shim.shim()` to modify the shim to the format required for output.

    Custom shims will want to override some or all of the following values

    Attributes:

        shim_name:
            This is the name of the event you want to shim.  If the name
            ends with a `'.'`, it will be treated as a *prefix shim*.  All
            other names denote *exact shims*.

            A *prefix shim* will handle any event whose name begins with the
            name of the prefix shim.  Only the most specific match will be
            used, so if a shim exists with a name of `'edx.ui.lms.'` and
            another shim has the name `'edx.ui.lms.sequence.'` then an event
            called `'edx.ui.lms.sequence.tab_selected'` will be handled by the
            `'edx.ui.lms.sequence.'` shim.

            An *exact shim* will only handle events whose name matches name of
            the shim exactly.

            Exact shims always take precedence over prefix shims.

            Shims without a name will not be added to the registry, and cannot
            be accessed via the `EventShim.create_shim()` classmethod.

        is_legacy_event:
            If an event is a legacy event, it needs to set event_type to
            the legacy name for the event, and may need to set certain
            event fields to maintain backward compatiblity.  If an event
            needs to provide legacy support in some contexts, `is_legacy_event`
            can be defined as a property to add dynamic behavior.

            Default: False

        legacy_event_type:
            If the event is or can be a legacy event, it should define
            the legacy value for the event_type field here.

    Processing methods.  Override these to provide the behavior needed for your
    particular EventShim:

        self.process_legacy_fields():

            This method should modify the event payload in any way necessary to
            support legacy event types.  It will only be run if
            `is_legacy_event` returns a True value.

        self.process_event()
            TODO:
    """
    __metaclass__ = EventShimMeta

    # factory method
    @classmethod
    def create_event_shim(cls, event):
        """
        Create a shimmed version of the given event.

        If no shim is registered to handle the event, this raises a KeyError.
        """
        name = event.get('name')
        return cls._registry[name](event)  # pylint: disable=no-member

    # Abstract Properties

    is_legacy_event = False

    @property
    def legacy_event_type(self):
        raise NotImplementedError

    # Convenience properties

    @property
    def name(self):
        return self['name']

    @property
    def context(self):
        return self['context']

    @property
    def event(self):
        return self['event']

    # Shimming methods

    def shim(self):
        if self.is_legacy_event:
            self.set_legacy_event_type()
            self.process_legacy_fields()
        self.process_event()

    def set_legacy_event_type(self):
        self['event_type'] = self.legacy_event_type

    def process_legacy_fields(self):
        pass

    def process_event(self):
        pass


class TabSelectedEventShim(EventShim):

    shim_name = u'edx.ui.lms.sequence.tab_selected'
    is_legacy_event = True
    legacy_event_type = u'seq_goto'

    def process_legacy_fields(self):
        self.event['old'] = self.event['current_tab']
        self.event['new'] = self.event['target_tab']


class _BaseLinearSequenceEventShim(EventShim):

    offset = None

    @property
    def is_legacy_event(self):
        return not self.crosses_boundary()

    def process_legacy_fields(self):
        self.event['old'] = self.event['current_tab']
        self.event['new'] = self.event['current_tab'] + self.offset

    def crosses_boundary(self):
        raise NotImplementedError


class NextSelectedEventShim(_BaseLinearSequenceEventShim):

    shim_name = u'edx.ui.lms.sequence.next_selected'
    offset = 1
    legacy_event_type = 'seq_next'

    def crosses_boundary(self):
        return self.event['current_tab'] == self.event['tab_count']


class PreviousSelectedEventShim(_BaseLinearSequenceEventShim):

    shim_name = u'edx.ui.lms.sequence.previous_selected'
    offset = -1
    legacy_event_type = 'seq_prev'

    def crosses_boundary(self):
        return self.event['current_tab'] == 1
