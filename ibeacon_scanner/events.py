from datetime import datetime
from event.models import BaseEvent


class IBeaconChange(BaseEvent):

    def __init__(self, data):
        super(IBeaconChange, self).__init__()
        self.actor = "ibeacon_scanner"
        self.target = "system"
        self.data = data
        self.time = datetime.now()
        self.type = "IBEACON_CHANGE"


class IBeaconRead(BaseEvent):

    def __init__(self, data):
        super(IBeaconRead, self).__init__()
        self.actor = "ibeacon_scanner"
        self.target = "system"
        self.data = data
        self.time = datetime.now()
        self.type = "IBEACON_READ"
    