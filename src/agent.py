from llm import create_chat
from google.genai import types

from tools import (
    inspect_dataset,
    execute_analysis
)


def run_agent(user_question, df):

    # ==================================================
    # DATASET INFORMATION
    # ==================================================

    dataset_info = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        }
    }

    print("\n===== DATASET INFO =====")
    print(dataset_info)


    # ==================================================
    # CREATE CHAT
    # ==================================================

    chat = create_chat()


    # ==================================================
    # INITIAL PROMPT
    # ==================================================

    prompt = f"""
You are an AI Data Analyst Agent.

You are working with a Pandas DataFrame called df.

Dataset information:

{dataset_info}

User question:

{user_question}

Available tools:

1. inspect_dataset
   Use this to inspect the dataset structure.

2. execute_analysis
   Use this to perform Python calculations
   and analysis.

You may call tools multiple times.

After receiving a tool result, decide whether
you need another tool.

When you have enough information, give the
user a clear final answer.

Never invent numerical results.
"""


    # ==================================================
    # AGENT LOOP
    # ==================================================

    max_iterations = 5

    response = chat.send_message(prompt)


    for iteration in range(max_iterations):

        print(
            f"\n===== AGENT ITERATION "
            f"{iteration + 1} ====="
        )


        tool_called = False


        # ==================================================
        # CHECK RESPONSE
        # ==================================================

        for candidate in response.candidates:

            if not candidate.content:
                continue

            if not candidate.content.parts:
                continue


            for part in candidate.content.parts:

                # ------------------------------------------
                # TEXT RESPONSE
                # ------------------------------------------

                if part.text:

                    print("\nAGENT:")
                    print(part.text)


                # ------------------------------------------
                # FUNCTION CALL
                # ------------------------------------------

                if not part.function_call:
                    continue


                tool_called = True

                function_call = part.function_call

                tool_name = function_call.name

                arguments = function_call.args


                print("\n===== TOOL CALL =====")
                print("Tool:", tool_name)
                print("Arguments:", arguments)


                # ==================================================
                # EXECUTE TOOL
                # ==================================================

                if tool_name == "inspect_dataset":

                    tool_result = inspect_dataset(df)


                elif tool_name == "execute_analysis":

                    code = arguments["code"]

                    tool_result = execute_analysis(
                        code,
                        df
                    )


                else:

                    tool_result = {
                        "error": f"Unknown tool: {tool_name}"
                    }


                print("\n===== TOOL RESULT =====")
                print(tool_result)


                # ==================================================
                # SEND TOOL RESULT BACK TO GEMINI
                # ==================================================

                response = chat.send_message(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=tool_name,
                            response={
                                "result": tool_result
                            }
                        )
                    )
                )


                break


            if tool_called:
                break


        # ==================================================
        # NO TOOL CALL = FINAL ANSWER
        # ==================================================

        if not tool_called:

            print("\n===== FINAL ANSWER =====")

            return response.text


    return (
        "The agent reached the maximum number "
        "of analysis steps."
    )