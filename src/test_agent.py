import pandas as pd

from agent import run_agent


print("STEP 1: Starting test...")


# Load Titanic dataset
df = pd.read_csv("data/train.csv")

print("STEP 2: Dataset loaded")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())


# Question
question = "What is the average age of the passengers?"

print("\nSTEP 3: Sending question to agent...")
print("Question:", question)


# Run agent
result = run_agent(
    question,
    df
)


print("\nSTEP 4: Agent finished")

print("\n===== FINAL TOOL RESULT =====")
print(result)