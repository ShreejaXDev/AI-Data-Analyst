import pandas as pd

from agent import run_agent


print("STEP 1: Starting test...")


df = pd.read_csv("data/train.csv")


print("STEP 2: Dataset loaded")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())

question = "Which passenger class had the highest survival rate?"

print("\nSTEP 3: Sending question to agent...")
print("Question:", question)


final_answer = run_agent(
    question,
    df
)


print("\nSTEP 4: Agent finished")

print("\n===== FINAL ANSWER =====")
print(final_answer)