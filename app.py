# app.py

import streamlit as st
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# -------------------------------
# Email Sending Function
# -------------------------------

def send_crisis_email(name, phone_number):
    sender_email = os.getenv("SENDER_EMAIL")  
    sender_password = os.getenv("SENDER_PASSWORD")  
    receiver_email = "iamsiddahsan@gmail.com"

    if not sender_email or not sender_password:
        st.error("Email credentials are not set. Please set SENDER_EMAIL and SENDER_PASSWORD environment variables.")
        return False

    subject = "Crisis Alert: User in Serious Condition"
    body = f"""\
Subject: {subject}

This is to inform you that a user is in a serious condition and may harm themselves.

Name: {name}
Phone Number: {phone_number}
"""

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# -------------------------------
# Crisis Keyword Detection
# -------------------------------

def is_crisis_keyword_detected(text):
    crisis_keywords = [
        "suicide", "kill myself", "end my life", "self-harm", "i'm going to die",
        "can't go on", "no reason to live", "drop everything", "dead inside"
    ]
    text_lower = text.lower()
    for keyword in crisis_keywords:
        if keyword in text_lower:
            return True
    return False

# -------------------------------
# API Interaction Function
# -------------------------------

def send_text_to_api(input_text, ngrok_url):
    """
    Sends the input text to the Flask API and retrieves the generated mental health exercise and emotion.

    Args:
        input_text (str): The text to analyze for emotion and generate an exercise.
        ngrok_url (str): The public Ngrok URL pointing to your Flask API.

    Returns:
        tuple: (response_text, emotion) or (error_message, None)
    """
    api_endpoint = f"{ngrok_url}/generate"  
    payload = {"input_text": input_text}

    try:
        response = requests.post(api_endpoint, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data.get("response", ""), data.get("emotion", "")
        else:
            try:
                error_message = response.json().get("error", "An unknown error occurred.")
            except ValueError:
                error_message = "Invalid response format from the server."
            return f"Error {response.status_code}: {error_message}", None
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}", None

# -------------------------------
# Streamlit App Configuration
# -------------------------------

st.set_page_config(page_title="Mental Health Support Chatbot", layout="wide")
st.title("Mental Health Support Chatbot")
st.markdown("Feel free to share your thoughts. I'm here to listen and help.")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""

if "crisis_detected" not in st.session_state:
    st.session_state["crisis_detected"] = False

if "crisis_form_submitted" not in st.session_state:
    st.session_state["crisis_form_submitted"] = False

# -------------------------------
# Handle User Message
# -------------------------------

def handle_message():
    user_message = st.session_state.user_input.strip()
    if user_message:
        st.session_state["messages"].append({"user": user_message})
        
        ngrok_url = "https://7060-34-125-52-33.ngrok-free.app" 

        exercise, emotion = send_text_to_api(user_message, ngrok_url)
        print(f"Received Exercise: {exercise}, Emotion: {emotion}")  # Debugging

        st.session_state["messages"].append({"bot": exercise, "emotion": emotion})

        if (emotion and emotion.lower() == "crisis") or is_crisis_keyword_detected(user_message):
            st.session_state["crisis_detected"] = True
        else:
            st.session_state["crisis_detected"] = False

        st.session_state["user_input"] = ""

# -------------------------------
# Display Messages
# -------------------------------

for message in st.session_state["messages"]:
    if "user" in message:
        st.markdown(
            f"""
            <div style="text-align:right; margin-bottom:20px;">
                <div style="font-size:14px; color:#4CAF50; font-weight:bold;">You</div>
                <div style="background-color:#4CAF50; color:white; padding:10px; border-radius:10px; display:inline-block; max-width:70%; word-wrap:break-word;">
                    {message['user']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif "bot" in message:
        st.markdown(
            f"""
            <div style="text-align:left; margin-bottom:20px;">
                <div style="font-size:14px; color:#2196F3; font-weight:bold;">Bot</div>
                <div style="font-size:12px; color:#FF9800; font-weight:bold; margin-bottom:5px;">Emotion: {message['emotion']}</div>
                <div style="background-color:#E0E0E0; color:black; padding:10px; border-radius:10px; display:inline-block; max-width:70%; word-wrap:break-word;">
                    {message['bot']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -------------------------------
# Crisis Handling Form
# -------------------------------

if st.session_state["crisis_detected"] and not st.session_state["crisis_form_submitted"]:
    st.markdown("---")
    st.warning("We've detected a crisis situation. Please provide your contact information so we can assist you further.")

    with st.form("crisis_form"):
        name = st.text_input("Your Name")
        phone = st.text_input("Your Phone Number")
        submit = st.form_submit_button("Submit")
        
        if submit:
            if not name or not phone:
                st.error("Please provide both your name and phone number.")
            else:
                email_sent = send_crisis_email(name, phone)
                if email_sent:
                    st.success("Thank you. We've been notified and will reach out to you shortly.")
                    st.session_state["crisis_form_submitted"] = True
                    st.session_state["crisis_detected"] = False
                else:
                    st.error("There was an issue sending your information. Please try again later.")

# -------------------------------
# User Input Field
# -------------------------------

st.text_input("Type your message here:", key="user_input", on_change=handle_message)
