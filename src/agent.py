import os
import json
import time

from dotenv import load_dotenv
from google import genai

from tools import (
    inspect_dataset,
    execute_analysis,
    generate_visualization,
    execute_transformation,
    export_dataset
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
# CONVERSATION MEMORY & ACTIVE WORKING DATAFRAME STATE
# ============================================================

conversation_history = []
active_working_df = None
active_dataset_name = None


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


execute_transformation_tool = {

    "name": "execute_transformation",

    "description": """
Execute Python Pandas data transformation or cleaning code on active_df.

The active working dataframe is available as `df`.
Pandas is available as `pd`, NumPy as `np`.

Rules:
- Modify `df` in-place or assign updated DataFrame back to `df` or `result`.
- Examples:
  df['Age'] = df['Age'].fillna(df['Age'].median())
  df = df.drop_duplicates()
  df['Date'] = pd.to_datetime(df['Date'])
- The system automatically validates the transformation result and creates an audit record.
""",

    "parameters": {

        "type": "object",

        "properties": {

            "code": {
                "type": "string",
                "description": "Python/Pandas data transformation code."
            }

        },

        "required": [
            "code"
        ]
    }
}


export_dataset_tool = {

    "name": "export_dataset",

    "description": """
Export and save the active transformed dataset to a CSV file.
Default output path is outputs/cleaned_<dataset_name>.
""",

    "parameters": {

        "type": "object",

        "properties": {

            "output_path": {
                "type": "string",
                "description": "Optional custom export output path."
            }

        }
    }
}


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """

You are a general-purpose AI Data Analyst agent equipped with Intelligent Data Cleaning and Transformation capabilities.

You analyze, clean, and transform ANY CSV dataset supplied by the user.

==================================================
SMART DATA PROFILE & CLEANING RECOMMENDATIONS
==================================================

You receive a comprehensive, deterministic dataset profile and auto-detected cleaning recommendations before planning and execution.

Use this profile to:
- Inspect exact row counts, columns, data types, missing values, duplicates, and correlations.
- Pay attention to `cleaning_recommendations` for missing value imputation, duplicate removal, or date parsing.
- Recognize when data cleaning/transformation is required before analysis or explicit in user requests.

==================================================
DATA TRANSFORMATION RULES
==================================================

1. Do NOT silently clean data without recording the reason and transformation action.
2. Do NOT drop rows, fill missing values, drop columns, or convert types UNLESS requested by the user OR necessary for analysis.
3. Every transformation modifies a working active DataFrame `df`.
4. The system validates every transformation, creates a structured audit record, and re-profiles the dataset.
5. If requested to save or export, use `EXPORT_DATA` to write the cleaned dataset safely to outputs/ cleaned_<name>.csv without overwriting the source dataset.

==================================================
CORE WORKFLOW
==================================================

1. Understand the user's question or request (analysis, cleaning, visualization, or export).
2. Consider previous conversation history.
3. Use the explicit plan and dataset profile.
4. Decide appropriate action: ANALYZE, TRANSFORM, VISUALIZE, EXPORT_DATA, REPLAN, or FINISH.
5. Execute code using tools: execute_analysis, execute_transformation, generate_visualization, or export_dataset.
6. Observe results and audit trailing metrics.
7. Synthesize an evidence-grounded final answer.
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
6. If the user asks to save or export the dataset without explicitly requesting new cleaning steps, the plan should consist of a single step to export the active dataset.
7. Return ONLY valid JSON.

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
    ANALYZE, TRANSFORM, VISUALIZE, EXPORT_DATA, REPLAN, or FINISH.
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

1. DATA TRANSFORMATION & CLEANING:
   - Choose "TRANSFORM" ONLY if the user explicitly asks to clean data, fill/impute missing values, drop duplicates, convert data types, rename columns, filter outliers, or modify the dataset.
   - Do NOT choose "TRANSFORM" for simple questions or export requests.

2. EXPORTING DATASET:
   - If the user asks to save, export, or write out the dataset to a CSV file (e.g. "Save the dataset to CSV") AND did NOT explicitly request new data cleaning/transformation operations in the prompt -> Choose "EXPORT_DATA" directly.
   - Do NOT execute unrequested data cleaning or transformation steps before exporting if the user only requested to save/export the dataset.

3. SUFFICIENCY CHECK & INFORMATIONAL QUESTIONS:
   - If the user asked an informational question (e.g., "How many missing values in Age?", "What are the columns?") and the exact answer is present in DATASET PROFILE -> Choose "FINISH".
   - If analytical calculations are required and not yet in COMPLETED ACTIONS -> Choose "ANALYZE".
   - If evidence in COMPLETED ACTIONS is sufficient -> Choose "FINISH".

4. MULTI-STEP INVESTIGATION:
   - If the user asks "Why" or asks for deeper breakdown, evaluate if more analysis is needed to explain the result. Choose "ANALYZE" if needed.

5. VISUALIZATION:
   - If user explicitly requested a chart/plot/graph AND visualization has NOT succeeded yet -> Choose "VISUALIZE".

6. REPLANNING:
   - If intermediate findings make the current plan invalid or suggest a better path -> Choose "REPLAN".

7. EFFICIENCY:
   - Avoid redundant actions. If an action was already completed, do NOT repeat it.

Return ONLY valid JSON matching this schema:

{{
    "decision": "ANALYZE" | "TRANSFORM" | "VISUALIZE" | "EXPORT_DATA" | "REPLAN" | "FINISH",
    "reason": "Detailed explanation of why this decision was made",
    "next_action": "Specific operational instruction for the next action (required if ANALYZE, TRANSFORM, VISUALIZE, EXPORT_DATA, or REPLAN)"
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
    Generate an evidence-grounded final answer based on dataset profile and tool results.
    """

    answer_prompt = f"""
You are an AI Data Analyst. Synthesize a concise, user-friendly final answer to the user's question.

==================================================
DATASET: {dataset_name}
USER QUESTION: {user_question}
==================================================
DATASET PROFILE & INFORMATION:
{dataset_context}

==================================================
PREVIOUS CONVERSATION:
{conversation_context}

==================================================
COMPLETED ACTIONS & EVIDENCE GATHERED:
{json.dumps(completed_actions, indent=2)}

==================================================
RULES:
1. Base your answer on the DATASET PROFILE and observations in COMPLETED ACTIONS.
2. If the user asked an informational question (such as missing value counts, row/column counts, or statistics) and the answer is present in DATASET PROFILE, answer directly using the exact numbers from DATASET PROFILE (even if COMPLETED ACTIONS is empty).
3. Never invent numbers, percentages, or statistics not present in DATASET PROFILE or COMPLETED ACTIONS.
4. If visualization succeeded, mention that a chart was created.
5. If transformations were performed, clearly summarize the cleaning actions and audit details.
6. Keep the response clean, professional, concise, and clear.
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
    dataset_name,
    return_active_df=False,
    return_details=False
):
    global active_working_df, active_dataset_name

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
    # STATEFUL ACTIVE DATAFRAME PERSISTENCE ACROSS TURNS
    # --------------------------------------------------------

    if active_working_df is None or active_dataset_name != dataset_name:
        active_working_df = df.copy()
        active_dataset_name = dataset_name

    active_df = active_working_df
    transformation_history = []

    # --------------------------------------------------------
    # CONTEXT PREPARATION
    # --------------------------------------------------------

    dataset_context = get_dataset_context(active_df)
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
    # AUTONOMOUS DECISION LOOP (PHASE 13)
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

            if return_details:
                return final_text, active_df, completed_actions
            if return_active_df:
                return final_text, active_df
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
        # DECISION: TRANSFORM (PHASE 13)
        # ----------------------------------------------------
        if decision == "TRANSFORM":

            trans_gen_prompt = f"""
Dataset: {dataset_name}
Profile:
{dataset_context}

Previous conversation:
{conversation_context}

User question: {user_question}
Transformation goal: {next_action}
Evidence gathered so far:
{json.dumps(completed_actions, indent=2)}

Generate Python/Pandas transformation code to clean or transform the active DataFrame `df`.
Rules:
- Modify `df` in-place or assign updated DataFrame back to `df` or `result`.
- Examples:
  df['Age'] = df['Age'].fillna(df['Age'].median())
  df = df.drop_duplicates()
  df['Date'] = pd.to_datetime(df['Date'])
- Do NOT read from disk or overwrite files in code.

Call execute_transformation(code=...).
"""

            resp = safe_generate_content(
                client=client,
                model=MODEL_NAME,
                contents=trans_gen_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "tools": [{"function_declarations": [execute_transformation_tool]}]
                }
            )

            code = None
            if resp.function_calls:
                for fc in resp.function_calls:
                    if fc.name == "execute_transformation":
                        code = fc.args.get("code")

            if not code:
                code = extract_code_from_text(resp.text)

            print()
            print("===== TOOL CALL =====")
            print("Tool: execute_transformation")
            print("Arguments:")
            print({"code": code})

            if not code:
                tool_res = {
                    "success": False,
                    "error": "No transformation code generated.",
                    "active_df": active_df,
                    "audit": {"success": False, "error": "No code generated."}
                }
            else:
                tool_res = execute_transformation(code, active_df, description=next_action)

            # Error Recovery (Phase 7)
            if not tool_res.get("success", False):
                print()
                print("[ERROR RECOVERY]: Transformation failed, attempting fix...")
                fix_prompt = f"""
Transformation failed or validation failed with error: {tool_res.get('error')}
Failed code:
{code}
Dataset profile:
{dataset_context}

Generate corrected Python code to transform DataFrame `df`.
"""
                fix_resp = safe_generate_content(
                    client=client,
                    model=MODEL_NAME,
                    contents=fix_prompt,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "tools": [{"function_declarations": [execute_transformation_tool]}]
                    }
                )
                fixed_code = None
                if fix_resp.function_calls:
                    for fc in fix_resp.function_calls:
                        if fc.name == "execute_transformation":
                            fixed_code = fc.args.get("code")

                if not fixed_code:
                    fixed_code = extract_code_from_text(fix_resp.text)

                if fixed_code:
                    code = fixed_code
                    tool_res = execute_transformation(code, active_df, description=next_action)

            print()
            print("===== TOOL RESULT =====")
            print({"success": tool_res.get("success"), "audit": tool_res.get("audit"), "error": tool_res.get("error")})

            if tool_res.get("success", False):
                active_working_df = tool_res["active_df"]
                active_df = active_working_df
                audit = tool_res.get("audit", {})
                transformation_history.append(audit)
                # Re-profile dataset post-transformation!
                dataset_context = get_dataset_context(active_df)

            completed_actions.append({
                "iteration": iteration,
                "action": "TRANSFORM",
                "description": next_action,
                "code": code,
                "result": tool_res.get("audit", tool_res)
            })
            continue

        # ----------------------------------------------------
        # DECISION: EXPORT_DATA (PHASE 13)
        # ----------------------------------------------------
        if decision == "EXPORT_DATA":

            print()
            print("===== TOOL CALL =====")
            print("Tool: export_dataset")
            print("Arguments:")
            print({"dataset_name": dataset_name})

            export_res = export_dataset(active_df, dataset_name=dataset_name)

            print()
            print("===== TOOL RESULT =====")
            print(export_res)

            completed_actions.append({
                "iteration": iteration,
                "action": "EXPORT_DATA",
                "description": next_action,
                "result": export_res
            })
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
                tool_res = execute_analysis(code, active_df)

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
                    tool_res = execute_analysis(code, active_df)

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
                tool_res = generate_visualization(code, active_df)

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
                    tool_res = generate_visualization(code, active_df)

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

    if return_details:
        return final_text, active_df, completed_actions
    if return_active_df:
        return final_text, active_df
    return final_text


# ============================================================
# RESET CONVERSATION
# ============================================================

def reset_conversation():

    """
    Clear conversational memory and active working DataFrame session state.
    """

    global active_working_df, active_dataset_name

    conversation_history.clear()
    active_working_df = None
    active_dataset_name = None


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