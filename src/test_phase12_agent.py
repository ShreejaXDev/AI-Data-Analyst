import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_loader import load_csv
from agent import run_agent, reset_conversation
from planner import parse_decision_response, validate_decision


def test_decision_parser_unit():
    print("Testing planner decision parser unit tests...")
    d1 = parse_decision_response('{"decision": "ANALYZE", "reason": "Test reason", "next_action": "Do something"}')
    assert d1["decision"] == "ANALYZE"
    assert d1["reason"] == "Test reason"

    d2 = parse_decision_response('```json\n{"decision": "finish", "reason": "Done"}\n```')
    assert d2["decision"] == "FINISH"

    d3 = parse_decision_response("invalid json")
    assert d3["decision"] == "ANALYZE"

    print("SUCCESS: Planner decision parser unit tests PASSED!")


def run_phase12_integration_tests():
    print("=" * 60)
    print("RUNNING PHASE 12 AUTONOMOUS AGENT INTEGRATION TESTS")
    print("=" * 60)

    df_sales = load_csv("sales.csv")
    df_titanic = load_csv("train.csv")

    # TEST 1: Simple Question
    reset_conversation()
    print("\n--- TEST 1: Simple Question ('What is the average sales?') ---")
    ans1 = run_agent("What is the average sales?", df_sales, "sales.csv")
    print("\nANSWER 1:")
    print(ans1)
    time.sleep(3)

    # TEST 2: Group Comparison
    reset_conversation()
    print("\n--- TEST 2: Group Comparison ('Which region had the highest total sales?') ---")
    ans2 = run_agent("Which region had the highest total sales?", df_sales, "sales.csv")
    print("\nANSWER 2:")
    print(ans2)
    time.sleep(3)

    # TEST 3: Multi-Step Investigation
    reset_conversation()
    print("\n--- TEST 3: Multi-Step Investigation ('Why is the highest-sales region performing better?') ---")
    ans3 = run_agent("Why is the highest-sales region performing better?", df_sales, "sales.csv")
    print("\nANSWER 3:")
    print(ans3)
    time.sleep(3)

    # TEST 4: Visualization Request
    reset_conversation()
    print("\n--- TEST 4: Visualization Request ('Compare total sales across regions and create a chart') ---")
    ans4 = run_agent("Compare total sales across regions and create a chart", df_sales, "sales.csv")
    print("\nANSWER 4:")
    print(ans4)
    time.sleep(3)

    # TEST 5: No Unnecessary Chart
    reset_conversation()
    print("\n--- TEST 5: No Unnecessary Chart ('What is the maximum sales value?') ---")
    ans5 = run_agent("What is the maximum sales value?", df_sales, "sales.csv")
    print("\nANSWER 5:")
    print(ans5)
    time.sleep(3)

    # TEST 6: Titanic Survival Rate
    reset_conversation()
    print("\n--- TEST 6: Titanic ('Which passenger class had the highest survival rate?') ---")
    ans6 = run_agent("Which passenger class had the highest survival rate?", df_titanic, "train.csv")
    print("\nANSWER 6:")
    print(ans6)
    time.sleep(3)

    # TEST 7 & 8: Conversational Follow-Up
    reset_conversation()
    print("\n--- TEST 7: Conversational Memory Q1 ('Which region had the highest sales?') ---")
    ans7_1 = run_agent("Which region had the highest sales?", df_sales, "sales.csv")
    print("\nANSWER 7.1:")
    print(ans7_1)
    time.sleep(3)

    print("\n--- TEST 8: Conversational Memory Q2 ('What was its average quantity?') ---")
    ans7_2 = run_agent("What was its average quantity?", df_sales, "sales.csv")
    print("\nANSWER 7.2:")
    print(ans7_2)

    print("\n" + "=" * 60)
    print("ALL PHASE 12 INTEGRATION TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    test_decision_parser_unit()
    run_phase12_integration_tests()
