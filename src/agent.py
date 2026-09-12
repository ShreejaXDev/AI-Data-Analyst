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

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY environment variable "
        "is not set."
    )


# ============================================================
# GEMINI
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
Execute Python Pandas analysis on the dataset.

The dataframe is available as:

df

Pandas is available as:

pd

The final answer must be stored in:

result

Use this tool for:

- calculations
- filtering
- sorting
- groupby
- aggregation
- statistics
- correlation
- missing-value analysis
- duplicate analysis
- top/bottom N
- comparisons
""",

    "parameters": {
        "type": "object",

        "properties": {

            "code": {
                "type": "string",

                "description": """
Python/Pandas code.

The final calculated result
must be assigned to:

result
"""
            }

        },

        "required": ["code"]
    }
}


generate_visualization_tool = {
    "name": "generate_visualization",

    "description": """
Generate a data visualization using Matplotlib.

Available variables:

df
pd
plt

Rules:

- Use Matplotlib only.
- Do not use seaborn.
- Do not use plotly.
- Do not call plt.savefig().
- Do not call plt.close().
- Create the figure.
- The tool saves the figure.

Choose appropriate charts:

Categorical comparison:
bar chart

Distribution:
histogram

Numerical relationship:
scatter plot

Trend:
line chart

Proportion:
pie or bar chart
""",

    "parameters": {
        "type": "object",

        "properties": {

            "code": {
                "type": "string",

                "description": (
                    "Matplotlib code that creates "
                    "the requested visualization."
                )
            }

        },

        "required": ["code"]
    }
}


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """

You are an AI Data Analyst agent.

Your job is to analyze arbitrary tabular datasets
using Python and Pandas.

You are an AGENT, not a simple chatbot.

--------------------------------------------------
CORE WORKFLOW
--------------------------------------------------

1. Understand the user's question.

2. Inspect the dataset information.

3. Identify relevant columns.

4. Check data quality when relevant.

5. Create a plan for complex questions.

6. Generate Python/Pandas code.

7. Execute the code using execute_analysis.

8. OBSERVE the tool result.

9. If the tool returns an error:
   - understand the error
   - identify the likely cause
   - generate corrected code
   - execute again

10. Continue until the analysis succeeds
    or no useful progress is possible.

11. If visualization is requested:
    use generate_visualization.

12. Only claim a visualization exists if
    the tool returned success=True.

--------------------------------------------------
DATA QUALITY
--------------------------------------------------

Pay attention to:

- missing values
- duplicate rows
- incorrect column names
- data types
- empty results
- invalid operations

Do not blindly remove or modify data.

If missing values are relevant:

- inspect them
- understand their impact
- choose a sensible analytical approach

Remember that Pandas functions such as mean()
often ignore NaN values automatically.

--------------------------------------------------
ERROR RECOVERY
--------------------------------------------------

IMPORTANT:

Errors are NOT final failures.

If execute_analysis returns:

success=False

inspect:

error
error_type

Then fix the generated code and try again.

Example:

Generated code:

result = df["salary"].mean()

Error:

KeyError: 'salary'

Look at the dataset columns.

If the actual column is:

Salary

generate:

result = df["Salary"].mean()

Then execute again.

Do NOT repeatedly generate the same failed code.

--------------------------------------------------
ANALYSIS PATTERNS
--------------------------------------------------

Filtering:

df[df["Age"] > 50]

Sorting:

df.sort_values(
    "Fare",
    ascending=False
)

Top N:

df.nlargest(
    10,
    "Fare"
)

Grouping:

df.groupby(
    "Pclass"
)["Fare"].mean()

Multiple statistics:

df.groupby(
    "Pclass"
)["Fare"].agg(
    ["mean", "median", "min", "max"]
)

Missing values:

df.isnull().sum()

Duplicates:

df.duplicated().sum()

Correlation:

df["Age"].corr(
    df["Fare"]
)

--------------------------------------------------
IMPORTANT RULES
--------------------------------------------------

Never invent numbers.

Never guess results.

Always use tools for calculations.

Use actual dataset column names.

Validate results before answering.

Keep final answers concise and understandable.

--------------------------------------------------
VISUALIZATION
--------------------------------------------------

