from uagents import Agent, Context, Protocol
from models.calendar_intent import CalendarIntent
import requests
import json

frontend_agent = Agent(
    name="frontend_agent",
    seed="frontend secret",
    port=8000,
    endpoint=["http://localhost:8000/submit"]
)

frontend_protocol = Protocol("calendar_protocol")

@frontend_protocol.on_message(model=CalendarIntent)
async def display_response(ctx: Context, sender: str, intent: CalendarIntent):
    ctx.logger.info(f"📩 Response: {intent.message}")
    if intent.status == "pending":
        ctx.logger.info("⏳ Awaiting user confirmation...")
        confirm_intent = intent.copy()
        confirm_intent.status = "confirmed"
        # Save for UI confirmation button
        with open("pending_intent.json", "w") as f:
            json.dump(confirm_intent.dict(), f)

frontend_agent.include(frontend_protocol)

if __name__ == "__main__":
    frontend_agent.run()
