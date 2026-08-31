from llm import ask_agent
from tools import inspect_dataset, execute_analysis


def run_agent(user_question, df):
    """
    Run the AI Data Analyst agent.

    The agent:
    1. Sends the question to Gemini.
    2. Detects the requested tool.
    3. Executes the tool.
    4. Returns the tool result.
    """

    # -----------------------------------------
    # 1. Build dataset information
    # -----------------------------------------

    dataset_info = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        }
    }

    # -----------------------------------------
    # 2. Ask Gemini what tool to use
    # -----------------------------------------

    response = ask_agent(
        user_question,
        dataset_info
    )

    # -----------------------------------------
    # 3. Look for function calls
    # -----------------------------------------

    for candidate in response.candidates:

        if not candidate.content:
            continue

        if not candidate.content.parts:
            continue

        for part in candidate.content.parts:

            if not part.function_call:
                continue

            function_call = part.function_call

            tool_name = function_call.name
            arguments = function_call.args

            print("\n===== TOOL CALL =====")
            print("Tool:", tool_name)
            print("Arguments:", arguments)

            # -----------------------------------------
            # 4. Execute requested tool
            # -----------------------------------------

            if tool_name == "inspect_dataset":

                result = inspect_dataset(df)

            elif tool_name == "execute_analysis":

                code = arguments["code"]

                result = execute_analysis(
                    code,
                    df
                )

            else:

                result = {
                    "error": f"Unknown tool: {tool_name}"
                }

            # -----------------------------------------
            # 5. Show result
            # -----------------------------------------

            print("\n===== TOOL RESULT =====")
            print(result)

            return result

    return {
        "error": "Gemini did not request a tool."
    }