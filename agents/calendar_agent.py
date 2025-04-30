import datetime
from uagents import Agent, Context, Protocol
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from models.calendar_intent import CalendarIntent

calendar_agent = Agent(
    name="calendar_agent",
    seed="calendar secret",
    port=8001,
    endpoint=["http://localhost:8001/submit"]
)

calendar_protocol = Protocol("calendar_protocol")

@calendar_protocol.on_message(model=CalendarIntent)
async def handle_intent(ctx: Context, sender: str, intent: CalendarIntent):
    try:
        creds = Credentials(
            token=intent.access_token,
            refresh_token=intent.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=intent.client_id,
            client_secret=intent.client_secret,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("calendar", "v3", credentials=creds)

        if intent.type == "create_event" and intent.status != "confirmed":
            start = intent.start_time
            end = intent.end_time
            events = service.events().list(
                calendarId="primary",
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime"
            ).execute().get("items", [])

            if events:
                conflict_event = events[0]
                intent.message = f"❌ Conflict: {conflict_event['summary']} already scheduled at this time."
                intent.status = "conflict"
            else:
                intent.message = "✅ No conflict. Please confirm to book."
                intent.status = "pending"

        elif intent.type == "create_event" and intent.status == "confirmed":
            body = {
                "summary": intent.title,
                "start": {"dateTime": intent.start_time, "timeZone": "America/Los_Angeles"},
                "end": {"dateTime": intent.end_time, "timeZone": "America/Los_Angeles"},
            }
            created = service.events().insert(calendarId="primary", body=body).execute()
            intent.message = f"📅 Event created: {created.get('htmlLink')}"

        elif intent.type == "read_events":
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events = service.events().list(calendarId='primary', timeMin=now, maxResults=5).execute().get('items', [])
            intent.message = "\n".join([f"{e['summary']} at {e['start']['dateTime']}" for e in events])

        elif intent.type == "delete_event":
            service.events().delete(calendarId='primary', eventId=intent.event_id).execute()
            intent.message = "🗑️ Event deleted."

        elif intent.type == "update_event":
            body = {
                "summary": intent.title,
                "start": {"dateTime": intent.start_time, "timeZone": "America/Los_Angeles"},
                "end": {"dateTime": intent.end_time, "timeZone": "America/Los_Angeles"},
            }
            updated = service.events().update(calendarId='primary', eventId=intent.event_id, body=body).execute()
            intent.message = f"🔁 Event updated: {updated.get('htmlLink')}"

        else:
            intent.message = f"⚠️ Unknown intent type: {intent.type}"

        await ctx.send(sender, intent)

    except Exception as e:
        intent.message = f"❌ Error: {str(e)}"
        await ctx.send(sender, intent)

calendar_agent.include(calendar_protocol)

if __name__ == "__main__":
    calendar_agent.run()
