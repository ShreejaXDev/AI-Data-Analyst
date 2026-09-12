import os
import json

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY environment variable is not set."
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

==================================================
CORE WORKFLOW
==================================================

1. Understand the user's current question.

2. Consider the previous conversation.

3. Inspect the supplied dataset information.

4. Identify the relevant columns.

5. Never assume that columns from another
   dataset exist.

6. Check data quality when relevant.

7. Create a plan for complex questions.

8. Generate Python/Pandas code.

9. Execute the code using execute_analysis.

10. OBSERVE the result.

11. If the tool returns an error:

    - inspect the error
    - determine the cause
    - correct the code
    - execute again

12. Continue until the analysis succeeds
    or no useful progress is possible.

13. If visualization is requested,
    use generate_visualization.

14. Only claim a visualization exists if
    the tool returned success=True.

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

Use the previous conversation history to
resolve references such as:

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

However, if the user asks a completely new
question, analyze it independently.

Do not repeat the entire previous answer
unless needed.

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

Always use the actual dataset information
provided in the prompt.

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

    dataset_info = inspect_dataset(df)

    return json.dumps(
        dataset_info,
        indent=2
    )


# ============================================================
# CONVERSATION CONTEXT
# ============================================================

def get_conversation_context():
    """
    Convert previous user/assistant turns into
    a clean context string.
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
# RUN AGENT
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
    # Dataset information
    # --------------------------------------------------------

    dataset_context = get_dataset_context(
        df
    )


    # --------------------------------------------------------
    # Previous conversation
    # --------------------------------------------------------

    conversation_context = (
        get_conversation_context()
    )


    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

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

Analyze the CURRENT question.

Use previous conversation when the current
question refers to something discussed earlier.

Resolve words such as "it", "its", "that",
"this", "the previous one", etc. using context.

Use tools to calculate the actual answer.

Do not invent values.
"""


    # --------------------------------------------------------
    # Gemini conversation for THIS turn
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


    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    visualization_completed = False

    visualization_path = None

    max_iterations = 8


    # ========================================================
    # AGENT LOOP
    # ========================================================

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


        # ----------------------------------------------------
        # Function calls
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
            # Visualization check
            # ------------------------------------------------

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


            # ------------------------------------------------
            # SAVE MEMORY
            # ------------------------------------------------

            conversation_history.append(
                {
                    "user": user_question,

                    "assistant": final_text
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
            # EXECUTE ANALYSIS
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
            # GENERATE VISUALIZATION
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


        # ====================================================
        # SEND TOOL RESULTS BACK TO GEMINI
        # ====================================================

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
            "user": user_question,

            "assistant": final_text
        }
    )


    return final_text


# ============================================================
# RESET MEMORY
# ============================================================

def reset_conversation():

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


    print(
        "\nDataset loaded successfully."
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
    print("=" * 60)
    print("CONVERSATIONAL MODE")
    print("=" * 60)

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
        # Empty input
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