import os
import json

from dotenv import load_dotenv
from google import genai

from tools import (
    inspect_dataset,
    execute_analysis,
    generate_visualization
)

from data_loader import (
    choose_dataset,
    load_csv
)

from planner import (
    validate_plan,
    format_plan,
    parse_plan_response
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
# CONVERSATION MEMORY
# ============================================================

conversation_history = []


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

        "required": [
            "code"
        ]
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

        "required": [
            "code"
        ]
    }
}


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """

You are a general-purpose AI Data Analyst agent.

You analyze ANY CSV dataset supplied by the user.

You are NOT limited to a specific dataset.

==================================================
SMART DATA PROFILE & REASONING
==================================================

You receive a comprehensive, deterministic dataset profile before planning and execution.

Use this rich profile to:
- Understand exact dataset shape, row count, column names, and dtypes.
- Check missing value counts and percentages per column to handle missingness safely.
- Identify key categorical grouping candidates based on unique value counts and cardinality.
- Recognize numerical statistics (min, max, mean, median, std, quartiles) for measures.
- Use correlation matrices when asked about column relationships.
- Pay attention to possible_id_columns and avoid using identifier columns as numeric measures.
- Pay attention to possible_date_columns for time-series / trend questions.
- Leverage the deterministic analysis_hints generated directly from the dataset.

==================================================
CORE WORKFLOW
==================================================

1. Understand the user's current question.

2. Consider the previous conversation.

3. Use the explicit analysis plan.

4. Inspect the supplied dataset information.

5. Identify the relevant columns.

6. Never assume columns from another dataset exist.

7. Check data quality when relevant.

8. Follow the analysis plan.

9. Generate Python/Pandas code.

10. Execute the code using execute_analysis.

11. OBSERVE the result.

12. Use the result to decide what should
    happen next.

13. If the tool returns an error:

    - inspect the error
    - determine the cause
    - correct the code
    - execute again

14. Continue until the analysis succeeds
    or no useful progress is possible.

15. If visualization is requested,
    use generate_visualization.

16. Only claim a visualization exists if
    the tool returned success=True.

==================================================
PLANNING
==================================================

The agent receives an explicit plan created
by a planning component.

The plan describes the logical steps required
to answer the user's question.

Do not blindly execute every planned step.

After each tool result:

- observe the result
- determine whether the next planned step
  is still necessary
- adapt if the result changes the situation

Planning tells you WHAT needs to happen.

Tool selection and execution determine HOW
to accomplish it.

==================================================
CONVERSATIONAL MEMORY
==================================================

You are a conversational AI Data Analyst.

The user may ask follow-up questions.

Examples:

User:
Which region had the highest sales?

User:
What is its average quantity?

Here, "its" refers to the region identified
in the previous answer.

Another example:

User:
Which product had the highest sales?

User:
How much quantity did it sell?

"it" refers to the product identified previously.

Another example:

User:
Show me sales by region.

User:
Now make a chart for that.

"that" refers to the previous analysis.

Another example:

User:
Which region performed best?

User:
Compare it with North.

"it" refers to the region identified previously.

IMPORTANT:

Do NOT treat every question as independent.

Use previous conversation history to resolve:

- it
- its
- they
- them
- that
- this
- those
- the previous result
- the highest one
- the lowest one
- the first one
- the second one
- that region
- that product

If the user asks a completely new question,
analyze it independently.

==================================================
DATA ANALYSIS
==================================================

The dataset can contain ANY columns.

Do not assume:

Age
Fare
Survived
Pclass
Sex

or any other Titanic-specific columns exist.

Always use actual dataset information.

==================================================
DATA QUALITY
==================================================

Pay attention to:

- missing values
- duplicate rows
- data types
- empty results
- invalid column names
- invalid calculations

Do not blindly remove or modify data.

==================================================
ERROR RECOVERY
==================================================

If execute_analysis returns:

success=False

read:

error
error_type

Then:

1. Understand the error.
2. Correct the code.
3. Execute again.

Do NOT repeat the same failed code.

==================================================
COMMON PANDAS PATTERNS
==================================================

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

==================================================
IMPORTANT RULES
==================================================

Never invent numbers.

Never guess results.

Always use tools for calculations.

Use actual column names.

Validate results before answering.

Do not create visualizations unless:

- the user explicitly asks for one
OR
- visualization is clearly useful.

==================================================
VISUALIZATION
==================================================

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
# DATASET CONTEXT
# ============================================================

def get_dataset_context(df):
    """
    Get structured information about the dataset.
    """

    dataset_info = inspect_dataset(
        df
    )

    return json.dumps(
        dataset_info,
        indent=2
    )


# ============================================================
# CONVERSATION CONTEXT
# ============================================================

def get_conversation_context():
    """
    Convert previous conversation turns
    into clean context for Gemini.
    """

    if not conversation_history:
        return "No previous conversation."

    context = ""

    for i, turn in enumerate(
        conversation_history,
        start=1
    ):

        context += f"""

