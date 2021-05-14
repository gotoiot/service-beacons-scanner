from log import *
from config import *
from event.models import BaseEvent


BLACK_LIST_EVENTS = [
    'IBeaconRead'
]


def publish_event(event):
    if not isinstance(event, BaseEvent):
        error("Event is not instance of event")
        return
    event_class = event.__class__.__name__
    if event_class in BLACK_LIST_EVENTS:
        return
    info(f"Publishing event '{str(event)}'")
        
