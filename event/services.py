from log import *
from config import EVENTS_TO_OMIT
from event.models import BaseEvent


def publish_event(event):
    if not isinstance(event, BaseEvent):
        error("Event is not instance of event")
        return
    event_class = event.__class__.__name__
    events_to_omit = EVENTS_TO_OMIT.replace(" ", "").split(",")
    if event_class in events_to_omit:
        return
    info(f"Publishing event '{event.to_json()}'")
        
