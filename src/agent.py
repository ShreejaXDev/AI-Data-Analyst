import os
import json

import pandas as pd

from dotenv import load_dotenv
from google import genai

from tools import (
    inspect_dataset,
    execute_analysis,
    generate_visualization
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY environment variable is not set."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

MODEL_NAME = "gemini-3.5-flash-lite"

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# TOOL DECLARATIONS
# ============================================================

execute_analysis_tool = {
    "name": "execute_analysis",
    "description": """
Execute Python Pandas code on the dataset.

The code must use the dataframe variable `df`.

The code must store the final answer in a variable
called `result`.

Available libraries:
- pandas as pd
- dataframe as df

Use this tool for:
- filtering
- sorting
- groupby
- aggregation
- statistics
- missing values
- correlations
- comparisons
- top/bottom records
- calculations
""",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Python Pandas code. "
                    "The final result must be stored "
                    "in the variable `result`."
                )
            }
        },
        "required": ["code"]
    }
}


generate_visualization_tool = {
    "name": "generate_visualization",
    "description": """
Generate a visualization using Matplotlib.

The code has access to:
- df
- pd
- plt

Rules:
- Use Matplotlib only.
- Do not use seaborn.
- Do not use plotly.
- Do not call plt.savefig().
- Do not call plt.close().
- Create a figure using plt.
- The tool itself saves the figure.

Choose the visualization based on the question:

Categorical comparison:
bar chart

Distribution:
histogram

Numerical relationship:
scatter plot

Trend over time:
line chart

Proportion:
pie chart or bar chart
""",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Matplotlib Python code that creates "
                    "the requested visualization."
                )
            }
        },
        "required": ["code"]
    }
}


# ============================================================
# SYSTEM INSTRUCTIONS
# ============================================================

SYSTEM_PROMPT = """
You are an AI Data Analyst.

Your job is to analyze a pandas dataframe and answer
the user's natural-language data questions.

You are an AGENT, not simply a chatbot.

You must:

1. Understand the user's question.

2. Inspect the dataset when necessary.

3. Break complex questions into smaller analytical tasks.

4. Generate Python/Pandas code dynamically.

5. Execute the code using the analysis tool.

6. Inspect the result returned by the tool.

7. If the result is insufficient, perform another analysis.

8. If the user asks for a visualization,
   use the visualization tool.

9. Only claim a visualization was created if
   the visualization tool returned success=True.

10. Give a clear final answer using the actual
    computed results.

IMPORTANT DATA ANALYSIS RULES:

- Never invent numbers.
- Never guess analytical results.
- Use the tools to calculate results.
- Prefer pandas operations.
- Handle missing values carefully.
- Check whether columns contain null values
  before calculations when relevant.
- Use appropriate aggregation functions.
- Use groupby when comparing categories.
- Use sorting when the user asks for top/bottom results.
- Use correlation when relationships between numerical
  variables are requested.

COMMON ANALYSIS PATTERNS:

Filtering:
df[df["Age"] > 50]

Sorting:
df.sort_values("Fare", ascending=False)

Top N:
df.nlargest(10, "Fare")

Grouping:
df.groupby("Pclass")["Fare"].mean()

Multiple statistics:
df.groupby("Pclass")["Fare"].agg(
    ["mean", "median", "min", "max"]
)

Missing values:
df.isnull().sum()

Correlation:
df["Age"].corr(df["Fare"])

IMPORTANT:

When using execute_analysis, the final result
must be stored in:

result

For visualization:

- use Matplotlib
- create a figure
- do not use seaborn
- do not use plotly
- do not use savefig
- do not use close

The visualization tool handles saving.

When the user requests both analysis and visualization,
perform BOTH tasks.

Do not say a chart was created unless the tool
actually succeeded.

Return concise but useful explanations.
"""


# ============================================================
# DATASET LOADING
# ============================================================

DATA_PATH = "data/train.csv"

df = pd.read_csv(DATA_PATH)


# ============================================================
# AGENT FUNCTION
# ============================================================

