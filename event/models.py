
class BaseEvent(object):

    def __init__(self):
        self.type = None
        self.time = None
        self.data = None
        self.target = None
        self.actor = None

    def to_json(self):
        return {
            "actor": self.actor,
            "target": self.target,
            "data": self.data,
            "time": self.time.isoformat(),
            "type": self.type,
        }

    def __repr__(self):
        return f"BaseEvent(" + \
            f"actor='{self.actor}', " + \
            f"target='{self.target}', " + \
            f"time={self.time}, " + \
            f"type={self.type}, " + \
            f"data={self.data}" + \
        ")"
