from log import *
from config import *
from events.models import BaseEvent


def publish_event(event):
    if not isinstance(event, BaseEvent):
        error("Event is not instance of event")
        return
