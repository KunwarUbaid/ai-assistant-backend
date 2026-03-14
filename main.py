from fastapi import FastAPI, Request as FastAPIRequest, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import base64
from email.mime.text import MIMEText
from sqlalchemy import create_engine
from typing import List, Optional

from services.ai_service import get_ai_response
from services.gmail_service import (
    send_email,
    schedule_meet,
    get_auth_url,
    fetch_token,
    get_gmail_service,
    get_logged_in_users,
    logout_user,
    _get_user,
)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ai-assistant-frontend-ochre.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ─────────────────────────────────────────────────
class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_input: str
    user_email: str
    history: Optional[List[HistoryMessage]] = []

class EmailRequest(BaseModel):
    user_email: str
    to: str
    subject: str
    body: str

class MeetRequest(BaseModel):
    user_email: str
    title: str
    attendees: list[str]
    start_time: str
    end_time: str
    description: str = ""

class LogoutRequest(BaseModel):
    email: str


# ── Basic ──────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "Backend running 🚀"}


# ── Auth ───────────────────────────────────────────────────
@app.get("/authorize-gmail")
def authorize_gmail():
    return {"auth_url": get_auth_url()}

@app.get("/oauth2callback")
def oauth2callback(code: str):
    token_data = fetch_token(code)
    email = token_data.get("email", "")
    frontend = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend}?logged_in={email}")


# ── Single user lookup (safe — no tokens exposed, no full list) ──
@app.get("/user")
def get_user(email: str):
    """
    Return the public profile for a specific user only.
    The frontend calls this with the email it already knows (from OAuth redirect).
    This prevents the old /users loophole where any device could see all accounts.
    """
    row = _get_user(email)
    if not row:
        raise HTTPException(status_code=404, detail="User not found. Please log in again.")
    return {
        "user": {
            "email": row["email"],
            "name": row.get("name", ""),
            "picture": row.get("picture", ""),
        }
    }


# ── Logout ─────────────────────────────────────────────────
@app.post("/logout")
def logout(req: LogoutRequest):
    logout_user(req.email)
    return {"message": f"Logged out {req.email}"}


# ── Chat ───────────────────────────────────────────────────
@app.post("/chat")
def chat(req: ChatRequest):
    if not req.user_email:
        return {"action": "chat", "reply": "Please log in first."}

    history = [{"role": m.role, "content": m.content} for m in req.history] if req.history else []
    print("HISTORY LENGTH:", len(history))
    result = get_ai_response(req.user_input, history=history)
    tool = result.get("tool", "none").lower()

    if tool == "send_email":
        args = result.get("arguments", {})
        args.setdefault("to", "")
        args.setdefault("subject", "No Subject")
        args.setdefault("body", "")
        return {"action": "draft_email", "data": args}

    elif tool == "schedule_meet":
        return {"action": "draft_meet", "data": result.get("arguments", {})}

    else:
        return {"action": "chat", "reply": result.get("response", "I couldn't understand that.")}


# ── Send Email ─────────────────────────────────────────────
@app.post("/send-email")
def send_email_endpoint(payload: EmailRequest):
    service = get_gmail_service(payload.user_email)
    if service is None:
        return {"error": "Not authorized. Please log in."}

    message = MIMEText(payload.body)
    message["to"] = payload.to
    message["subject"] = payload.subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"message": "Email sent successfully 🚀", "id": result.get("id")}


# ── Schedule Meet ──────────────────────────────────────────
@app.post("/schedule-meet")
def schedule_meet_endpoint(payload: MeetRequest):
    try:
        result = schedule_meet(
            email=payload.user_email,
            title=payload.title,
            attendees=payload.attendees,
            start_time=payload.start_time,
            end_time=payload.end_time,
            description=payload.description,
        )
        return {
            "message": "Meeting scheduled 🎉",
            "meet_link": result["meet_link"],
            "event_link": result["event_link"],
            "details": result,
        }
    except Exception as e:
        return {"error": str(e)}


# ── Paraphrase ─────────────────────────────────────────────
@app.post("/paraphrase-email")
def paraphrase_email(payload: dict):
    body = payload.get("body", "")
    result = get_ai_response(f"Rewrite this email more professionally. Return ONLY the rewritten email:\n\n{body}")
    return {"paraphrased": result.get("response", body)}
