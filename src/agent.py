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

from data_loader import choose_dataset, load_csv


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
Execute Python Pandas analysis on the currently
selected CSV dataset.

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
Generate a visualization using Matplotlib.

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

You are a general-purpose AI Data Analyst agent.

You analyze ANY CSV dataset supplied by the user.

You are NOT limited to a specific dataset.

--------------------------------------------------
CORE WORKFLOW
--------------------------------------------------

1. Understand the user's question.

2. Inspect the supplied dataset information.

3. Identify the relevant columns.

4. Never assume that columns from another
   dataset exist.

5. Check data quality when relevant.

6. Create a plan for complex questions.

7. Generate Python/Pandas code.

8. Execute the code using execute_analysis.

9. OBSERVE the result.

10. If the tool returns an error:

    - inspect the error
    - determine the cause
    - correct the code
    - execute again

11. Continue until the analysis succeeds
    or no useful progress is possible.

12. If visualization is requested,
    use generate_visualization.

13. Only claim a visualization exists if
    the tool returned success=True.

--------------------------------------------------
GENERAL DATA ANALYSIS
--------------------------------------------------

The dataset can contain ANY columns.

Do not assume:

Age
Fare
Survived
Pclass
Sex

or any other Titanic-specific columns exist.

Always use the actual dataset information
provided in the prompt.

--------------------------------------------------
DATA QUALITY
--------------------------------------------------

Pay attention to:

- missing values
- duplicate rows
- data types
- empty results
- invalid column names
- invalid calculations

Do not blindly remove or modify data.

--------------------------------------------------
ERROR RECOVERY
--------------------------------------------------

If execute_analysis returns:

success=False

read:

error
error_type

Then correct the code and try again.

Do NOT repeat the same failed code.

--------------------------------------------------
COMMON PANDAS PATTERNS
--------------------------------------------------

Filtering:

df[df["column"] > value]

Sorting:

df.sort_values(
    "column",
    ascending=False
)

Top N:

df.nlargest(
    10,
    "column"
)

Grouping:

df.groupby(
    "category"
)["value"].mean()

Multiple statistics:

df.groupby(
    "category"
)["value"].agg(
    ["mean", "median", "min", "max"]
)

Missing values:

df.isnull().sum()

Duplicates:

df.duplicated().sum()

Correlation:

df["column1"].corr(
    df["column2"]
)

--------------------------------------------------
IMPORTANT RULES
--------------------------------------------------

Never invent numbers.

Never guess results.

Always use tools for calculations.

Use actual column names.

Validate results before answering.

Do not create visualizations unless:

- the user explicitly asks for one
OR
- visualization is clearly useful.

--------------------------------------------------
VISUALIZATION
--------------------------------------------------

Use Matplotlib only.

Do not use:

seaborn
plotly

Do not call:

plt.savefig()
plt.close()

The visualization tool handles saving.
"""


# ============================================================
# AGENT FUNCTION
# ============================================================

def run_agent(
    user_question,
    df,
    dataset_name
):

    print(
        "\n" + "=" * 60
    )

    print(
        "SELECTED DATASET"
    )

    print(
        "=" * 60
    )

    print(
        dataset_name
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "USER QUESTION"
    )

    print(
        "=" * 60
    )

    print(
        user_question
    )

    # --------------------------------------------------------
    # Inspect dataset
    # --------------------------------------------------------

    dataset_info = inspect_dataset(
        df
    )

    dataset_context = json.dumps(
        dataset_info,
        indent=2
    )

    prompt = f"""
Currently selected dataset:

{dataset_name}

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
        # Execute tools
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

            print(
                tool_args
            )

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

                print(
                    "\n===== TOOL RESULT ====="
                )

                print(
                    result
                )

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

                print(
                    result
                )

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

If a tool failed:

1. Read the error.
2. Determine why it failed.
3. Correct the code.
4. Call the tool again.

Do not repeat the same failed code.

Use the actual dataset columns.

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

    dataset_name = choose_dataset()

    if dataset_name is None:

        print(
            "No dataset available."
        )

        exit()

    try:

        df = load_csv(
            dataset_name
        )

    except Exception as e:

        print(
            f"\nError loading dataset: {e}"
        )

        exit()

    print(
        f"\nDataset loaded successfully."
    )

    print(
        f"Rows: {df.shape[0]}"
    )

    print(
        f"Columns: {df.shape[1]}"
    )

    question = input(
        "\nAsk your AI Data Analyst: "
    )

    answer = run_agent(
        question,
        df,
        dataset_name
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

    print(
        answer
    )