Only create a visualization when:

- user explicitly asks for one
OR
- visualization is clearly necessary to answer the question.

Do not automatically create charts for every question.

Use:

Matplotlib only.

Do not use:

seaborn
plotly

Do not call:

plt.savefig()
plt.close()

The visualization tool handles saving.
"""


# ============================================================
# LOAD DATA
# ============================================================

DATA_PATH = "data/train.csv"

df = pd.read_csv(
    DATA_PATH
)


# ============================================================
# AGENT
# ============================================================

def run_agent(user_question):

    print("\n" + "=" * 60)
    print("USER QUESTION")
    print("=" * 60)

    print(user_question)

    # --------------------------------------------------------
    # Inspect dataset
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

Analyze the question carefully.

Use the available tools to calculate
the actual answer.
"""

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

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    analysis_completed = False

    visualization_completed = False

    visualization_path = None

    max_iterations = 8

    # --------------------------------------------------------
    # Agent loop
    # --------------------------------------------------------

    for iteration in range(
        max_iterations
    ):

        print(
            f"\n===== AGENT ITERATION "
            f"{iteration + 1} ====="
        )

        response = client.models.generate_content(
            model=MODEL_NAME,

            contents=contents,

            config={
                "system_instruction":
                    SYSTEM_PROMPT,

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

        function_calls = []

        if response.function_calls:

            function_calls = (
                response.function_calls
            )

        # ----------------------------------------------------
        # No tool call
        # ----------------------------------------------------

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

            if (
                wants_visualization
                and not visualization_completed
            ):

                contents.append(
                    {
                        "role": "user",

                        "parts": [
                            {
                                "text": (
                                    "The user explicitly "
                                    "requested a visualization. "
                                    "You have not successfully "
                                    "generated one yet. "
                                    "Please call "
                                    "generate_visualization."
                                )
                            }
                        ]
                    }
                )

                continue

            return final_text

        # ----------------------------------------------------
        # Tool results
        # ----------------------------------------------------

        tool_results = []

        for function_call in function_calls:

            tool_name = function_call.name

            tool_args = function_call.args

            print(
                "\n===== TOOL CALL ====="
            )

            print(
                f"Tool: {tool_name}"
            )

            print(
                "Arguments:"
            )

            print(tool_args)

            # ================================================
            # ANALYSIS
            # ================================================

            if tool_name == "execute_analysis":

                code = tool_args.get(
                    "code"
                )

                result = execute_analysis(
                    code,
                    df
                )

                analysis_completed = (
                    result.get(
                        "success",
                        False
                    )
                )

                print(
                    "\n===== TOOL RESULT ====="
                )

                print(result)

                tool_results.append(
                    {
                        "name": tool_name,

                        "result": result
                    }
                )

            # ================================================
            # VISUALIZATION
            # ================================================

            elif (
                tool_name ==
                "generate_visualization"
            ):

                code = tool_args.get(
                    "code"
                )

                result = generate_visualization(
                    code,
                    df
                )

                visualization_completed = (
                    result.get(
                        "success",
                        False
                    )
                )

                if visualization_completed:

                    visualization_path = (
                        result.get(
                            "path"
                        )
                    )

                print(
                    "\n===== TOOL RESULT ====="
                )

                print(result)

                tool_results.append(
                    {
                        "name": tool_name,

                        "result": result
                    }
                )

        # ----------------------------------------------------
        # Send results back to Gemini
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
                            + """

Continue the task.

IMPORTANT:

If a tool failed:

1. Read the error.
2. Determine why it failed.
3. Correct the code.
4. Call the tool again.

Do not repeat the same failed code.

If the analysis is successful,
use the result to answer the user.

If visualization was explicitly requested
and has not succeeded, generate it.
"""
                        )
                    }

                ]
            }
        )

    return (
        "The agent reached its maximum "
        "number of iterations before "
        "completing the task."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    question = input(
        "\nAsk your AI Data Analyst: "
    )

    answer = run_agent(
        question
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "FINAL ANSWER"
    )

    print(
        "=" * 60
    )

    print(answer)

    if visualization_path:

        print(
            "\nVisualization saved at:"
        )

        print(
            visualization_path
        )