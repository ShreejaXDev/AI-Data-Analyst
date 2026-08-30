import os

from dotenv import load_dotenv
from google import genai


# Load .env
load_dotenv()


# Get API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing.")


# Create Gemini client
client = genai.Client(api_key=api_key)


print("\n===== MODELS AVAILABLE TO YOUR API KEY =====\n")

for model in client.models.list():

    if model.supported_actions:

        if "generateContent" in model.supported_actions:
            print(model.name)