import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Please add it to your .env file."
    )


client = genai.Client(api_key=api_key)


MODEL_NAME = "gemini-3.5-flash"


# --------------------------------------------------
# Tool definitions
# --------------------------------------------------

inspect_dataset_tool = types.FunctionDeclaration(
    name="inspect_dataset",
    description=(
        "Inspect the dataset and return information "
        "such as number of rows, number of columns, "
        "column names, data types, and missing values."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={}
    ),
)


execute_analysis_tool = types.FunctionDeclaration(
    name="execute_analysis",
    description=(
        "Execute Python code to perform analysis on "
        "the dataset. The code must store the final "
        "answer in a variable called result."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "code": types.Schema(
                type=types.Type.STRING,
                description=(
                    "Python code that analyzes the existing "
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


# --------------------------------------------------
# Gemini call
# --------------------------------------------------

def ask_agent(user_question, dataset_info):
    """
    Ask Gemini to decide which tool should be used.
    """

    prompt = f"""
You are an AI Data Analyst Agent.

You have access to a Pandas DataFrame called df.

Dataset information:

{dataset_info}

User question:

{user_question}

Decide what action should be taken to answer
the user's question.

Available tools:

1. inspect_dataset
   Use this when you need information about the
   structure of the dataset.

2. execute_analysis
   Use this when Python computation or analysis
   is required.

Choose the appropriate tool.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[tools]
        )
    )

    return response