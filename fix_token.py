"""
Run this ONCE in your backend folder to fix your existing token.json.
Usage: python fix_token.py
"""
import json

with open("token.json", "r") as f:
    token = json.load(f)

with open("client_secret.json", "r") as f:
    secret = json.load(f)

web = secret.get("web", secret)
token["client_id"] = web["client_id"]
token["client_secret"] = web["client_secret"]

with open("token.json", "w") as f:
    json.dump(token, f, indent=2)

print("✅ token.json patched successfully! You can now run uvicorn main:app --reload")
