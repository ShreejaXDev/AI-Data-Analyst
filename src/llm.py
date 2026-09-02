import os

from dotenv import load_dotenv

from google import genai

from google.genai import types


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:

    raise ValueError(
        "GEMINI_API_KEY is not set."
    )


# ============================================================
# CLIENT
# ============================================================

client = genai.Client(
    api_key=api_key
)


MODEL_NAME = "gemini-3.5-flash-lite"


# ============================================================
# TOOL 1 — INSPECT DATASET
# ============================================================

inspect_dataset_tool = types.FunctionDeclaration(

    name="inspect_dataset",

    description=(
        "Inspect the dataset and return "
        "rows, columns, data types and "
        "missing values."
    ),

    parameters=types.Schema(

        type=types.Type.OBJECT,

        properties={}
    )
)


# ============================================================
# TOOL 2 — BASIC STATISTICS
# ============================================================

get_basic_statistics_tool = types.FunctionDeclaration(

    name="get_basic_statistics",

    description=(
        "Calculate basic statistics for "
        "numerical columns."
    ),

    parameters=types.Schema(

        type=types.Type.OBJECT,

        properties={}
    )
)


# ============================================================
# TOOL 3 — EXECUTE ANALYSIS
# ============================================================

execute_analysis_tool = types.FunctionDeclaration(

    name="execute_analysis",

    description=(
        "Execute Python code to analyze "
        "the Pandas DataFrame named df. "
        "Store the final result in a variable "
        "called result."
    ),

    parameters=types.Schema(

        type=types.Type.OBJECT,

        properties={

            "code": types.Schema(

                type=types.Type.STRING,

                description=(
                    "Python analysis code."
                )
            )
        },

        required=[
            "code"
        ]
    )
)


# ============================================================
# TOOL 4 — GENERATE VISUALIZATION
# ============================================================

generate_visualization_tool = types.FunctionDeclaration(

    name="generate_visualization",

    description=(
        "Generate a chart or visualization "
        "using Python and matplotlib. "
        "Use this when a visualization would "
        "help answer the user's question. "
        "The chart should be saved automatically."
    ),

    parameters=types.Schema(

        type=types.Type.OBJECT,

        properties={

            "code": types.Schema(

                type=types.Type.STRING,

                description=(
                    "Python code that creates "
                    "a matplotlib visualization."
                )
            )
        },

        required=[
            "code"
        ]
    )
)


# ============================================================
# ALL TOOLS
# ============================================================

tools = types.Tool(

    function_declarations=[

        inspect_dataset_tool,

        get_basic_statistics_tool,

        execute_analysis_tool,

        generate_visualization_tool

    ]
)


# ============================================================
# CREATE CHAT
# ============================================================

def create_chat():

    return client.chats.create(

        model=MODEL_NAME,

        config=types.GenerateContentConfig(

            tools=[
                tools
            ]
        )
    )