def run_agent(user_question):

    print("\n" + "=" * 60)
    print("USER QUESTION")
    print("=" * 60)

    print(user_question)

    # --------------------------------------------------------
    # Dataset inspection
    # --------------------------------------------------------

    dataset_info = inspect_dataset(df)

    dataset_context = json.dumps(
        dataset_info,
        indent=2
    )

    prompt = f"""
Dataset information:

{dataset_context}

User question:

{user_question}

Analyze the question and use the appropriate tools.
"""

    # --------------------------------------------------------
    # Conversation state
    # --------------------------------------------------------

    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ]

    analysis_completed = False
    visualization_completed = False
    visualization_path = None

    max_iterations = 8

    # --------------------------------------------------------
    # Agent loop
    # --------------------------------------------------------

    for iteration in range(max_iterations):

        print(
            f"\n===== AGENT ITERATION "
            f"{iteration + 1} ====="
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "tools": [
                    {
                        "function_declarations": [
                            execute_analysis_tool,
                            generate_visualization_tool
                        ]
                    }
                ]
            }
        )

        # ----------------------------------------------------
        # Check function calls
        # ----------------------------------------------------

        function_calls = []

        if response.function_calls:

            function_calls = response.function_calls

        if not function_calls:

            final_text = response.text

            wants_visualization = any(
                keyword in user_question.lower()
                for keyword in [
                    "visualization",
                    "visualize",
                    "chart",
                    "graph",
                    "plot"
                ]
            )

            if wants_visualization and not visualization_completed:

                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    "The user explicitly requested "
                                    "a visualization. You have not "
                                    "successfully generated one yet. "
                                    "Please call generate_visualization."
                                )
                            }
                        ]
                    }
                )

                continue

            return final_text

        # ----------------------------------------------------
        # Process function calls
        # ----------------------------------------------------

        tool_results = []

        for function_call in function_calls:

            tool_name = function_call.name

            tool_args = function_call.args

            print("\n===== TOOL CALL =====")
            print(f"Tool: {tool_name}")
            print("Arguments:")
            print(tool_args)

            # ------------------------------------------------
            # ANALYSIS TOOL
            # ------------------------------------------------

            if tool_name == "execute_analysis":

                code = tool_args.get("code")

                result = execute_analysis(
                    code,
                    df
                )

                analysis_completed = result.get(
                    "success",
                    False
                )

                print("\n===== TOOL RESULT =====")
                print(result)

                tool_results.append(
                    {
                        "name": tool_name,
                        "result": result
                    }
                )

            # ------------------------------------------------
            # VISUALIZATION TOOL
            # ------------------------------------------------

            elif tool_name == "generate_visualization":

                code = tool_args.get("code")

                result = generate_visualization(
                    code,
                    df
                )

                visualization_completed = result.get(
                    "success",
                    False
                )

                if visualization_completed:

                    visualization_path = result.get(
                        "path"
                    )

                print("\n===== TOOL RESULT =====")
                print(result)

                tool_results.append(
                    {
                        "name": tool_name,
                        "result": result
                    }
                )

        # ----------------------------------------------------
        # Send tool results back to Gemini
        # ----------------------------------------------------

        contents.append(
            {
                "role": "model",
                "parts": [
                    {
                        "function_call": {
                            "name": call.name,
                            "args": call.args
                        }
                    }
                    for call in function_calls
                ]
            }
        )

        contents.append(
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Tool results:\n"
                            + json.dumps(
                                tool_results,
                                default=str,
                                indent=2
                            )
                            + "\n\n"
                            "Use these results to continue "
                            "the analysis. If more analysis "
                            "is required, call the appropriate "
                            "tool. If visualization was requested "
                            "and has not succeeded, call the "
                            "visualization tool."
                        )
                    }
                ]
            }
        )

    return (
        "The agent reached its maximum number of "
        "iterations before completing the task."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    question = input(
        "\nAsk your AI Data Analyst: "
    )

    answer = run_agent(question)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)

    print(answer)

    if visualization_path:

        print(
            "\nVisualization saved at:"
        )

        print(visualization_path)