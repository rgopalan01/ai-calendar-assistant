from uagents import Model

class CalendarIntent(Model):
    type: str  # create_event, read_events, update_event, delete_event
    title: str | None = None
    start_time: str | None = None  # ISO format
    end_time: str | None = None
    event_id: str | None = None  # for update/delete
    message: str | None = None  # response message from calendar agent
    access_token: str | None = None  # user-specific token
    refresh_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    status: str | None = None  # pending, conflict, confirmed
