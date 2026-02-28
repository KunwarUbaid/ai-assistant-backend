# # from fastapi import FastAPI
# # from fastapi.middleware.cors import CORSMiddleware
# # from sqlalchemy import create_engine, text
# # from pydantic import BaseModel
# # import os
# # from dotenv import load_dotenv
# # from services.ai_service import get_ai_response
# # import json
# # from services.tools import tool_registry
# # import re
# # from google_auth_oauthlib.flow import Flow
# # from google.oauth2.credentials import Credentials
# # from services.gmail_service import send_email
# # from services.gmail_service import get_auth_url, fetch_token

# # SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


# # # Load env variables
# # load_dotenv()
# # DATABASE_URL = os.getenv("DATABASE_URL")

# # # Create app ONCE
# # app = FastAPI()

# # # Add CORS middleware ONCE
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["http://localhost:3000"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # @app.get("/authorize-gmail")
# # def authorize_gmail():
# #     auth_url = get_auth_url()
# #     return {"auth_url": auth_url}


# # @app.get("/oauth2callback")
# # def oauth2callback(code: str):
# #     fetch_token(code)
# #     return {"message": "Gmail authorized successfully!"}

# # # Create DB engine
# # engine = create_engine(DATABASE_URL)

# # # Request model
# # class ChatRequest(BaseModel):
# #     user_input: str

# # # Home route
# # @app.get("/")
# # def home():
# #     return {"message": "Backend running 🚀"}

# # @app.post("/chat")
# # def chat(req: ChatRequest):

# #     ai_raw = get_ai_response(req.user_input)
# #     print("AI RAW:", ai_raw)

# #     # 🔥 Clean possible markdown wrapping (```json ... ```)
# #     cleaned = re.sub(r"```json|```", "", ai_raw).strip()

# #     try:
# #         ai_data = json.loads(cleaned)
# #         tool_name = ai_data.get("tool", "").lower()

# #         # ----------------------------
# #         # EMAIL DRAFT MODE
# #         # ----------------------------
# #         if tool_name == "send_email":
            
            
# #             args = ai_data.get("arguments", {})

# #             # 🔥 Normalize keys
# #             if "recipient" in args:
# #                 args["to"] = args.pop("recipient")

# #             # Ensure required fields exist
# #             args.setdefault("to", "")
# #             args.setdefault("subject", "No Subject")
# #             args.setdefault("body", "")

# #             return {
# #                 "action": "draft_email",
# #                 "data": args
# #             }

# #         # ----------------------------
# #         # NORMAL CHAT
# #         # ----------------------------
# #         elif tool_name == "none":
# #             return {
# #                 "action": "chat",
# #                 "reply": ai_data.get("response", "")
# #             }

# #         else:
# #             return {
# #                 "action": "chat",
# #                 "reply": f"Tool '{tool_name}' not implemented."
# #             }

# #     except Exception as e:
# #         print("JSON parse error:", str(e))

# #         # If model fails JSON → treat as normal chat
# #         return {
# #             "action": "chat",
# #             "reply": ai_raw
# #         }
        
# # @app.post("/send-email")
# # def send_email_endpoint(payload: dict):

# #     to = payload.get("to")
# #     subject = payload.get("subject")
# #     body = payload.get("body")

# #     result = send_email(to, subject, body)

# #     return {
# #         "status": "success",
# #         "message": result
# #     }
    
# # @app.post("/paraphrase-email")
# # def paraphrase_email(payload: dict):

# #     body = payload.get("body", "")

# #     prompt = f"""
# # Rewrite the following email in a more polished, professional tone.
# # Keep structure with greeting and closing.

# # Email:
# # {body}
# # """

# #     ai_raw = get_ai_response(prompt)

# #     return {"paraphrased": ai_raw}

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import RedirectResponse
# from sqlalchemy import create_engine
# from pydantic import BaseModel
# from dotenv import load_dotenv
# import os
# import json
# import re
# from email.mime.text import MIMEText
# import base64
# from services.ai_service import get_ai_response
# from services.gmail_service import (
#     send_email,
#     get_auth_url,
#     fetch_token,
# )
# from services.gmail_service import get_gmail_service

# # -------------------------
# # ENV & APP SETUP
# # -------------------------
# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# engine = create_engine(DATABASE_URL)


# # -------------------------
# # MODELS
# # -------------------------
# class ChatRequest(BaseModel):
#     user_input: str


# # -------------------------
# # BASIC ROUTES
# # -------------------------
# @app.get("/")
# def home():
#     return {"message": "Backend running 🚀"}


# # -------------------------
# # GMAIL AUTH ROUTES
# # -------------------------
# @app.get("/authorize-gmail")
# def authorize_gmail():
#     auth_url = get_auth_url()
#     return {"auth_url": auth_url}


# @app.get("/oauth2callback")
# def oauth2callback(code: str):
#     fetch_token(code)
#     # After successful login, redirect back to frontend
#     return RedirectResponse("http://localhost:3000")


# def get_plain_text_response(prompt: str):

#     if AI_PROVIDER == "ollama":
#         response = requests.post(
#             "http://localhost:11434/api/generate",
#             json={
#                 "model": "llama3",
#                 "prompt": prompt,
#                 "stream": False
#             }
#         )
#         return response.json()["response"]

#     elif AI_PROVIDER == "claude":
#         response = claude_client.messages.create(
#             model="claude-3-haiku-20240307",
#             max_tokens=500,
#             messages=[
#                 {"role": "user", "content": prompt}
#             ],
#         )
#         return response.content[0].text
# # -------------------------
# # CHAT ROUTE
# # -------------------------
# @app.post("/chat")
# def chat(req: ChatRequest):

#     ai_raw = get_ai_response(req.user_input)
#     print("AI RAW:", ai_raw)

#     # Clean markdown wrappers if present
#     cleaned = re.sub(r"```json|```", "", ai_raw).strip()

#     try:
#         ai_data = json.loads(cleaned)
#         tool_name = ai_data.get("tool", "").lower()

#         # -------------------------
#         # EMAIL DRAFT MODE
#         # -------------------------
#         if tool_name == "send_email":

#             args = ai_data.get("arguments", {})

#             # Normalize key if model uses wrong one
#             if "recipient" in args:
#                 args["to"] = args.pop("recipient")

#             args.setdefault("to", "")
#             args.setdefault("subject", "No Subject")
#             args.setdefault("body", "")

#             return {
#                 "action": "draft_email",
#                 "data": args
#             }

#         # -------------------------
#         # NORMAL CHAT
#         # -------------------------
#         elif tool_name == "none":
#             return {
#                 "action": "chat",
#                 "reply": ai_data.get("response", "")
#             }

#         else:
#             return {
#                 "action": "chat",
#                 "reply": f"Tool '{tool_name}' not implemented."
#             }

#     except Exception as e:
#         print("JSON parse error:", str(e))

#         return {
#             "action": "chat",
#             "reply": "AI returned malformed response."
#         }


# # -------------------------
# # SEND EMAIL
# # -------------------------
# from pydantic import BaseModel

# class EmailRequest(BaseModel):
#     to: str
#     subject: str
#     body: str


# @app.post("/send-email")
# def send_email_endpoint(payload: EmailRequest):
#     service = get_gmail_service()

#     print("SERVICE OBJECT:", service)

#     if service is None:
#         return {"error": "Authorize Gmail first."}

#     message = MIMEText(payload.body)
#     message["to"] = payload.to
#     message["subject"] = payload.subject

#     raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

#     result = service.users().messages().send(
#         userId="me",
#         body={"raw": raw},
#     ).execute()

#     print("GMAIL RESPONSE:", result)

#     return {"message": "Email sent successfully 🚀"}


# # -------------------------
# # PARAPHRASE EMAIL
# # -------------------------
# @app.post("/paraphrase-email")
# def paraphrase_email(payload: dict):

#     body = payload.get("body", "")

#     prompt = f"""
# Rewrite the following email in a more polished, professional tone.
# Keep structure with greeting and closing.

# Email:
# {body}
# """

#     ai_raw = get_ai_response(prompt)

#     return {"paraphrased": ai_raw}
from fastapi import FastAPI, Request as FastAPIRequest
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
)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv( "https://ai-assistant-frontend-ochre.vercel.app",, "http://localhost:3000"),
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
    # Redirect to frontend with email as query param
    frontend = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend}?logged_in={email}")

@app.get("/users")
def list_users():
    return {"users": get_logged_in_users()}

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
