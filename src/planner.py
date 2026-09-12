import json


# ============================================================
# PLAN VALIDATION
# ============================================================

def validate_plan(plan):
    """
    Validate the structure of an analysis plan.
    """

    if not isinstance(plan, dict):
        return False

    if "goal" not in plan:
        return False

    if "steps" not in plan:
        return False

    if not isinstance(plan["goal"], str):
        return False

    if not isinstance(plan["steps"], list):
        return False

    if len(plan["steps"]) == 0:
        return False

    for step in plan["steps"]:

        if not isinstance(step, dict):
            return False

        if "step" not in step:
            return False

        if "description" not in step:
            return False

        if not isinstance(step["step"], int):
            return False

        if not isinstance(step["description"], str):
            return False

    return True


# ============================================================
# PLAN FORMATTER
# ============================================================

def format_plan(plan):
    """
    Convert a plan into readable text.
    """

    if not validate_plan(plan):
        return "Invalid plan."

    lines = []

    lines.append(
        f"Goal: {plan['goal']}"
    )

    lines.append("")
    lines.append("Steps:")

    for step in plan["steps"]:

        lines.append(
            f"{step['step']}. "
            f"{step['description']}"
        )

    return "\n".join(lines)


# ============================================================
# EXECUTION STATE
# ============================================================

def initialize_execution_state(plan):
    """
    Create execution state for every plan step.
    """

    state = []

    for step in plan["steps"]:

        state.append(
            {
                "step": step["step"],
                "description": step["description"],
                "status": "pending",
                "observation": ""
            }
        )

    return state


# ============================================================
# EXECUTION STATE FORMATTER
# ============================================================

def format_execution_state(execution_state):
    """
    Convert execution state into readable text.
    """

    lines = []

    for item in execution_state:

        status = item["status"].upper()

        lines.append(
            f"Step {item['step']}: "
            f"{status} - "
            f"{item['description']}"
        )

        if item.get("observation"):

            lines.append(
                f"    Observation: "
                f"{item['observation']}"
            )

    return "\n".join(lines)


# ============================================================
# UPDATE STEP
# ============================================================

def update_step(
    execution_state,
    step_number,
    status,
    observation=""
):
    """
    Update the status of one execution step.
    """

    for item in execution_state:

        if item["step"] == step_number:

            item["status"] = status
            item["observation"] = observation

            return execution_state

    return execution_state


# ============================================================
# CHECK PLAN COMPLETION
# ============================================================

def is_plan_complete(execution_state):
    """
    Return True if every step is completed.
    """

    if not execution_state:
        return False

    return all(
        item["status"] == "completed"
        for item in execution_state
    )


# ============================================================
# FALLBACK PLAN
# ============================================================

def create_fallback_plan():
    """
    Safe fallback if Gemini returns invalid planner output.
    """

    return {
        "goal": "Analyze the user's question.",
        "steps": [
            {
                "step": 1,
                "description": (
                    "Analyze the user's question "
                    "using the supplied dataset."
                )
            }
        ]
    }


# ============================================================
# SAFE JSON PARSING
# ============================================================

def parse_plan_response(response_text):
    """
    Safely parse Gemini's planner response.
    """

    if not response_text:

        return create_fallback_plan()

    text = response_text.strip()

    # --------------------------------------------------------
    # Remove markdown fences
    # --------------------------------------------------------

    if text.startswith("```json"):

        text = text[7:]

    elif text.startswith("```"):

        text = text[3:]

    if text.endswith("```"):

        text = text[:-3]

    text = text.strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        plan = json.loads(text)

    except json.JSONDecodeError:

        return create_fallback_plan()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if not validate_plan(plan):

        return create_fallback_plan()

    return plan


# ============================================================
# PARSE EXECUTION UPDATE
# ============================================================

def parse_execution_update(response_text):
    """
    Parse Gemini's execution/replanning decision.

    Expected format:

    {
        "completed_steps": [1],
        "in_progress_step": 2,
        "replanned_steps": [],
        "should_finish": false,
        "reason": "..."
    }
    """

    if not response_text:

        return {
            "completed_steps": [],
            "in_progress_step": None,
            "replanned_steps": [],
            "should_finish": False,
            "reason": ""
        }

    text = response_text.strip()

    if text.startswith("```json"):

        text = text[7:]

    elif text.startswith("```"):

        text = text[3:]

    if text.endswith("```"):

        text = text[:-3]

    text = text.strip()

    try:

        update = json.loads(text)

    except json.JSONDecodeError:

        return {
            "completed_steps": [],
            "in_progress_step": None,
            "replanned_steps": [],
            "should_finish": False,
            "reason": ""
        }

    if not isinstance(update, dict):

        return {
            "completed_steps": [],
            "in_progress_step": None,
            "replanned_steps": [],
            "should_finish": False,
            "reason": ""
        }

    update.setdefault(
        "completed_steps",
        []
    )

    update.setdefault(
        "in_progress_step",
        None
    )

    update.setdefault(
        "replanned_steps",
        []
    )

    update.setdefault(
        "should_finish",
        False
    )

    update.setdefault(
        "reason",
        ""
    )

    return update