import streamlit as st
import openai
import requests
import json
from urllib.parse import urlencode
from models.calendar_intent import CalendarIntent

st.set_page_config(page_title="AI Calendar Assistant")

GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8501"
SCOPES = "https://www.googleapis.com/auth/calendar"

st.title("📅 AI Calendar Assistant")

st.sidebar.subheader("🔑 OpenAI API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
if api_key:
    openai.api_key = api_key
else:
    st.stop()

st.sidebar.subheader("🔐 Login with Google")
if "access_token" not in st.session_state:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent"
    }
    login_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    st.sidebar.markdown(f"[Login with Google]({login_url})", unsafe_allow_html=True)
else:
    st.sidebar.success("✅ Logged in")

query_params = st.query_params
if "code" in query_params and "access_token" not in st.session_state:
    code = query_params["code"][0]
    token_url = "https://oauth2.googleapis.com/token"
    res = requests.post(token_url, data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    })
    if res.ok:
        tokens = res.json()
        st.session_state.access_token = tokens["access_token"]
        st.session_state.refresh_token = tokens["refresh_token"]
        st.experimental_set_query_params()
        st.rerun()
    else:
        st.error(f"OAuth failed: {res.text}")

if "access_token" in st.session_state:
    st.subheader("🧠 Talk to your Calendar Assistant")
    user_input = st.text_input("What would you like to schedule or check?")

    if st.button("Send to AI") and user_input:
        prompt = f"Convert this into a calendar intent JSON:\n'{user_input}'\nFormat: {{type, title, start_time, end_time}}."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response["choices"][0]["message"]["content"]
        st.code(content, language="json")

        try:
            parsed = CalendarIntent.parse_raw(content)
            parsed.access_token = st.session_state.access_token
            parsed.refresh_token = st.session_state.refresh_token
            parsed.client_id = GOOGLE_CLIENT_ID
            parsed.client_secret = GOOGLE_CLIENT_SECRET
            requests.post("http://localhost:8000/submit", json=parsed.dict())
            st.success("📤 Sent to calendar agent!")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

    st.divider()

    st.subheader("📥 Confirm Suggested Event")
    try:
        with open("pending_intent.json", "r") as f:
            pending = json.load(f)
        st.info(pending["message"])
        if st.button("✅ Confirm and Book"):
            requests.post("http://localhost:8000/submit", json=pending)
            st.success("Confirmed! Event booking submitted.")
    except FileNotFoundError:
        st.write("No pending event suggestions yet.")