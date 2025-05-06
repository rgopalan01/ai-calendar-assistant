import streamlit as st
import json
import os
import requests
import datetime
import openai
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from models.calendar_intent import CalendarIntent

# Page configuration
st.set_page_config(
    page_title="AI Calendar Assistant",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="expanded",
)

# CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .success {
        color: green;
        font-weight: bold;
    }
    .error {
        color: red;
        font-weight: bold;
    }
    .pending {
        color: orange;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize OAuth variables
if "google_auth_state" not in st.session_state:
    st.session_state.google_auth_state = None
if "credentials" not in st.session_state:
    st.session_state.credentials = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "openai_key" not in st.session_state:
    st.session_state.openai_key = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_intent" not in st.session_state:
    st.session_state.pending_intent = None

# Function to create OAuth flow
def create_flow():
    # Get the base URL for your Streamlit app
    # For local development this will be http://localhost:8501
    # For deployed apps, this will be your app's URL
    
    # You can hardcode this for development
    redirect_uri = "http://localhost:8501"  # Use this for local development
    # redirect_uri = "https://your-deployed-app-url.com"  # Use this for production
    
    # Define scopes consistently - order matters for OAuth matching
    scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"  # Adding openid scope which Google might be adding automatically
    ]
    
    return Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=scopes,
        redirect_uri=redirect_uri
    )

# Sidebar for authentication
with st.sidebar:
    st.title("🔐 Authentication")
    
    # OpenAI API Key
    openai_key = st.text_input("OpenAI API Key", type="password", 
                              value=st.session_state.openai_key if st.session_state.openai_key else "")
    if openai_key:
        st.session_state.openai_key = openai_key
        try:
            openai.api_key = openai_key
            # Minimal test to validate API key
            openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            st.success("✅ OpenAI API Key valid")
        except Exception as e:
            st.error(f"❌ OpenAI API Key invalid: {str(e)}")
            st.session_state.openai_key = ""
    
    # Google OAuth
    if not st.session_state.authenticated:
        st.subheader("Google Calendar Auth")
        
        if st.button("Login with Google"):
            flow = create_flow()
            authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent"
            )
            st.session_state.google_auth_state = state
            st.markdown(f"[Click here to authorize]({authorization_url})")
            
    else:
        st.success("✅ Connected to Google Calendar")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.credentials = None
            st.experimental_rerun()

