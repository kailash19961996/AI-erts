import streamlit as st
import requests
import json
from twilio.rest import Client
import time
import threading

st.title("AI-erts (AI Alerts)")
st.write("Enter your question to get a real time information delivered directly to your whatsapp")

perplexity_api_key = st.secrets["perplexity_api"]["api_key"]
twilio_api_key = st.secrets["twilio_api"]["api_key"]

# Initialize session state variables
if 'thread' not in st.session_state:
    st.session_state.thread = None

# Twilio credentials
account_sid = 'ACe90242f44d61b05da1f1504a46808400'
auth_token = twilio_api_key
twilio_number = '+14155238886'
client = Client(account_sid, auth_token)

def send_whatsapp_message(to, message):
    client.messages.create(
        body=message,
        from_=f'whatsapp:{twilio_number}',
        to=f'whatsapp:{to}'
    )

def query_perplexity(question):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "llama-3-sonar-small-32k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": question
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer {perplexity_api_key}"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response

def send_periodic_messages(question, whatsapp_number, interval):
    while True:
        response = query_perplexity(question)
        if response.status_code == 200:
            response_json = response.json()
            content = response_json['choices'][0]['message']['content']
            send_whatsapp_message(whatsapp_number, content)
            st.success(f"Message sent to {whatsapp_number}")
        else:
            st.error(f"Error: {response.status_code}")
        
        time.sleep(interval)

user_question = st.text_input("Enter your question:")
whatsapp_number = st.text_input("Enter your WhatsApp number (in E.164 format, e.g., +14155552671):")

frequency_options = {
    "15 secs": 15,
    "1 hour": 3600,
    "6 hours": 21600,
    "24 hours": 86400,
    "1 week": 604800
}
selected_frequency = st.select_slider(
    "Select how frequently you want to receive updates:",
    options=list(frequency_options.keys())
)

if st.button("Start Sending Updates"):
    if user_question and whatsapp_number:
        if st.session_state.thread is None or not st.session_state.thread.is_alive():
            interval = frequency_options[selected_frequency]
            st.info(f"Updates will be sent every {selected_frequency}")
            
            st.session_state.thread = threading.Thread(target=send_periodic_messages, args=(user_question, whatsapp_number, interval))
            st.session_state.thread.start()
            
            st.success("Update service started!")
        else:
            st.warning("Update service is already running.")
    else:
        st.warning("Don't leave any tabs empty.")

st.sidebar.title("Usage Information")
st.sidebar.info(
    "This app uses the Perplexity AI API to answer questions. "
    "Enter your question in the text box, select the frequency of updates, "
    "and click 'Start Sending Updates' to begin receiving periodic responses."
)
