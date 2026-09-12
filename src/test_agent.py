from data_loader import choose_dataset, load_csv
from agent import run_agent, reset_conversation


# ============================================================
# PHASE 9
# CONVERSATIONAL AI DATA ANALYST
# ============================================================

print("=" * 60)
print("AI DATA ANALYST - PHASE 9")
print("=" * 60)


# ============================================================
# SELECT DATASET
# ============================================================

dataset_name = choose_dataset()


if dataset_name is None:

    print(
        "\nNo dataset selected."
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
        f"\nError loading dataset: {e}"
    )

    exit()


print()
print(
    f"Selected dataset: {dataset_name}"
)

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
# CONVERSATION
# ============================================================

print()
print("#" * 60)
print("CONVERSATIONAL MODE")
print("#" * 60)

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


    # --------------------------------------------------------
    # Empty question
    # --------------------------------------------------------

    if not question:

        print(
            "Please enter a question."
        )

        continue


    # --------------------------------------------------------
    # EXIT
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
    # CLEAR MEMORY
    # --------------------------------------------------------

    if question.lower() == "clear":

        reset_conversation()

        print()
        print(
            "Conversation memory cleared."
        )

        print()

        continue


    # --------------------------------------------------------
    # ASK AGENT
    # --------------------------------------------------------

    try:

        answer = run_agent(
            question,
            df,
            dataset_name
        )

        print()
        print(
            "AI:"
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