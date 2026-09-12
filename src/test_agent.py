from data_loader import choose_dataset, load_csv
from agent import run_agent


print("=" * 60)
print("AI DATA ANALYST - PHASE 8 TEST")
print("=" * 60)


# ============================================================
# SELECT DATASET
# ============================================================

dataset_name = choose_dataset()


if dataset_name is None:

    print(
        "No CSV datasets available."
    )

    exit()


# ============================================================
# LOAD DATASET
# ============================================================

try:

    df = load_csv(
        dataset_name
    )

except Exception as e:

    print(
        f"Error loading dataset: {e}"
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


# ============================================================
# QUESTIONS
# ============================================================

questions = [

    "Give me a summary of this dataset.",

    "Which columns have missing values?",

    "What are the main numerical columns?",

    "Show me the top 10 records based on the "
    "most appropriate numerical column."

]


# ============================================================
# RUN QUESTIONS
# ============================================================

for question in questions:

    print(
        "\n" + "#" * 60
    )

    print(
        "QUESTION:"
    )

    print(
        question
    )

    print(
        "#" * 60
    )

    answer = run_agent(
        question,
        df,
        dataset_name
    )

    print(
        "\nFINAL ANSWER:"
    )

    print(
        answer
    )