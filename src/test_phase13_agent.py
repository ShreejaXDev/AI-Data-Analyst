import sys
import os
import pandas as pd
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_loader import load_csv
from tools import inspect_dataset, execute_transformation, export_dataset
from agent import run_agent, reset_conversation
from planner import parse_decision_response, validate_decision


def test_decision_parser_phase13():
    print("Testing planner decision parser for Phase 13 decisions...")
    d1 = parse_decision_response('{"decision": "TRANSFORM", "reason": "Impute missing values", "next_action": "Fill Age NA"}')
    assert d1["decision"] == "TRANSFORM"
    assert d1["reason"] == "Impute missing values"

    d2 = parse_decision_response('{"decision": "EXPORT_DATA", "reason": "Export to CSV", "next_action": "Save to outputs"}')
    assert d2["decision"] == "EXPORT_DATA"
    print("SUCCESS: Phase 13 decision parser unit tests PASSED!")


def test_execute_transformation_missing_values():
    print("Testing missing value transformation (train.csv)...")
    df_titanic = load_csv("train.csv")
    missing_age_before = df_titanic["Age"].isnull().sum()
    assert missing_age_before == 177

    code = "df['Age'] = df['Age'].fillna(df['Age'].median())"
    res = execute_transformation(code, df_titanic, description="Impute missing Age with median")

    assert res["success"] is True
    active_df = res["active_df"]
    assert active_df["Age"].isnull().sum() == 0

    audit = res["audit"]
    assert audit["success"] is True
    assert "Age" in audit["columns_affected"]
    assert audit["missing_values_before"] > audit["missing_values_after"]
    print("SUCCESS: Missing value transformation test PASSED!")


def test_execute_transformation_duplicate_removal():
    print("Testing duplicate removal transformation...")
    df_sales = load_csv("sales.csv")
    df_dups = pd.concat([df_sales, df_sales.iloc[:2]], ignore_index=True)
    assert len(df_dups) == 12

    code = "df = df.drop_duplicates()"
    res = execute_transformation(code, df_dups, description="Remove duplicate rows")

    assert res["success"] is True
    active_df = res["active_df"]
    assert len(active_df) == 10
    assert active_df.duplicated().sum() == 0

    audit = res["audit"]
    assert audit["rows_before"] == 12
    assert audit["rows_after"] == 10
    assert audit["duplicates_before"] == 2
    assert audit["duplicates_after"] == 0
    print("SUCCESS: Duplicate removal test PASSED!")


def test_datatype_conversion():
    print("Testing datatype conversion transformation...")
    df_sales = load_csv("sales.csv")
    assert df_sales["Sales"].dtype == "int64"

    code = "df['Sales'] = df['Sales'].astype(float)"
    res = execute_transformation(code, df_sales, description="Convert Sales to float")

    assert res["success"] is True
    active_df = res["active_df"]
    assert active_df["Sales"].dtype == "float64"

    audit = res["audit"]
    assert "Sales" in audit["columns_affected"]
    print("SUCCESS: Datatype conversion test PASSED!")


def test_rejected_failed_transformation():
    print("Testing rejected/failed transformation error recovery & state preservation...")
    df_sales = load_csv("sales.csv")

    code = "df['NonExistentColumn'] = df['AnotherMissingColumn'] + 100"
    res = execute_transformation(code, df_sales, description="Invalid column operation")

    assert res["success"] is False
    assert "active_df" in res
    assert res["active_df"].equals(df_sales)
    assert "error" in res
    print("SUCCESS: Rejected/failed transformation test PASSED!")


def test_reprofiling_post_transformation():
    print("Testing re-profiling post-transformation...")
    df_titanic = load_csv("train.csv")
    profile_before = inspect_dataset(df_titanic)
    assert profile_before["missing_values"]["Age"] == 177

    code = "df['Age'] = df['Age'].fillna(df['Age'].median())"
    res = execute_transformation(code, df_titanic, description="Impute missing Age")
    active_df = res["active_df"]

    profile_after = inspect_dataset(active_df)
    assert profile_after["missing_values"]["Age"] == 0
    print("SUCCESS: Re-profiling post-transformation test PASSED!")


