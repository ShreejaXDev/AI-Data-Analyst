from llm import ask_agent


dataset_info = {
    "rows": 891,
    "columns": 12,
    "column_names": [
        "PassengerId",
        "Survived",
        "Pclass",
        "Name",
        "Sex",
        "Age",
        "SibSp",
        "Parch",
        "Ticket",
        "Fare",
        "Cabin",
        "Embarked"
    ]
}


question = "What is the average age of the passengers?"


response = ask_agent(
    question,
    dataset_info
)


print("\n===== RESPONSE OBJECT =====\n")
print(response)


print("\n===== TEXT =====\n")

if response.text:
    print(response.text)


print("\n===== FUNCTION CALLS =====\n")

for candidate in response.candidates:

    if candidate.content and candidate.content.parts:

        for part in candidate.content.parts:

            if part.function_call:

                print("Tool:", part.function_call.name)
                print("Arguments:", part.function_call.args)