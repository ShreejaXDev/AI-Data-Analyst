from agent import (
    run_agent,
    reset_conversation
)

from data_loader import (
    choose_dataset,
    load_csv
)


print(
    "=" * 60
)

print(
    "AI DATA ANALYST - PHASE 10"
)

print(
    "=" * 60
)


# ============================================================
# DATASET SELECTION
# ============================================================

selected_dataset = choose_dataset()

if not selected_dataset:

    print(
        "No dataset selected."
    )

    exit()


print()
print(
    f"Selected dataset: {selected_dataset}"
)


df = load_csv(
    selected_dataset
)

if df is None:

    print(
        "Failed to load dataset."
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


# ============================================================
# CONVERSATIONAL MODE
# ============================================================

print()
print(
    "#" * 60
)

print(
    "CONVERSATIONAL MODE"
)

print(
    "#" * 60
)

print()
print(
    "Ask any question about your dataset."
)

print(
    "Type 'exit' or 'quit' to stop."
)

print(
    "Type 'clear' to clear conversation memory."
)


# ============================================================
# QUESTION LOOP
# ============================================================

while True:

    try:

        question = input(
            "\nYou: "
        ).strip()

    except KeyboardInterrupt:

        print()
        print(
            "Goodbye! 👋"
        )

        break

    if not question:

        continue

    # --------------------------------------------------------
    # Exit
    # --------------------------------------------------------

    if question.lower() in [
        "exit",
        "quit"
    ]:

        print()
        print(
            "Goodbye! 👋"
        )

        break

    # --------------------------------------------------------
    # Clear memory
    # --------------------------------------------------------

    if question.lower() == "clear":

        reset_conversation()

        continue

    # --------------------------------------------------------
    # Run agent
    # --------------------------------------------------------

    run_agent(
        question,
        df,
        selected_dataset
    )