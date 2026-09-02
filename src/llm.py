import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set."
    )

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash"


# ==================================================
# TOOL DEFINITIONS
# ==================================================

inspect_dataset_tool = types.FunctionDeclaration(
    name="inspect_dataset",
    description=(
        "Inspect the dataset and return the number "
        "of rows, number of columns, column names, "
        "data types, and missing values."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={}
    ),
)


execute_analysis_tool = types.FunctionDeclaration(
    name="execute_analysis",
    description=(
        "Execute Python code to analyze the Pandas "
        "DataFrame named df. The final result must "
        "be stored in a variable called result."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "code": types.Schema(
                type=types.Type.STRING,
                description=(
                    "Python code that analyzes the "
                    "Pandas DataFrame named df."
                )
            )
        },
        required=["code"]
    ),
)


tools = types.Tool(
    function_declarations=[
        inspect_dataset_tool,
        execute_analysis_tool
    ]
)


# ==================================================
# CREATE CHAT
# ==================================================

def create_chat():

    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            tools=[tools]
        )
    )

    return chat