def test_side_effect_isolation():
    print("Testing side-effect isolation post-transformation...")
    df_titanic = load_csv("train.csv")
    code = "df['Age'] = df['Age'].fillna(df['Age'].median())"
    res = execute_transformation(code, df_titanic, description="Impute missing Age")
    active_df = res["active_df"]

    assert active_df["Age"].isnull().sum() == 0, "Age null count should be 0"
    assert active_df["Cabin"].isnull().sum() == 687, "Cabin null count should remain 687"
    assert active_df["Embarked"].isnull().sum() == 2, "Embarked null count should remain 2"
    assert len(active_df) == 891, "Row count should remain 891"
    assert len(active_df.columns) == 12, "Column count should remain 12"
    print("SUCCESS: Side-effect isolation test PASSED!")


def test_export_integrity():
    print("Testing export content integrity and source file protection...")
    df_titanic = load_csv("train.csv")
    code = "df['Age'] = df['Age'].fillna(df['Age'].median())"
    res = execute_transformation(code, df_titanic, description="Impute missing Age")
    active_df = res["active_df"]

    exp_res = export_dataset(active_df, dataset_name="train.csv")
    assert exp_res["success"] is True
    exported_path = exp_res["path"]

    # Re-read exported CSV
    df_exported = pd.read_csv(exported_path)
    assert df_exported["Age"].isnull().sum() == 0, "Exported file should have 0 missing Age values"

    # Verify source CSV is 100% untouched
    orig_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "train.csv")
    df_orig = pd.read_csv(orig_path)
    assert df_orig["Age"].isnull().sum() == 177, "Original train.csv must remain untouched with 177 missing Age values"
    print("SUCCESS: Export content integrity test PASSED!")


def run_phase13_agent_regression_tests():
    print("=" * 60)
    print("RUNNING PHASE 13 MANDATORY REGRESSION TESTS (A, B, C, D, E)")
    print("=" * 60)

    df_sales = load_csv("sales.csv")
    df_titanic = load_csv("train.csv")

    # TEST A: Informational Query Bug Fix
    reset_conversation()
    print("\n--- TEST A: Informational Query ('How many missing values are in Age?') ---")
    ans_a = run_agent("How many missing values are in Age?", df_titanic, "train.csv")
    print("\nANSWER A:")
    print(ans_a)
    assert "177" in ans_a, f"Expected '177' in answer, got: {ans_a}"
    time.sleep(3)

    # TEST B: Multi-Turn Active DataFrame Persistence
    reset_conversation()
    print("\n--- TEST B1: Turn 1 ('Fill missing Age values with the median') ---")
    ans_b1 = run_agent("Fill missing Age values with the median", df_titanic, "train.csv")
    print("\nANSWER B1:")
    print(ans_b1)
    time.sleep(3)

    print("\n--- TEST B2: Turn 2 ('How many missing values are in Age now?') ---")
    ans_b2 = run_agent("How many missing values are in Age now?", df_titanic, "train.csv")
    print("\nANSWER B2:")
    print(ans_b2)
    assert "0" in ans_b2, f"Expected '0' in Turn 2 answer, got: {ans_b2}"
    time.sleep(3)

    # TEST E: Direct Export Without Unnecessary TRANSFORM
    reset_conversation()
    print("\n--- TEST E: Direct Export ('Save the dataset to CSV') ---")
    ans_e = run_agent("Save the dataset to CSV", df_sales, "sales.csv")
    print("\nANSWER E:")
    print(ans_e)
    assert os.path.exists("outputs/cleaned_sales.csv")

    print("\n" + "=" * 60)
    print("ALL PHASE 13 REGRESSION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_decision_parser_phase13()
    test_execute_transformation_missing_values()
    test_execute_transformation_duplicate_removal()
    test_datatype_conversion()
    test_rejected_failed_transformation()
    test_reprofiling_post_transformation()
    test_side_effect_isolation()
    test_export_integrity()
    run_phase13_agent_regression_tests()
