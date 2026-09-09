import enum


class EventStatus(str, enum.Enum):
    NEW = "new"
    PUBLISHED = "published"
    UNKNOWN = "unknown"


class SyncStatus(str, enum.Enum):
    NEVER_RUN = "never_run"
    OK = "ok"
    ERROR = "error"
