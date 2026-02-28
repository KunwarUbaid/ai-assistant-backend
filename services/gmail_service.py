# import os
# import base64
# import requests
# from email.mime.text import MIMEText
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials

# SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# CLIENT_SECRET_FILE = "client_secret.json"
# TOKEN_FILE = "token.json"

# import json


# def load_client_config():
#     with open(CLIENT_SECRET_FILE, "r") as f:
#         return json.load(f)["web"]


# def get_auth_url():
#     config = load_client_config()

#     auth_url = (
#         "https://accounts.google.com/o/oauth2/v2/auth"
#         f"?client_id={config['client_id']}"
#         "&response_type=code"
#         "&scope=https://www.googleapis.com/auth/gmail.send"
#         "&access_type=offline"
#         "&prompt=consent"
#         f"&redirect_uri={config['redirect_uris'][0]}"
#     )

#     return auth_url


# def fetch_token(code):
#     config = load_client_config()

#     token_url = "https://oauth2.googleapis.com/token"

#     data = {
#         "code": code,
#         "client_id": config["client_id"],
#         "client_secret": config["client_secret"],
#         "redirect_uri": config["redirect_uris"][0],
#         "grant_type": "authorization_code",
#     }

#     response = requests.post(token_url, data=data)
#     tokens = response.json()

#     if "error" in tokens:
#         raise Exception(tokens)

#     with open(TOKEN_FILE, "w") as f:
#         json.dump(tokens, f)


# def get_gmail_service():
#     if not os.path.exists(TOKEN_FILE):
#         return None

#     with open(TOKEN_FILE, "r") as f:
#         token_data = json.load(f)

#     creds = Credentials(
#         token=token_data["access_token"],
#         refresh_token=token_data.get("refresh_token"),
#         token_uri="https://oauth2.googleapis.com/token",
#         client_id=load_client_config()["client_id"],
#         client_secret=load_client_config()["client_secret"],
#         scopes=SCOPES,
#     )

#     return build("gmail", "v1", credentials=creds)


# def send_email(to, subject, body):
#     service = get_gmail_service()

#     if service is None:
#         return {"error": "Authorize Gmail first."}

#     message = MIMEText(body)
#     message["to"] = to
#     message["subject"] = subject

#     raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

#     result = service.users().messages().send(
#         userId="me",
#         body={"raw": raw},
#     ).execute()

#     print("Gmail API Response:", result)

#     return {"message": "Email sent successfully 🚀"}


#claude code
import os
import json
import requests
import secrets
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

CLIENT_SECRET_FILE = "client_secret.json"
CODE_VERIFIER_FILE = "code_verifier.txt"

engine = create_engine(os.getenv("DATABASE_URL"))


def _load_client_secrets():
    # On Railway: read from environment variable
    raw = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
    if raw:
        secret = json.loads(raw)
        return secret.get("web", secret)
    # Locally: read from file
    with open(CLIENT_SECRET_FILE, "r") as f:
        secret = json.load(f)
    return secret.get("web", secret)


# ── DB helpers ─────────────────────────────────────────────

def _save_user(email, name, picture, google_id, access_token, refresh_token, token_expiry):
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if existing:
            conn.execute(
                text("""
                    UPDATE users SET
                        access_token = :access_token,
                        refresh_token = :refresh_token,
                        token_expiry = :token_expiry,
                        name = COALESCE(NULLIF(:name, ''), name),
                        picture = COALESCE(NULLIF(:picture, ''), picture)
                    WHERE email = :email
                """),
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_expiry": token_expiry,
                    "name": name,
                    "picture": picture,
                    "email": email,
                }
            )
        else:
            conn.execute(
                text("""
                    INSERT INTO users (email, google_id, name, picture, access_token, refresh_token, token_expiry)
                    VALUES (:email, :google_id, :name, :picture, :access_token, :refresh_token, :token_expiry)
                """),
                {
                    "email": email,
                    "google_id": google_id,
                    "name": name,
                    "picture": picture,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_expiry": token_expiry,
                }
            )


