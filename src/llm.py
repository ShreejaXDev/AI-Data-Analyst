import os

from dotenv import load_dotenv
from google import genai


# Load variables from .env
load_dotenv()


# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Please add it to your .env file."
    )


# Create Gemini client
client = genai.Client(api_key=api_key)


# Model we will use
MODEL_NAME = "gemini-3.5-flash"


def generate_python_code(dataset_info, user_question):
    """
    Ask Gemini to generate Python code
    that can answer the user's question.
    """

    prompt = f"""
You are a Python data analyst.

You are given information about a Pandas DataFrame
called df.

Dataset information:
{dataset_info}

User question:
{user_question}

Your task is to generate Python code that answers
the user's question.

Rules:

1. Use the existing DataFrame named df.
2. Use pandas or standard Python only.
3. Do not load another file.
4. Do not modify the original dataset.
5. Return only executable Python code.
6. Store the final answer/result in a variable
   called result.
7. Do not use markdown code fences.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()