--- Conversation Turn {i} ---

USER:
{turn["user"]}

ASSISTANT:
{turn["assistant"]}

"""

    return context


# ============================================================
# CREATE EXPLICIT PLAN
# ============================================================

def create_plan(
    user_question,
    dataset_name,
    dataset_context,
    conversation_context
):
    """
    Ask Gemini to create an explicit
    step-by-step analysis plan.
    """

    planner_prompt = f"""
You are the planning component of an
AI Data Analyst.

Your job is to create a clear and practical
step-by-step plan for answering the user's
current question.

==================================================
DATASET
==================================================

Dataset name:

{dataset_name}

Dataset information:

{dataset_context}

==================================================
PREVIOUS CONVERSATION
==================================================

{conversation_context}

==================================================
CURRENT QUESTION
==================================================

{user_question}

==================================================
PLANNING RULES
==================================================

1. Break complex questions into logical steps.

2. Keep simple questions simple.

3. Do not invent columns.

4. Use actual dataset columns.

5. Include calculations that require
   Python/Pandas.

6. If the user explicitly requests a chart,
   graph, plot, or visualization, include
   visualization as a plan step.

7. Do not perform the analysis.

8. Do not invent numerical results.

9. Resolve follow-up references using the
   previous conversation when possible.

10. Return ONLY valid JSON.

Required format:

{{
    "goal": "overall goal",
    "steps": [
        {{
            "step": 1,
            "description": "..."
        }},
        {{
            "step": 2,
            "description": "..."
        }}
    ]
}}
"""

    try:

        response = client.models.generate_content(

            model=MODEL_NAME,

            contents=planner_prompt,

            config={
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        )

        plan = parse_plan_response(
            response.text
        )

        return plan

    except Exception as e:

        print()
        print(
            "Planner warning:"
        )

        print(
            str(e)
        )

        print(
            "Using fallback plan."
        )

        return {
            "goal": (
                "Analyze the user's question."
            ),

            "steps": [
                {
                    "step": 1,
                    "description": (
                        "Analyze the user's "
                        "question using the "
                        "supplied dataset."
                    )
                }
            ]
        }


# ============================================================
# RUN AGENT
# ============================================================

def run_agent(
    user_question,
    df,
    dataset_name
):

    print()
    print(
        "=" * 60
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

    print()
    print(
        "=" * 60
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


    # ========================================================
    # DATASET CONTEXT
    # ========================================================

    dataset_context = get_dataset_context(
        df
    )


    # ========================================================
    # CONVERSATION CONTEXT
    # ========================================================

    conversation_context = (
        get_conversation_context()
    )


    # ========================================================
    # CREATE PLAN
    # ========================================================

    plan = create_plan(

        user_question,

        dataset_name,

        dataset_context,

        conversation_context

    )


    # ========================================================
    # DISPLAY PLAN
    # ========================================================

    print()
    print(
        "=" * 60
    )

    print(
        "AGENT PLAN"
    )

    print(
        "=" * 60
    )

    print(
        format_plan(plan)
    )

    print(
        "=" * 60
    )


    # ========================================================
    # MAIN PROMPT
    # ========================================================

    prompt = f"""
Currently selected dataset:

{dataset_name}

Dataset information:

{dataset_context}

==================================================
PREVIOUS CONVERSATION
==================================================

{conversation_context}

==================================================
CURRENT USER QUESTION
==================================================

{user_question}

==================================================
EXPLICIT ANALYSIS PLAN
==================================================

{json.dumps(plan, indent=2)}

==================================================

Follow the explicit plan.

Important:

- Do not blindly execute every step.
- Use tool results to decide what to do next.
- If a result changes the situation,
  adapt the remaining work.
