# services/tools.py

def send_email(args):
    to = args.get("to")
    subject = args.get("subject")
    body = args.get("body")

    print(f"📧 Sending email to {to}")
    return f"Email prepared for {to} with subject '{subject}'."

def summarize_file(args):
    filename = args.get("filename")
    return f"Summary generated for {filename}"

# 🔥 Add aliases
tool_registry = {
    "send_email": send_email,
    "email": send_email,          # alias
    "send email": send_email,     # alias
    "summarize_file": summarize_file,
}