"""
Diagnostic: list all available Gemini models for the configured API key.
Run: python check_models.py
"""
import requests
from config import GEMINI_API_KEY

url = f"https://generativelanguage.googleapis.com/v1/models?key={GEMINI_API_KEY}"
resp = requests.get(url)
data = resp.json()

if "models" not in data:
    print("ERROR:", data)
else:
    print("Available models that support generateContent:\n")
    for m in data["models"]:
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(" •", m["name"])
