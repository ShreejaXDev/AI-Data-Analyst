import os
import json
import time

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
    parse_plan_response,
    parse_decision_response,
    create_fallback_decision
)


# ============================================================
# SAFE GENERATE CONTENT (RATE LIMIT & NETWORK RETRY HANDLING)
# ============================================================

def safe_generate_content(client, model, contents, config=None, retries=6, delay=10):
    """
    Wrapper around client.models.generate_content to handle rate limits (HTTP 429) and network glitches gracefully.
    """
    for attempt in range(retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if attempt < retries - 1:
                    wait_time = float(delay)
                    if "retry in" in err_str:
                        try:
                            seconds_str = err_str.split("retry in")[1].split("s")[0].strip()
                            wait_time = max(float(seconds_str) + 2.0, float(delay))
                        except Exception:
                            pass
                    print(f"\n[RATE LIMIT]: Gemini API 429 rate limit encountered. Retrying in {wait_time:.1f} seconds (Attempt {attempt + 1}/{retries})...")
                    time.sleep(wait_time)
                    continue
            elif "Server disconnected" in err_str or "RemoteProtocolError" in err_str or "ConnectError" in err_str or "ReadTimeout" in err_str:
                if attempt < retries - 1:
                    print(f"\n[NETWORK RETRY]: Connection reset or network error ({type(e).__name__}). Retrying in 5 seconds (Attempt {attempt + 1}/{retries})...")
                    time.sleep(5)
                    continue
            raise e


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
12. Use the result to decide what should happen next.
13. If the tool returns an error:
    - inspect the error
    - determine the cause
    - correct the code
    - execute again
14. Continue until the analysis succeeds or no useful progress is possible.
15. If visualization is requested, use generate_visualization.
16. Only claim a visualization exists if the tool returned success=True.

==================================================
CONVERSATIONAL MEMORY
==================================================

The user may ask follow-up questions. Use conversation history to resolve
references like 'it', 'its', 'they', 'them', 'that', 'that region', 'that product'.

==================================================
VISUALIZATION
==================================================

Use Matplotlib only. Do not use seaborn or plotly.
Do not call plt.savefig() or plt.close().
"""


# ============================================================
# DATASET CONTEXT
# ============================================================

def get_dataset_context(df):
    """
    Get structured smart profile information about the dataset.
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
    Convert previous conversation turns into clean context for Gemini.
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
# CODE EXTRACTION HELPER
# ============================================================

def extract_code_from_text(text):
    """
    Safely extract Python code from markdown blocks if no tool call structure returned.
    """
    if not text:
        return ""

    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()

    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()

    return text.strip()


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
    Ask Gemini to create an explicit step-by-step analysis plan.
    """

    planner_prompt = f"""
You are the planning component of an AI Data Analyst.

Your job is to create a clear and practical step-by-step plan for answering the user's current question.

==================================================
DATASET: {dataset_name}
==================================================
DATASET PROFILE:
{dataset_context}

==================================================
PREVIOUS CONVERSATION:
{conversation_context}

==================================================
CURRENT QUESTION:
{user_question}

==================================================
PLANNING RULES:
1. Break complex questions into logical steps.
2. Keep simple questions simple.
3. Do not invent columns. Use actual dataset columns from profile.
4. Include calculations that require Python/Pandas.
5. If the user explicitly requests a chart, graph, plot, or visualization, include visualization as a plan step.
6. Return ONLY valid JSON.

Required format:
{{
    "goal": "overall goal",
    "steps": [
        {{
            "step": 1,
            "description": "..."
        }}
    ]
}}
"""

    try:

        response = safe_generate_content(
            client=client,
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

        print(f"\nPlanner warning: {e}. Using fallback plan.")

        return {
            "goal": "Analyze the user's question.",
            "steps": [
                {
                    "step": 1,
                    "description": "Analyze the user's question using the supplied dataset."
                }
            ]
        }


# ============================================================
# PHASE 12: DECIDE NEXT ACTION (AUTONOMOUS DECISION MAKER)
# ============================================================

def decide_next_action(
    user_question,
    dataset_name,
    dataset_context,
    conversation_context,
    plan,
    completed_actions,
    visualization_completed
):
    """
    Autonomous decision-making component.
    Evaluates current evidence against the objective and decides what to do next:
    ANALYZE, VISUALIZE, REPLAN, or FINISH.
    """

    decision_prompt = f"""
You are the autonomous decision-making component of an AI Data Analyst agent.

Your task is to evaluate the evidence gathered so far and decide what action to take next.

==================================================
DATASET: {dataset_name}
==================================================
DATASET PROFILE:
{dataset_context}

==================================================
PREVIOUS CONVERSATION:
{conversation_context}

==================================================
USER QUESTION:
{user_question}

==================================================
EXPLICIT ANALYSIS PLAN:
{json.dumps(plan, indent=2)}

==================================================
COMPLETED ACTIONS & EVIDENCE GATHERED:
{json.dumps(completed_actions, indent=2)}

Visualization already generated: {visualization_completed}

==================================================
DECISION RULES:

1. SUFFICIENCY CHECK: Ask yourself: "Do I have sufficient concrete evidence in COMPLETED ACTIONS (numerical calculations, groupbys, statistics) to answer the user's question completely?"
   - If NO actions have been completed in COMPLETED ACTIONS yet → Choose "ANALYZE" to execute the analysis tool first.
   - If YES (evidence in COMPLETED ACTIONS is sufficient) → Choose "FINISH". Do NOT perform unnecessary or redundant tool calls.
   - If simple single-step question (e.g. "What is average sales?") and calculation is in COMPLETED ACTIONS → Choose "FINISH".

2. MULTI-STEP INVESTIGATION:
   - If the user asks "Why" or asks for deeper breakdown, evaluate if more analysis is needed to explain the result.
   - If more data is needed → Choose "ANALYZE" and describe the specific `next_action`.

3. VISUALIZATION:
   - If user explicitly requested a chart/plot/graph AND visualization has NOT succeeded yet → Choose "VISUALIZE".
   - If visualization materially helps illustrate the findings AND has NOT succeeded yet → Choose "VISUALIZE".
   - Otherwise, do NOT choose "VISUALIZE" just for decoration.

4. REPLANNING:
   - If intermediate findings make the current plan invalid or suggest a better path → Choose "REPLAN".

5. EFFICIENCY:
   - Avoid redundant actions. If an action was already completed, do NOT repeat it.

Return ONLY valid JSON matching this schema:

{{
    "decision": "ANALYZE" | "VISUALIZE" | "REPLAN" | "FINISH",
    "reason": "Detailed explanation of why this decision was made",
    "next_action": "Specific operational instruction for the next action (required if ANALYZE, VISUALIZE, or REPLAN)"
}}
"""

    try:

        response = safe_generate_content(
            client=client,
            model=MODEL_NAME,
            contents=decision_prompt,
            config={
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        )

        return parse_decision_response(response.text)

    except Exception as e:

        print(f"\nDecision Maker warning: {e}. Using fallback.")

        if completed_actions:
            return {
                "decision": "FINISH",
                "reason": "Sufficient evidence collected before decision exception.",
                "next_action": ""
            }

        return create_fallback_decision(str(e))


# ============================================================
# PHASE 12: GENERATE EVIDENCE-GROUNDED FINAL ANSWER
# ============================================================

def generate_final_answer(
    user_question,
    dataset_name,
    dataset_context,
    conversation_context,
    completed_actions
):
    """
    Generate an evidence-grounded final answer based strictly on tool results.
    """

    answer_prompt = f"""
You are an AI Data Analyst. Synthesize a concise, user-friendly final answer to the user's question.

==================================================
DATASET: {dataset_name}
USER QUESTION: {user_question}
==================================================
PREVIOUS CONVERSATION:
{conversation_context}

==================================================
COMPLETED ACTIONS & EVIDENCE GATHERED:
{json.dumps(completed_actions, indent=2)}

==================================================
RULES:
1. Base your answer EXCLUSIVELY on the tool observations in COMPLETED ACTIONS.
2. Never invent numbers, percentages, or statistics.
3. If visualization succeeded, mention that a chart was created.
4. Keep the response clean, professional, concise, and clear.
"""

    response = safe_generate_content(
        client=client,
        model=MODEL_NAME,
        contents=answer_prompt,
        config={
            "temperature": 0.2
        }
    )

    return response.text.strip()


# ============================================================
# RUN AGENT (PHASE 12 AUTONOMOUS LOOP)
# ============================================================

def run_agent(
    user_question,
    df,
    dataset_name
):

    print()
    print("=" * 60)
    print("SELECTED DATASET")
    print("=" * 60)
    print(dataset_name)

    print()
    print("=" * 60)
    print("USER QUESTION")
    print("=" * 60)
    print(user_question)

    # --------------------------------------------------------
    # CONTEXT PREPARATION
    # --------------------------------------------------------

    dataset_context = get_dataset_context(df)
    conversation_context = get_conversation_context()

    # --------------------------------------------------------
    # CREATE INITIAL PLAN
    # --------------------------------------------------------

    plan = create_plan(
        user_question,
        dataset_name,
        dataset_context,
        conversation_context
    )

    print()
    print("=" * 60)
    print("AGENT PLAN")
    print("=" * 60)
    print(format_plan(plan))
    print("=" * 60)

    # --------------------------------------------------------
    # STATE TRACKING
    # --------------------------------------------------------

    completed_actions = []
    visualization_completed = False
    visualization_path = None
    max_iterations = 8

    # --------------------------------------------------------
    # PHASE 12 AUTONOMOUS DECISION LOOP
    # --------------------------------------------------------

    for iteration in range(1, max_iterations + 1):

        print()
        print(f"===== AGENT ITERATION {iteration} =====")

        # 1. Decision Maker decides next action
        decision_info = decide_next_action(
            user_question,
            dataset_name,
            dataset_context,
            conversation_context,
            plan,
            completed_actions,
            visualization_completed
        )

        decision = decision_info.get("decision", "ANALYZE")
        reason = decision_info.get("reason", "")
        next_action = decision_info.get("next_action", "")

        print(f"\n[DECISION]: {decision}")
        print(f"[REASON]: {reason}")
        if next_action:
            print(f"[NEXT ACTION]: {next_action}")

        # ----------------------------------------------------
        # DECISION: FINISH
        # ----------------------------------------------------
        if decision == "FINISH":
            final_text = generate_final_answer(
                user_question,
                dataset_name,
                dataset_context,
                conversation_context,
                completed_actions
            )

            conversation_history.append({
                "user": user_question,
                "assistant": final_text
            })

            return final_text

        # ----------------------------------------------------
        # DECISION: REPLAN
        # ----------------------------------------------------
        if decision == "REPLAN":
            print("\nReplanning based on intermediate findings...")
            plan = create_plan(
                user_question + f" (Context update: {reason})",
                dataset_name,
                dataset_context,
                conversation_context
            )
            print()
            print("=" * 60)
            print("NEW AGENT PLAN")
            print("=" * 60)
            print(format_plan(plan))
            print("=" * 60)
            continue

        # ----------------------------------------------------
        # DECISION: ANALYZE
        # ----------------------------------------------------
        if decision == "ANALYZE":

            code_gen_prompt = f"""
Dataset: {dataset_name}
Profile:
{dataset_context}

Previous conversation:
{conversation_context}

User question: {user_question}
Current action goal: {next_action}
Evidence gathered so far:
{json.dumps(completed_actions, indent=2)}

Generate Python/Pandas code to accomplish this step.
Assign the final calculated output to variable `result`.
DataFrame is available as `df`. Pandas is available as `pd`.

Call execute_analysis(code=...).
"""

            resp = safe_generate_content(
                client=client,
                model=MODEL_NAME,
                contents=code_gen_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "tools": [{"function_declarations": [execute_analysis_tool]}]
                }
            )

            code = None
            if resp.function_calls:
                for fc in resp.function_calls:
                    if fc.name == "execute_analysis":
                        code = fc.args.get("code")

            if not code:
                code = extract_code_from_text(resp.text)

            print()
            print("===== TOOL CALL =====")
            print("Tool: execute_analysis")
            print("Arguments:")
            print({"code": code})

            if not code:
                tool_res = {
                    "success": False,
                    "error": "No Python code generated.",
                    "error_type": "MissingCode"
                }
            else:
                tool_res = execute_analysis(code, df)

            # Error Recovery (Phase 7)
            if not tool_res.get("success", False):
                print()
                print("[ERROR RECOVERY]: Tool returned error, attempting fix...")
                fix_prompt = f"""
Tool execution failed with error: {tool_res.get('error')}
Failed code:
{code}
Dataset information:
{dataset_context}

Generate corrected Python code. Assign the result to `result`.
"""
                fix_resp = safe_generate_content(
                    client=client,
                    model=MODEL_NAME,
                    contents=fix_prompt,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "tools": [{"function_declarations": [execute_analysis_tool]}]
                    }
                )
                fixed_code = None
                if fix_resp.function_calls:
                    for fc in fix_resp.function_calls:
                        if fc.name == "execute_analysis":
                            fixed_code = fc.args.get("code")

                if not fixed_code:
                    fixed_code = extract_code_from_text(fix_resp.text)

                if fixed_code:
                    code = fixed_code
                    tool_res = execute_analysis(code, df)

            print()
            print("===== TOOL RESULT =====")
            print(tool_res)

            completed_actions.append({
                "iteration": iteration,
                "action": "ANALYZE",
                "description": next_action,
                "code": code,
                "result": tool_res
            })
            continue

        # ----------------------------------------------------
        # DECISION: VISUALIZE
        # ----------------------------------------------------
        if decision == "VISUALIZE":

            viz_gen_prompt = f"""
Dataset: {dataset_name}
Profile:
{dataset_context}

User question: {user_question}
Visualization goal: {next_action}
Evidence gathered so far:
{json.dumps(completed_actions, indent=2)}

Generate Matplotlib visualization code.
Rules:
- Matplotlib only. No seaborn, no plotly.
- Do NOT call plt.savefig() or plt.close().
- DataFrame is `df`, Pandas is `pd`, Matplotlib.pyplot is `plt`.

Call generate_visualization(code=...).
"""

            resp = safe_generate_content(
                client=client,
                model=MODEL_NAME,
                contents=viz_gen_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "tools": [{"function_declarations": [generate_visualization_tool]}]
                }
            )

            code = None
            if resp.function_calls:
                for fc in resp.function_calls:
                    if fc.name == "generate_visualization":
                        code = fc.args.get("code")

            if not code:
                code = extract_code_from_text(resp.text)

            print()
            print("===== TOOL CALL =====")
            print("Tool: generate_visualization")
            print("Arguments:")
            print({"code": code})

            if not code:
                tool_res = {
                    "success": False,
                    "error": "No visualization code generated.",
                    "error_type": "MissingCode"
                }
            else:
                tool_res = generate_visualization(code, df)

            # Error Recovery (Phase 7)
            if not tool_res.get("success", False):
                print()
                print("[ERROR RECOVERY]: Visualization failed, attempting fix...")
                fix_prompt = f"""
Visualization code failed with error: {tool_res.get('error')}
Failed code:
{code}

Generate corrected Matplotlib code.
"""
                fix_resp = safe_generate_content(
                    client=client,
                    model=MODEL_NAME,
                    contents=fix_prompt,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "tools": [{"function_declarations": [generate_visualization_tool]}]
                    }
                )
                fixed_code = None
                if fix_resp.function_calls:
                    for fc in fix_resp.function_calls:
                        if fc.name == "generate_visualization":
                            fixed_code = fc.args.get("code")

                if not fixed_code:
                    fixed_code = extract_code_from_text(fix_resp.text)

                if fixed_code:
                    code = fixed_code
                    tool_res = generate_visualization(code, df)

            print()
            print("===== TOOL RESULT =====")
            print(tool_res)

            if tool_res.get("success", False):
                visualization_completed = True
                visualization_path = tool_res.get("path")

            completed_actions.append({
                "iteration": iteration,
                "action": "VISUALIZE",
                "description": next_action,
                "code": code,
                "result": tool_res
            })
            continue

    # Max Iterations reached fallback
    final_text = generate_final_answer(
        user_question,
        dataset_name,
        dataset_context,
        conversation_context,
        completed_actions
    )

    conversation_history.append({
        "user": user_question,
        "assistant": final_text
    })

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
        print("No dataset available.")
        exit()

    try:
        df = load_csv(dataset_name)
    except Exception as e:
        print(f"\nError loading dataset: {e}")
        exit()

    print()
    print("Dataset loaded successfully.")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print()
    print("=" * 60)
    print("CONVERSATIONAL MODE (PHASE 12 AUTONOMOUS AGENT)")
    print("=" * 60)
    print()
    print("Ask questions about your dataset.")
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'clear' to reset conversation memory.")
    print()

    while True:

        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not question:
            print("Please enter a question.")
            continue

        if question.lower() in ["exit", "quit"]:
            print("\nGoodbye! 👋")
            break

        if question.lower() == "clear":
            reset_conversation()
            print("\nConversation memory cleared.\n")
            continue

        try:
            answer = run_agent(
                question,
                df,
                dataset_name
            )

            print()
            print("FINAL ANSWER:")
            print(answer)
            print()

        except Exception as e:
            print("\nAgent Error:")
            print(str(e))
            print()