- Use execute_analysis for calculations.
- Use generate_visualization only when needed.
- Observe tool results before continuing.
- Do not invent values.
- Use actual dataset columns.
"""


    # ========================================================
    # GEMINI CONTENTS FOR CURRENT TURN
    # ========================================================

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


    # ========================================================
    # STATE
    # ========================================================

    visualization_completed = False

    visualization_path = None

    max_iterations = 8


    # ========================================================
    # AGENT LOOP
    # ========================================================

    for iteration in range(
        max_iterations
    ):

        print()

        print(
            f"===== AGENT ITERATION "
            f"{iteration + 1} ====="
        )


        # ----------------------------------------------------
        # ASK GEMINI
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # GET FUNCTION CALLS
        # ----------------------------------------------------

        function_calls = []

        if response.function_calls:

            function_calls = (
                response.function_calls
            )


        # ====================================================
        # NO TOOL CALL
        # ====================================================

        if not function_calls:

            final_text = response.text


            # ------------------------------------------------
            # Check visualization request
            # ------------------------------------------------

            wants_visualization = any(

                keyword in (
                    user_question.lower()
                )

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


            # ------------------------------------------------
            # SAVE CONVERSATION MEMORY
            # ------------------------------------------------

            conversation_history.append(

                {

                    "user":
                        user_question,

                    "assistant":
                        final_text

                }

            )


            return final_text


        # ====================================================
        # EXECUTE TOOLS
        # ====================================================

        tool_results = []


        for function_call in function_calls:

            tool_name = function_call.name

            tool_args = function_call.args


            print()
            print(
                "===== TOOL CALL ====="
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


            # =================================================
            # EXECUTE ANALYSIS
            # =================================================

            if tool_name == "execute_analysis":

                code = tool_args.get(
                    "code"
                )


                if not code:

                    result = {

                        "success": False,

                        "error":
                            "No Python code was provided.",

                        "error_type":
                            "MissingCode"

                    }

                else:

                    result = execute_analysis(

                        code,

                        df

                    )


                print()
                print(
                    "===== TOOL RESULT ====="
                )

                print(
                    result
                )


                tool_results.append(

                    {

                        "name":
                            tool_name,

                        "result":
                            result

                    }

                )


            # =================================================
            # GENERATE VISUALIZATION
            # =================================================

            elif (
                tool_name ==
                "generate_visualization"
            ):

                code = tool_args.get(
                    "code"
                )


                if not code:

                    result = {

                        "success": False,

                        "error":
                            "No visualization code "
                            "was provided.",

                        "error_type":
                            "MissingCode"

                    }

                else:

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


                print()
                print(
                    "===== TOOL RESULT ====="
                )

                print(
                    result
                )


                tool_results.append(

                    {

                        "name":
                            tool_name,

                        "result":
                            result

                    }

                )


        # ====================================================
        # SEND TOOL RESULTS BACK TO GEMINI
        # ====================================================

        contents.append(

            {

                "role": "model",

                "parts": [

                    {

                        "function_call": {

                            "name":
                                call.name,

                            "args":
                                call.args

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

1. Observe the tool result.

2. Follow the explicit plan.

3. Decide what the next logical step is.

4. If a tool failed:

   - read the error
   - identify the cause
   - correct the code
   - execute again

5. Do not repeat the same failed code.

6. Use actual dataset columns.

7. If visualization was explicitly
   requested and has not succeeded,
   generate it.

8. Do not invent results.
"""

                        )

                    }

                ]

            }

        )


    # ========================================================
    # MAX ITERATIONS
    # ========================================================

    final_text = (

        "The agent reached its maximum "
        "number of iterations before "
        "completing the task."

    )


    conversation_history.append(

        {

            "user":
                user_question,

            "assistant":
                final_text

        }

    )


    return final_text


# ============================================================
# RESET CONVERSATION
# ============================================================

def reset_conversation():

    """
    Clear conversational memory.
    """

    conversation_history.clear()


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


    print()
    print(
        "Dataset loaded successfully."
    )

    print(
        f"Rows: {df.shape[0]}"
    )

    print(
        f"Columns: {df.shape[1]}"
    )


    # ========================================================
    # CONVERSATIONAL MODE
    # ========================================================

    print()
    print(
        "=" * 60
    )

    print(
        "CONVERSATIONAL MODE"
    )

    print(
        "=" * 60
    )

    print()

    print(
        "Ask questions about your dataset."
    )

    print(
        "Type 'exit' or 'quit' to stop."
    )

    print(
        "Type 'clear' to reset conversation memory."
    )

    print()


    while True:

        try:

            question = input(
                "You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print(
                "\nGoodbye!"
            )

            break


        # ----------------------------------------------------
        # EMPTY INPUT
        # ----------------------------------------------------

        if not question:

            print(
                "Please enter a question."
            )

            continue


        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if question.lower() in [

            "exit",
            "quit"

        ]:

            print()
            print(
                "Goodbye! 👋"
            )

            break


        # ----------------------------------------------------
        # CLEAR MEMORY
        # ----------------------------------------------------

        if question.lower() == "clear":

            reset_conversation()

            print()
            print(
                "Conversation memory cleared."
            )

            print()

            continue


        # ----------------------------------------------------
        # RUN AGENT
        # ----------------------------------------------------

        try:

            answer = run_agent(

                question,

                df,

                dataset_name

            )


            print()
            print(
                "FINAL ANSWER:"
            )

            print(
                answer
            )

            print()


        except Exception as e:

            print()
            print(
                "Agent Error:"
            )

            print(
                str(e)
            )

            print()