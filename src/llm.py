import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ==================================================
# ENVIRONMENT
# ==================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Please add it to your .env file."
    )


# ==================================================
# GEMINI CLIENT
# ==================================================

client = genai.Client(
    api_key=api_key
)


MODEL_NAME = "gemini-3.5-flash-lite"


# ==================================================
# TOOL 1 — INSPECT DATASET
# ==================================================

inspect_dataset_tool = types.FunctionDeclaration(
    name="inspect_dataset",

    description=(
        "Inspect the dataset and return information "
        "about rows, columns, column names, data types "
        "and missing values."
    ),

    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={}
    )
)


# ==================================================
# TOOL 2 — BASIC STATISTICS
# ==================================================

get_basic_statistics_tool = types.FunctionDeclaration(
    name="get_basic_statistics",

    description=(
        "Calculate basic statistics for numerical "
        "columns including count, mean, median, "
        "minimum and maximum."
    ),

    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={}
    )
)


# ==================================================
# TOOL 3 — EXECUTE ANALYSIS
# ==================================================

execute_analysis_tool = types.FunctionDeclaration(
    name="execute_analysis",

    description=(
        "Execute Python code to analyze the Pandas "
        "DataFrame named df. The final result of the "
        "analysis must be stored in a variable called "
        "result."
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

        required=[
            "code"
        ]
    )
)


# ==================================================
# ALL TOOLS
# ==================================================

tools = types.Tool(
    function_declarations=[

        inspect_dataset_tool,

        get_basic_statistics_tool,

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