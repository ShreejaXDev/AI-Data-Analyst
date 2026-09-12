from agent import run_agent


print("=" * 60)
print("AI DATA ANALYST - PHASE 7 TEST")
print("=" * 60)


questions = [

    # ---------------------------------------------
    # DATA QUALITY
    # ---------------------------------------------

    "Are there any duplicate rows in the dataset?",

    "Which columns contain missing values and how many?",


    # ---------------------------------------------
    # NORMAL ANALYSIS
    # ---------------------------------------------

    "What is the average age of passengers?",


    # ---------------------------------------------
    # ERROR RECOVERY
    # ---------------------------------------------

    "What is the average value of the Salary column?",


    # ---------------------------------------------
    # COMPLEX ANALYSIS
    # ---------------------------------------------

    "Compare the average fare and survival rate "
    "for each passenger class.",


    # ---------------------------------------------
    # VISUALIZATION
    # ---------------------------------------------

    "Show the distribution of passenger ages "
    "using an appropriate visualization."

]


for question in questions:

    print("\n")

    print(
        "#" * 60
    )

    print(
        "QUESTION:"
    )

    print(question)

    print(
        "#" * 60
    )

    answer = run_agent(
        question
    )

    print(
        "\nFINAL ANSWER:"
    )

    print(answer)