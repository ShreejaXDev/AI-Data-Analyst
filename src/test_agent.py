import pandas as pd

from agent import run_agent


# ==================================================
# START
# ==================================================

print(
    "STEP 1: Starting AI Data Analyst..."
)


# ==================================================
# LOAD DATASET
# ==================================================

df = pd.read_csv(
    "data/train.csv"
)


print(
    "\nSTEP 2: Dataset loaded"
)

print(
    "Shape:",
    df.shape
)

print(
    "Columns:",
    df.columns.tolist()
)


# ==================================================
# USER QUESTION
# ==================================================
question = """
Show me the survival rate for each passenger class
and create an appropriate visualization.
"""


print(
    "\nSTEP 3: Sending question to agent..."
)

print(
    "Question:",
    question
)


# ==================================================
# RUN AGENT
# ==================================================

final_answer = run_agent(
    question,
    df
)


# ==================================================
# FINAL RESULT
# ==================================================

print(
    "\nSTEP 4: Agent finished"
)

print(
    "\n======================================"
)

print(
    "FINAL ANSWER"
)

print(
    "======================================"
)

print(
    final_answer
)