def _get_user(email):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()
    return row._asdict() if row else None


def _get_all_users():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT email, google_id, name, picture FROM users")
        ).fetchall()
    return [r._asdict() for r in rows]


def _delete_user(email):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email}
        )


# ── Credentials ────────────────────────────────────────────

def get_credentials(email):
    user = _get_user(email)
    if not user:
        return None

    web = _load_client_secrets()

    try:
        creds = Credentials(
            token=user["access_token"],
            refresh_token=user["refresh_token"],
            token_uri=web["token_uri"],
            client_id=web["client_id"],
            client_secret=web["client_secret"],
            scopes=SCOPES,
        )
    except Exception as e:
        print("Credentials load error:", e)
        return None

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_user(
                email=email,
                name="",
                picture="",
                google_id=user.get("google_id", ""),
                access_token=creds.token,
                refresh_token=creds.refresh_token or user["refresh_token"],
                token_expiry=creds.expiry,
            )
        except Exception as e:
            print("Token refresh error:", e)
            return None

    return creds


# ── OAuth ──────────────────────────────────────────────────

def get_auth_url():
    web = _load_client_secrets()

    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    with open(CODE_VERIFIER_FILE, "w") as f:
        f.write(code_verifier)

    params = {
        "client_id": web["client_id"],
        "redirect_uri": os.getenv("REDIRECT_URI", "http://localhost:8000/oauth2callback"),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    query = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
    return f"{web['auth_uri']}?{query}"


def fetch_token(code):
    web = _load_client_secrets()

    if not os.path.exists(CODE_VERIFIER_FILE):
        raise Exception("code_verifier.txt not found. Please re-authorize.")

    with open(CODE_VERIFIER_FILE, "r") as f:
        code_verifier = f.read().strip()

    resp = requests.post(
        web["token_uri"],
        data={
            "code": code,
            "client_id": web["client_id"],
            "client_secret": web["client_secret"],
            "redirect_uri": os.getenv("REDIRECT_URI", "http://localhost:8000/oauth2callback"),
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        },
    )
    token_data = resp.json()
    if "error" in token_data:
        raise Exception(f"Token exchange failed: {token_data}")

    os.remove(CODE_VERIFIER_FILE)

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token_data['access_token']}"}
    ).json()

    email = user_info.get("email", "unknown")
    google_id = user_info.get("id", "")
    name = user_info.get("name", email)
    picture = user_info.get("picture", "")
    token_expiry = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))

    _save_user(
        email=email,
        name=name,
        picture=picture,
        google_id=google_id,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", ""),
        token_expiry=token_expiry,
    )

    return {"email": email, "name": name, "picture": picture}


def get_logged_in_users():
    return _get_all_users()


def logout_user(email):
    _delete_user(email)


# ── Services ───────────────────────────────────────────────

def get_gmail_service(email):
    creds = get_credentials(email)
    if not creds:
        return None
    return build("gmail", "v1", credentials=creds)


def get_calendar_service(email):
    creds = get_credentials(email)
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds)


def send_email(email, to, subject, body):
    import base64 as b64
    from email.mime.text import MIMEText

    service = get_gmail_service(email)
    if not service:
        raise Exception("Not authorized.")

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = b64.urlsafe_b64encode(message.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def schedule_meet(email, title, attendees, start_time, end_time, description=""):
    service = get_calendar_service(email)
    if not service:
        raise Exception("Not authorized.")

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"},
        "attendees": [{"email": e} for e in attendees],
        "conferenceData": {
            "createRequest": {
                "requestId": f"meet-{start_time}-{email}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    created = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1,
        sendUpdates="all",
    ).execute()

    return {
        "event_id": created["id"],
        "meet_link": created.get("hangoutLink", ""),
        "event_link": created.get("htmlLink", ""),
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
    }
