# 🤖 AI Calendar Assistant

Schedule Google Calendar events with natural language.

This project combines the power of LLMs, agent-based architecture, and modern web interfaces to allow users to type freeform event requests like:

> “Lunch with Alex tomorrow at 1pm”

And the system interprets, converts, and sends the request to a Fetch.ai autonomous agent, which (simulated or real) handles scheduling the event.

---

## 🌐 Live Demo (Optional)

**Coming soon**: Hosted version on [Streamlit Cloud](https://streamlit.io/cloud)

---

Powered by:

- 🧠 OpenAI (LLM for intent parsing)
- 🤖 Fetch.ai uAgents (agent logic and message handling)
- 🗓️ Google Calendar API
- 🎛️ Streamlit (user interface)

---

## 🚀 Features

- Converts natural language into structured JSON using GPT-4
- Sends structured messages to a calendar agent hosted on Agentverse
- The agent parses the request and (simulated) handles scheduling logic
- Streamlit-based UI for easy interaction and demo

---

## 🛠️ Tech Stack

- Python
- OpenAI API
- Fetch.ai Agentverse
- Streamlit
- Google Calendar API (OAuth2)

---

## 🧪 How to Run Locally

### Clone the repo

```bash
git clone https://github.com/your-username/ai-calendar-assistant.git
cd ai-calendar-assistant
```
