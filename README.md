# 🧠 AI Calendar Assistant (Agentic, Multi-user)

This project is a fully agentic calendar scheduling assistant using [Fetch.ai](https://fetch.ai) `uAgents`, [Streamlit](https://streamlit.io) for the UI, OpenAI for natural language interpretation, and Google Calendar API for calendar operations.

---

## ⚙️ Architecture

- **streamlit_ui.py** – Streamlit app for user login, prompt submission, and confirmation interface
- **frontend_agent.py** – Formats and sends `CalendarIntent` to backend
- **calendar_agent.py** – Handles scheduling logic, conflict checking, and event creation via Google Calendar
- **calendar_intent.py** – Shared message schema

---

## 🚀 Features

- 🧠 Natural language to intent conversion using OpenAI
- 🔐 Per-user Google Calendar login (OAuth2)
- 🤖 Agentic backend with automatic conflict checking
- ✅ Human-in-the-loop: event is only booked on user confirmation
- 📨 Multi-turn agent messaging using Fetch.ai's protocol system

---

## 📦 Setup

1. Clone the repo:

```bash
git clone https://github.com/your-username/calendar-agentic-assistant
cd calendar-agentic-assistant
```

2. Create `.streamlit/secrets.toml`:

```toml
GOOGLE_CLIENT_ID = "your-client-id"
GOOGLE_CLIENT_SECRET = "your-client-secret"
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the agents:

```bash
python agents/calendar_agent.py
python agents/frontend_agent.py
```

5. Start the frontend:

```bash
streamlit run streamlit_ui.py
```

---

## 🛡️ Environment Variables (used in secrets.toml)

- `GOOGLE_CLIENT_ID` – From Google Cloud Console (OAuth credentials)
- `GOOGLE_CLIENT_SECRET` – From Google Cloud Console

---

## 💡 Example Prompt

> "Schedule a meeting with Alex tomorrow at 3PM"

The LLM will convert this into a structured JSON intent. The calendar agent checks for conflicts and asks for confirmation if the slot is free.

---

## 🧠 Extendable Ideas

- Add group availability negotiation
- Use persistent storage for confirmed intent history
- Add Slack or SMS notification integration
- Support for recurring events

---

Built with ❤️ using Fetch.ai, Streamlit, OpenAI, and Python.
