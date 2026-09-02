# ============================================================
# AI DATA ANALYST - AGENT
# ============================================================

import os
import json
import pandas as pd

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import (
    inspect_dataset,
    execute_analysis,
    generate_visualization
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

MODEL_NAME = "gemini-3.5-flash-lite"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY environment variable is not set."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# TOOL DECLARATIONS
# ============================================================

execute_analysis_declaration = types.FunctionDeclaration(
    name="execute_analysis",
    description="""
Execute Python/pandas analysis on the provided dataframe.

The dataframe is already available as `df`.

Use this tool for:
- calculations
- averages
- sums
- counts
- percentages
- grouping
- filtering
- comparisons
- statistics
- aggregations
- correlations

The final result must be stored in a variable named `result`.

Do not load another dataset.
""",
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": """
Python code for analyzing the dataframe.

The dataframe is available as `df`.

Always store the final result in:

result = ...

Example:

result = df["Fare"].mean()
"""
            }
        },
        "required": ["code"]
    }
)


generate_visualization_declaration = types.FunctionDeclaration(
    name="generate_visualization",
    description="""
Generate a visualization from the provided dataframe.

IMPORTANT:
Use this tool whenever the user asks for:
- a visualization
- a chart
- a graph
- a plot
- a visual comparison
- graphical representation

Rules:

1. Use matplotlib only.
2. Do NOT import seaborn.
3. Do NOT import plotly.
4. Do NOT use other visualization libraries.
5. The dataframe is available as `df`.
6. Use the actual dataframe column names.
7. Create a matplotlib figure.
8. Add a meaningful title.
9. Add meaningful axis labels.
10. Make the visualization readable.
11. Do NOT use plt.savefig().
12. Do NOT use plt.close().

The visualization tool automatically saves the generated figure.
""",
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": """
Matplotlib code for the requested visualization.

The dataframe is available as `df`.

Do NOT use:

plt.savefig()

Do NOT use:

plt.close()

Example:

import matplotlib.pyplot as plt

survival_rates = (
    df.groupby("Pclass")["Survived"]
    .mean()
)

plt.figure(figsize=(8, 6))

plt.bar(
    survival_rates.index.astype(str),
    survival_rates.values
)

plt.title("Survival Rate by Passenger Class")
plt.xlabel("Passenger Class")
plt.ylabel("Survival Rate")
plt.ylim(0, 1)

plt.tight_layout()
"""
            }
        },
        "required": ["code"]
    }
)


# ============================================================
# TOOL
# ============================================================

analyst_tool = types.Tool(
    function_declarations=[
        execute_analysis_declaration,
        generate_visualization_declaration
    ]
)


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """

You are an autonomous AI Data Analyst.

You analyze pandas dataframes by writing and executing Python.

You have exactly two tools:

1. execute_analysis
2. generate_visualization


============================================================
UNDERSTAND THE USER'S COMPLETE REQUEST
============================================================

You MUST identify every task requested by the user.

For example:

"Show survival rate for each passenger class and
create an appropriate visualization."

contains TWO tasks:

TASK 1:
Calculate survival rate.

TASK 2:
Create a visualization.

You must complete BOTH tasks.


============================================================
ANALYSIS TOOL
============================================================

Use:

execute_analysis

for:

- calculations
- averages
- sums
- counts
- percentages
- groupby
- filtering
- comparisons
- statistics
- correlations
- aggregations


============================================================
VISUALIZATION TOOL
============================================================

Use:

generate_visualization

whenever the user asks for:

- visualization
- chart
- graph
- plot
- visual
- graphical representation
- visual comparison

If the user requests analysis AND visualization,
use BOTH tools.


============================================================
IMPORTANT VISUALIZATION RULE
============================================================

When visualization is requested, you MUST call:

generate_visualization

Do NOT attempt to satisfy the visualization request
using execute_analysis.

Do NOT repeatedly call execute_analysis just to verify
a result if the requested visualization has not yet
been created.


============================================================
MATPLOTLIB RULES
============================================================

Visualization code must:

- import matplotlib.pyplot as plt
- use matplotlib only
- NOT use seaborn
- NOT use plotly
- NOT use other visualization libraries
- use the dataframe `df`
- use real dataframe column names
- create a figure
- add a title
- add axis labels
- make the chart readable

NEVER use:

plt.savefig()

NEVER use:

plt.close()

The visualization tool saves the chart automatically.


============================================================
DO NOT OVER-ANALYZE
============================================================

Once an analysis result has successfully answered
the analysis part of the question, do not repeatedly
recalculate the exact same thing.

If visualization is still required, create it.

If all requested tasks are completed, provide the
final answer.


============================================================
TOOL FAILURE
============================================================

If a tool fails:

DO NOT claim success.

Instead:

1. Read the error.
2. Correct the code.
3. Retry the appropriate tool.

Only say that a visualization was generated when
generate_visualization actually succeeded.


============================================================
FINAL ANSWER
============================================================

The final answer should:

- directly answer the user's question
- include important numerical results
- briefly explain the analysis
- mention the visualization if it was successfully created
- mention the actual output path when available

Never claim a chart was generated if the visualization
tool failed or was never called.

"""


# ============================================================
# CREATE CHAT
# ============================================================

def create_chat():

    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[analyst_tool]
        )
    )


# ============================================================
# MAKE VALUES JSON SAFE
# ============================================================

def make_json_safe(value):

    if isinstance(value, dict):

        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, list):

        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):

        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, pd.DataFrame):

        return {
            "type": "dataframe",
            "columns": list(value.columns),
            "rows": value.to_dict(
                orient="records"
            )
        }

    if isinstance(value, pd.Series):

        return {
            "type": "series",
            "values": value.to_dict()
        }

    if hasattr(value, "item"):

        try:
            return value.item()

        except Exception:
            pass

    return value


# ============================================================
# RUN EXECUTE_ANALYSIS
# ============================================================

def run_analysis_tool(
    code,
    df
):

    print("\n===== TOOL CALL =====")
    print("Tool: execute_analysis")
    print("Arguments:")
    print(code)

    result = execute_analysis(
        code,
        df
    )

    safe_result = make_json_safe(
        result
    )

    print("\n===== TOOL RESULT =====")
    print(safe_result)

    return safe_result


# ============================================================
# RUN VISUALIZATION
# ============================================================

def run_visualization_tool(
    code,
    df
):

    print("\n===== TOOL CALL =====")
    print("Tool: generate_visualization")
    print("Arguments:")
    print(code)

    result = generate_visualization(
        code,
        df,
        "outputs/chart.png"
    )

    safe_result = make_json_safe(
        result
    )

    print("\n===== TOOL RESULT =====")
    print(safe_result)

    return safe_result


# ============================================================
# RUN AGENT
# ============================================================

def run_agent(
    question,
    df
):

    # --------------------------------------------------------
    # Dataset information
    # --------------------------------------------------------

    dataset_info = inspect_dataset(
        df
    )

    dataset_info = make_json_safe(
        dataset_info
    )

    print("\n===== DATASET INFO =====")
    print(dataset_info)


    # --------------------------------------------------------
    # Create chat
    # --------------------------------------------------------

    chat = create_chat()


    # --------------------------------------------------------
    # Track completed tasks
    # --------------------------------------------------------

    analysis_completed = False
    visualization_completed = False

    visualization_path = None


    # --------------------------------------------------------
    # Initial request
    # --------------------------------------------------------

    prompt = f"""

USER QUESTION:

{question}


DATASET INFORMATION:

{json.dumps(
    dataset_info,
    indent=2
)}


You must answer the user's complete request.

Determine whether the user requires:

1. data analysis
2. visualization
3. both

IMPORTANT:

If visualization is requested, you MUST call
generate_visualization.

Do not repeatedly call execute_analysis when the
visualization task remains incomplete.

Begin now.
"""


    print("\n===== STARTING AGENT =====")


    # ========================================================
    # AGENT LOOP
    # ========================================================

    max_iterations = 6


    for iteration in range(
        1,
        max_iterations + 1
    ):

        print(
            f"\n===== AGENT ITERATION {iteration} ====="
        )


        # ----------------------------------------------------
        # Ask Gemini
        # ----------------------------------------------------

        response = chat.send_message(
            prompt
        )


        # ----------------------------------------------------
        # Get function calls
        # ----------------------------------------------------

        function_calls = response.function_calls


        # ----------------------------------------------------
        # No function call
        # ----------------------------------------------------

        if not function_calls:

            final_text = response.text

            # ------------------------------------------------
            # Safety check:
            # If visualization was requested but not created,
            # ask Gemini to create it instead of accepting
            # a false final answer.
            # ------------------------------------------------

            visualization_requested = any(
                word in question.lower()
                for word in [
                    "visualization",
                    "visualize",
                    "chart",
                    "graph",
                    "plot"
                ]
            )


            if (
                visualization_requested
                and not visualization_completed
            ):

                print(
                    "\n===== VISUALIZATION STILL REQUIRED ====="
                )

                prompt = """

The user explicitly requested a visualization.

You have NOT successfully created one yet.

Do NOT provide a final answer.

You MUST call generate_visualization now.

Use matplotlib only.
"""

                continue


            print("\n===== FINAL ANSWER =====")
            print(final_text)

            return final_text


        # ----------------------------------------------------
        # Execute function calls
        # ----------------------------------------------------

        for function_call in function_calls:

            tool_name = function_call.name

            arguments = function_call.args


            # =================================================
            # ANALYSIS
            # =================================================

            if tool_name == "execute_analysis":

                code = arguments.get(
                    "code",
                    ""
                )

                result = run_analysis_tool(
                    code,
                    df
                )

                success = (
                    isinstance(result, dict)
                    and result.get(
                        "success",
                        False
                    )
                )

                if success:

                    analysis_completed = True


                tool_part = (
                    types.Part.from_function_response(
                        name="execute_analysis",
                        response={
                            "result": result
                        }
                    )
                )


                # ---------------------------------------------
                # IMPORTANT:
                # Tell Gemini that visualization is still
                # required when applicable.
                # ---------------------------------------------

                visualization_requested = any(
                    word in question.lower()
                    for word in [
                        "visualization",
                        "visualize",
                        "chart",
                        "graph",
                        "plot"
                    ]
                )


                if visualization_requested:

                    follow_up = """

The analysis tool completed successfully.

The original user request ALSO asks for a visualization.

The visualization has NOT been completed yet.

You MUST now call:

generate_visualization

Do NOT call execute_analysis again just to verify
the same result.

Create an appropriate matplotlib visualization
using the dataframe.
"""

                else:

                    follow_up = """

The analysis completed successfully.

Review the user's request.

If another requested task remains, complete it.
Otherwise provide the final answer.
"""


            # =================================================
            # VISUALIZATION
            # =================================================

            elif tool_name == "generate_visualization":

                code = arguments.get(
                    "code",
                    ""
                )

                result = run_visualization_tool(
                    code,
                    df
                )

                success = (
                    isinstance(result, dict)
                    and result.get(
                        "success",
                        False
                    )
                )


                if success:

                    visualization_completed = True

                    visualization_path = result.get(
                        "path"
                    )


                    follow_up = f"""

The visualization was successfully generated.

Output path:

{visualization_path}

The visualization task is now complete.

Review the original user question.

If all requested tasks are complete,
provide the final answer.

Do not call execute_analysis again unless
the user requested another analysis.
"""

                else:

                    follow_up = f"""

The visualization tool failed.

Error/result:

{json.dumps(
    result,
    indent=2
)}

Do NOT claim that the visualization was generated.

Correct the visualization code and call
generate_visualization again.

Use matplotlib only.
"""


                tool_part = (
                    types.Part.from_function_response(
                        name="generate_visualization",
                        response={
                            "result": result
                        }
                    )
                )


            # =================================================
            # UNKNOWN TOOL
            # =================================================

            else:

                tool_part = (
                    types.Part.from_function_response(
                        name=tool_name,
                        response={
                            "result": {
                                "success": False,
                                "error": (
                                    f"Unknown tool: {tool_name}"
                                )
                            }
                        }
                    )
                )

                follow_up = """

An unknown tool was requested.

Do not continue using the unknown tool.

Use only:

execute_analysis

or:

generate_visualization
"""


            # ------------------------------------------------
            # Send tool result back
            # ------------------------------------------------

            response = chat.send_message(
                [
                    tool_part,

                    types.Part.from_text(
                        text=follow_up
                    )
                ]
            )


        # ----------------------------------------------------
        # Check whether Gemini immediately has final answer
        # ----------------------------------------------------

        if not response.function_calls:

            final_text = response.text


            visualization_requested = any(
                word in question.lower()
                for word in [
                    "visualization",
                    "visualize",
                    "chart",
                    "graph",
                    "plot"
                ]
            )


            # ------------------------------------------------
            # Never accept a false visualization claim
            # ------------------------------------------------

            if (
                visualization_requested
                and not visualization_completed
            ):

                print(
                    "\n===== VISUALIZATION STILL REQUIRED ====="
                )

                prompt = """

The user requested a visualization.

No successful visualization tool result exists yet.

Do NOT provide a final answer.

Call generate_visualization now.
"""

                continue


            print("\n===== FINAL ANSWER =====")
            print(final_text)

            return final_text


        # ----------------------------------------------------
        # Continue agent loop
        # ----------------------------------------------------

        prompt = """

Continue working on the original user request.

Remember:

- Do not repeat completed analysis unnecessarily.
- If visualization is requested and has not succeeded,
  call generate_visualization.
- If all requested tasks are complete, provide the
  final answer.
"""


    # ========================================================
    # MAX ITERATIONS
    # ========================================================

    print(
        "\n===== AGENT STOPPED ====="
    )

    return (
        "The agent could not complete all requested "
        "tasks within the maximum number of iterations."
    )