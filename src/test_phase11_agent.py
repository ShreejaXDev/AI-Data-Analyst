import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_loader import load_csv
from agent import run_agent, reset_conversation


def run_phase11_tests():
    print("=" * 60)
    print("RUNNING PHASE 11 AGENT TESTS")
    print("=" * 60)

    # 1. Test sales.csv questions
    df_sales = load_csv("sales.csv")

    reset_conversation()
    print("\n--- TEST 1 (sales.csv): Smart Overview ---")
    q1 = "Give me a smart overview of this dataset."
    ans1 = run_agent(q1, df_sales, "sales.csv")
    print("\nANSWER 1:")
    print(ans1)

    reset_conversation()
    print("\n--- TEST 2 (sales.csv): Grouping Columns ---")
    q2 = "Which columns are best for grouping the data?"
    ans2 = run_agent(q2, df_sales, "sales.csv")
    print("\nANSWER 2:")
    print(ans2)

    reset_conversation()
    print("\n--- TEST 3 (sales.csv): Numerical Correlations ---")
    q3 = "Which numerical columns are strongly correlated?"
    ans3 = run_agent(q3, df_sales, "sales.csv")
    print("\nANSWER 3:")
    print(ans3)

    # 2. Test train.csv (Titanic) questions
    df_titanic = load_csv("train.csv")

    reset_conversation()
    print("\n--- TEST 4 (train.csv): High Missingness ---")
    q4 = "Which columns have high missingness?"
    ans4 = run_agent(q4, df_titanic, "train.csv")
    print("\nANSWER 4:")
    print(ans4)

    reset_conversation()
    print("\n--- TEST 5 (train.csv): Columns to avoid as measures ---")
    q5 = "Which columns should I avoid using as measures?"
    ans5 = run_agent(q5, df_titanic, "train.csv")
    print("\nANSWER 5:")
    print(ans5)

    print("\n=" * 60)
    print("PHASE 11 AGENT TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase11_tests()
