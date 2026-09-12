from agent import run_agent


print("=" * 60)
print("AI DATA ANALYST - PHASE 6 TEST")
print("=" * 60)


questions = [

    "Which passenger class had the highest survival rate?",

    "Show me the top 10 passengers who paid the highest fare.",

    "Which columns have missing values?",

    "What is the average age of passengers?",

    "What is the relationship between Age and Fare?",

    "Compare the survival rate of males and females."

]


for question in questions:

    print("\n")
    print("#" * 60)
    print("QUESTION:")
    print(question)
    print("#" * 60)

    answer = run_agent(question)

    print("\nFINAL ANSWER:")
    print(answer)