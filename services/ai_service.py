# import os
# import requests
# import anthropic
# from services.tools import tool_registry

# AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")

# # Initialize Claude only if needed
# claude_client = None
# if AI_PROVIDER == "claude":
#     claude_client = anthropic.Anthropic(
#         api_key=os.getenv("ANTHROPIC_API_KEY")
#     )


# def build_system_prompt():
#     available_tools = ", ".join(tool_registry.keys())

#     return f"""
# You are an AI workflow assistant.

# Available tools:
# {available_tools}

# When the user wants to send an email:

# - ALWAYS use tool name: "send_email"
# - ALWAYS return EXACTLY these argument keys:
#     - to
#     - subject
#     - body
# - NEVER use other keys like "recipient"
# - ALWAYS generate a professional email.
# - The email body must:
#     • Start with a greeting (Dear <Name>,)
#     • Contain 2–4 polite sentences
#     • End with a professional closing (Best regards, / Kind regards,)
# - Always generate a meaningful subject line.

# If email intent detected, return ONLY valid JSON:

# {{
#   "tool": "send_email",
#   "arguments": {{
#     "to": "...",
#     "subject": "...",
#     "body": "..."
#   }}
# }}

# If it is normal conversation, return ONLY:

# {{
#   "tool": "none",
#   "response": "..."
# }}

# Do not include explanations.
# Do not wrap JSON in markdown.
# Return raw JSON only.
# """


# def get_ai_response(user_input: str):

#     system_prompt = build_system_prompt()

#     # ---------------------------
#     # OLLAMA MODE
#     # ---------------------------
#     if AI_PROVIDER == "ollama":

#         response = requests.post(
#             "http://localhost:11434/api/generate",
#             json={
#                 "model": "llama3",
#                 "prompt": system_prompt + "\n\nUser: " + user_input,
#                 "stream": False,
#                 "temperature": 0.2  # lower randomness for structured output
#             }
#         )

#         return response.json()["response"]

#     # ---------------------------
#     # CLAUDE MODE
#     # ---------------------------
#     elif AI_PROVIDER == "claude":

#         response = claude_client.messages.create(
#             model="claude-3-haiku-20240307",
#             max_tokens=400,
#             temperature=0.2,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_input}
#             ],
#         )

#         return response.content[0].text

#     else:
#         raise Exception("Invalid AI provider")
    
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


#claude code
import os
from datetime import date
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TOOLS = [
    {
        "name": "send_email",
        "description": "Send an email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "schedule_meet",
        "description": "Schedule a Google Meet calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}},
                "start_time": {"type": "string", "description": "ISO 8601 e.g. 2026-03-01T15:00:00"},
                "end_time": {"type": "string", "description": "ISO 8601 e.g. 2026-03-01T15:30:00"},
                "description": {"type": "string"},
            },
            "required": ["title", "attendees", "start_time", "end_time"],
        },
    },
]

SYSTEM_PROMPT = """You are an AI assistant that sends emails and schedules Google Meet meetings.
Today is {today}.

## TOOL USE GUARD — READ FIRST:
Before using ANY tool, ask yourself: "Is the user EXPLICITLY asking me to send an email or schedule a meeting RIGHT NOW?"
- "explain science" → NO TOOL. Just answer.
- "what is AI" → NO TOOL. Just answer.
- "tell me about X" → NO TOOL. Just answer.
- "send email to X" → YES, use send_email tool.
- "schedule meeting with X" → YES, use schedule_meet tool.
If in ANY doubt → do NOT use a tool. Just respond conversationally.

## CRITICAL RULES — READ CAREFULLY:

1. SCAN THE ENTIRE CONVERSATION HISTORY before responding. All details the user has mentioned are valid.
2. NEVER ask for information the user already provided — even if it was 5 messages ago.
3. Once you have: email address + date + time → IMMEDIATELY call schedule_meet. Do not ask again.
4. Use these DEFAULTS silently (no need to ask):
   - Duration: 30 minutes if not specified
   - Title: "Meeting" if not specified
   - Description: write something friendly based on context
5. NEVER say "I need a few more details" if the info exists anywhere in the chat history.
6. "tomorrow" = {tomorrow}. Calculate dates from today.

## Examples of CORRECT behavior:
- User says "schedule meet with bob@gmail.com at 3pm tomorrow" → IMMEDIATELY call schedule_meet with title="Meeting", attendees=["bob@gmail.com"], start=tomorrow 15:00, end=tomorrow 15:30
- User says "send email to alice@gmail.com about the project" → IMMEDIATELY call send_email with a drafted email
- User across multiple messages provides: email, then title, then date → collect all, then call the tool

## WRONG behavior (never do this):
- Asking "what date?" when user already said "1st March 2026"
- Asking "who to invite?" when user already gave an email address
- Asking "what's the title?" when user already said "lets catch up"
- Re-scheduling or re-sending something that was ALREADY completed in this conversation
- Using a tool again when the user is now asking something completely different (e.g. asking about science after scheduling a meeting)

## IMPORTANT - Topic switching:
If the user's NEW message is clearly unrelated to the previous tool action (e.g. they just ask a general question, want to send a NEW email, etc.), treat it as a fresh request. Do NOT repeat the previous tool call.
"""


def get_ai_response(user_input: str, history: list = None) -> dict:
    today = date.today()
    today_str = today.strftime("%A, %B %d, %Y")
    
    from datetime import timedelta
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    system = SYSTEM_PROMPT.format(today=today_str, tomorrow=tomorrow)

    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if block.type == "tool_use":
                return {"tool": block.name, "arguments": block.input}

        for block in response.content:
            if block.type == "text":
                return {"tool": "none", "response": block.text}

    except Exception as e:
        print("Claude API error:", e)
        return {"tool": "none", "response": f"AI error: {str(e)}"}

    return {"tool": "none", "response": "I couldn't process that request."}
