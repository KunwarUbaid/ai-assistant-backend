# 🚀 AI Agent Setup Guide

## What Was Added / Changed

### Backend Changes
1. **`services/ai_service.py`** — Rebuilt with Claude's native Tool Use API (no more JSON parsing hacks). Claude now directly calls `send_email` or `schedule_meet` tools.

2. **`services/gmail_service.py`** — Added `schedule_meet()` function using Google Calendar API with Google Meet link generation. Also updated scopes to include Calendar.

3. **`main.py`** — Added `/schedule-meet` endpoint. Chat route now handles `draft_meet` action.

### Frontend Changes
4. **`app/page.tsx`** — Full chat UI with email + meet draft cards, editable before sending.

---

## ⚠️ Important: Re-authorize Google

Since we added the **Google Calendar scope**, you need to re-authorize:

1. **Delete your existing `token.json`** (it only has Gmail scope)
2. Run your backend: `uvicorn main:app --reload`
3. Click **"Authorize Gmail"** button in the UI
4. Log in and accept both Gmail + Calendar permissions
5. You'll be redirected back to the app

---

## 🔧 Google Cloud Console: Enable Calendar API

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select your project `ai-assistant-488808`
3. Go to **APIs & Services → Library**
4. Search for **Google Calendar API** and enable it

---

## 🏃 Running the App

**Backend:**
```bash
cd your-backend-folder
pip install fastapi uvicorn google-auth google-auth-oauthlib google-api-python-client anthropic python-dotenv sqlalchemy psycopg2-binary
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd your-nextjs-folder
pnpm dev
```

---

## 🧪 How to Use

| You say | Agent does |
|---|---|
| "Send an email to bob@gmail.com about the project update" | Shows editable email draft → Send |
| "Schedule a Google Meet with alice@gmail.com tomorrow at 3pm" | Shows editable meet draft → Creates event with Meet link |
| "What can you do?" | Normal chat reply |

---

## 📁 File Structure

```
backend/
├── main.py               ← Updated ✅
├── services/
│   ├── ai_service.py     ← Rebuilt with Claude Tool Use ✅
│   └── gmail_service.py  ← Added Google Meet support ✅
├── client_secret.json
├── token.json            ← DELETE THIS, re-auth needed
└── .env

frontend/
└── app/
    └── page.tsx          ← New chat UI ✅
```