# Check for OAuth callback
# UPDATED: Use st.query_params instead of st.experimental_get_query_params
query_params = st.query_params
if "code" in query_params and not st.session_state.authenticated:
    try:
        flow = create_flow()
        # Save the current state from session to verify during token fetch
        if st.session_state.google_auth_state:
            # Add state parameter to validate the request
            flow.fetch_token(
                code=query_params["code"],
                # Include state parameter to maintain consistency in the OAuth flow
                state=st.session_state.google_auth_state
            )
        else:
            # If no state is saved, just use the code
            flow.fetch_token(code=query_params["code"])
        
        # Store credentials
        creds = flow.credentials
        st.session_state.credentials = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }
        
        # Test credentials
        service = build("calendar", "v3", credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        service.events().list(calendarId='primary', timeMin=now, maxResults=1).execute()
        
        st.session_state.authenticated = True
        # UPDATED: Use st.experimental_set_query_params() replacement
        # Clear the query parameters from the URL
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Authentication failed: {str(e)}")
        # Clean URL by removing query parameters
        st.query_params.clear()

# Main app content
st.title("📅 AI Calendar Assistant")

# Only show chat interface if authenticated
if st.session_state.get("authenticated", False) and st.session_state.openai_key:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Check for pending intents from file
    try:
        if os.path.exists("pending_intent.json"):
            with open("pending_intent.json", "r") as f:
                intent_data = json.load(f)
                st.session_state.pending_intent = intent_data
                
                # Display the pending intent
                with st.container():
                    st.subheader("🔔 Pending Calendar Action")
                    st.write(f"**Event:** {intent_data.get('title')}")
                    start = datetime.datetime.fromisoformat(intent_data.get('start_time').replace('Z', '+00:00'))
                    end = datetime.datetime.fromisoformat(intent_data.get('end_time').replace('Z', '+00:00'))
                    st.write(f"**When:** {start.strftime('%A, %B %d, %Y')} from {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirm", key="confirm_intent"):
                            # Add credentials to the intent
                            intent_data.update({
                                "access_token": st.session_state.credentials["token"],
                                "refresh_token": st.session_state.credentials["refresh_token"],
                                "client_id": st.session_state.credentials["client_id"],
                                "client_secret": st.session_state.credentials["client_secret"],
                            })
                            
                            # Send to calendar agent
                            response = requests.post(
                                "http://localhost:8001/submit",
                                json={
                                    "sender": "frontend_agent",
                                    "message": intent_data
                                }
                            )
                            
                            if response.status_code == 200:
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": "✅ Event has been confirmed and added to your calendar!"
                                })
                                # Remove the pending intent file
                                os.remove("pending_intent.json")
                                st.session_state.pending_intent = None
                                st.rerun()
                            else:
                                st.error(f"Failed to confirm: {response.text}")
                    
                    with col2:
                        if st.button("❌ Cancel", key="cancel_intent"):
                            os.remove("pending_intent.json")
                            st.session_state.pending_intent = None
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "Event cancelled. What would you like to do instead?"
                            })
                            st.rerun()
    except Exception as e:
        st.error(f"Error processing pending intent: {str(e)}")
    
    # User input
    if prompt := st.chat_input("What would you like to do with your calendar?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process with OpenAI to get structured intent
        with st.spinner("Processing your request..."):
            try:
                response = openai.chat.completions.create(
                    model="gpt-4",  # Use appropriate model
                    messages=[
                        {"role": "system", "content": """
                        You are a calendar assistant that converts natural language into structured calendar intents.
                        Extract the relevant details and format them as JSON with these fields:
                        - type: create_event, read_events, update_event, delete_event
                        - title: Event title/summary
                        - start_time: ISO formatted datetime (with timezone)
                        - end_time: ISO formatted datetime (with timezone)
                        - event_id: For update/delete operations
                        
                        If the request is to create an event, assume it's 1 hour long by default unless specified.
                        Use America/Los_Angeles timezone unless otherwise specified.
                        """},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                
                # Parse the structured intent
                intent_data = json.loads(response.choices[0].message.content)
                
                # Process different intent types
                if intent_data.get("type") == "create_event":
                    # Add credentials to the intent
                    intent_data.update({
                        "access_token": st.session_state.credentials["token"],
                        "refresh_token": st.session_state.credentials["refresh_token"],
                        "client_id": st.session_state.credentials["client_id"],
                        "client_secret": st.session_state.credentials["client_secret"],
                        "status": "pending_check"
                    })
                    
                    # Send to frontend agent
                    response = requests.post(
                        "http://localhost:8000/submit",
                        json={
                            "sender": "calendar_agent",
                            "message": intent_data
                        }
                    )
                    
                    if response.status_code == 200:
                        # Forward to calendar agent to check conflicts
                        response = requests.post(
                            "http://localhost:8001/submit",
                            json={
                                "sender": "frontend_agent",
                                "message": intent_data
                            }
                        )
                        
                        if response.status_code == 200:
                            with st.chat_message("assistant"):
                                st.write("⏳ Checking your calendar for conflicts...")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "⏳ Checking your calendar for conflicts..."
                            })
                        else:
                            with st.chat_message("assistant"):
                                st.write(f"❌ Error: {response.text}")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"❌ Error: {response.text}"
                            })
                    else:
                        with st.chat_message("assistant"):
                            st.write(f"❌ Error: {response.text}")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ Error: {response.text}"
                        })
                
                elif intent_data.get("type") == "read_events":
                    # Add credentials to the intent
                    intent_data.update({
                        "access_token": st.session_state.credentials["token"],
                        "refresh_token": st.session_state.credentials["refresh_token"],
                        "client_id": st.session_state.credentials["client_id"],
                        "client_secret": st.session_state.credentials["client_secret"],
                    })
                    
                    # Send directly to calendar agent
                    response = requests.post(
                        "http://localhost:8001/submit",
                        json={
                            "sender": "frontend_agent",
                            "message": intent_data
                        }
                    )
                    
                    if response.status_code == 200:
                        with st.chat_message("assistant"):
                            st.write("⏳ Fetching your calendar events...")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": "⏳ Fetching your calendar events..."
                        })
                    else:
                        with st.chat_message("assistant"):
                            st.write(f"❌ Error: {response.text}")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"❌ Error: {response.text}"
                        })
            
            except Exception as e:
                with st.chat_message("assistant"):
                    st.write(f"❌ Error: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {str(e)}"
                })

else:
    # Show instructions if not authenticated
    if not st.session_state.get("authenticated", False):
        st.warning("⚠️ Please login with your Google account in the sidebar")
    if not st.session_state.openai_key:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar")
    
    st.markdown("""
    ## 🚀 Getting Started
    
    1. Enter your OpenAI API key in the sidebar
    2. Login with your Google account to connect your calendar
    3. Start interacting with your AI Calendar Assistant!
    
    ### Example commands:
    - "Schedule a meeting with Alex tomorrow at 3PM"
    - "Show me my upcoming events"
    - "Book a dentist appointment next Monday at 10AM"
    - "Reschedule my meeting with John to Friday"
    """)