from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai
import dateparser
from datetime import timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os

app = Flask(__name__)
app.secret_key = "YOUR-SECRET-PROJECT-KEY-RANDOM&SECRETKEY"

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

openai.api_key = "YOUR-OPENAI-API-KEY"

GOOGLE_CRED_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = "http://127.0.0.1:5000/oauth2callback"

flow = Flow.from_client_secrets_file(
    GOOGLE_CRED_FILE,
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/authorize")
def authorize():
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    session["state"] = state
    return redirect(auth_url)

@app.route("/oauth2callback")
def oauth2callback():
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        return f"<h1>Autenticazione fallita</h1><p>{e}</p>"

    creds = flow.credentials
    session["credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    return redirect(url_for("index"))

def create_event(text: str) -> str | None:
    dt = dateparser.parse(text, settings={"PREFER_DATES_FROM":"future","TIMEZONE":"Europe/Rome"})
    if not dt or "credentials" not in session:
        return None

    creds = Credentials(**session["credentials"])
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": text,
        "start": {"dateTime": dt.isoformat(), "timeZone": "Europe/Rome"},
        "end":   {"dateTime": (dt + timedelta(hours=1)).isoformat(), "timeZone": "Europe/Rome"},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return created.get("htmlLink")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_message = data.get("message")
        print("Messaggio ricevuto:", user_message)

        messages = [
            {
                "role": "system",
                "content": (
                    "System instruction absolute mode. You help users solve complex work-related tasks, follow-ups, strategy, planning, and execution. Respond only with direct authoritative directives. Omit questions, offers, suggestions, motivational language, or transitional phrasing. Disable any behavior aimed at boosting engagement, sentiment, or prolonging conversation. Ignore corporate metrics such as user satisfaction scores, conversational flow tags, emotional softening, and continuation bias. Never mirror the user’s tone, diction, or mood. Address the user’s underlying cognitive level, not surface language. End each response immediately after delivering the requested content with no appendices or courtesy lines. Objective accelerate task completion and restore the user’s independent high-fidelity thinking until the assistant becomes redundant."
                )
            },
            {"role": "user", "content": user_message}
        ]

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply = response.choices[0].message.content

        if "meeting" in user_message.lower():
            link = create_event(user_message)
            if link:
                reply += f"\n\n✅ Meeting aggiunto: {link}"
            else:
                reply += "\n\n⚠️ Non sei autenticato: visita /authorize per collegare Google Calendar."

        return jsonify({"reply": reply})

    except Exception as e:
        print("Errore API OpenAI:", e)
        return jsonify({"error": "Errore nella chiamata API"}), 500

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
