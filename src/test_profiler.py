import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data_loader import load_csv
from data_inspector import get_smart_profile
from tools import inspect_dataset


def test_sales_profiler():
    print("Testing sales.csv profiler...")
    df = load_csv("sales.csv")
    profile = inspect_dataset(df)

    assert profile["rows"] == 10, f"Expected 10 rows, got {profile['rows']}"
    assert profile["columns"] == 4, f"Expected 4 columns, got {profile['columns']}"
    assert set(profile["numeric_columns"]) == {"Sales", "Quantity"}, f"Unexpected numeric columns: {profile['numeric_columns']}"
    assert set(profile["categorical_columns"]) == {"Product", "Region"}, f"Unexpected categorical columns: {profile['categorical_columns']}"

    sales_stats = profile["column_profiles"]["Sales"]["statistics"]
    assert sales_stats["min"] == 25000, f"Sales min failed: {sales_stats['min']}"
    assert sales_stats["max"] == 90000, f"Sales max failed: {sales_stats['max']}"
    assert sales_stats["mean"] == 54000.0, f"Sales mean failed: {sales_stats['mean']}"

    qty_stats = profile["column_profiles"]["Quantity"]["statistics"]
    assert qty_stats["min"] == 4, f"Quantity min failed: {qty_stats['min']}"
    assert qty_stats["max"] == 12, f"Quantity max failed: {qty_stats['max']}"
    assert round(qty_stats["mean"], 1) == 7.1, f"Quantity mean failed: {qty_stats['mean']}"

    assert profile["total_missing_values"] == 0, f"Expected 0 missing, got {profile['total_missing_values']}"
    assert profile["duplicate_rows"] == 0, f"Expected 0 duplicates, got {profile['duplicate_rows']}"

    product_u = profile["column_profiles"]["Product"]["unique_count"]
    assert product_u == 3, f"Expected 3 unique products, got {product_u}"

    region_u = profile["column_profiles"]["Region"]["unique_count"]
    assert region_u == 4, f"Expected 4 unique regions, got {region_u}"

    assert "Sales" not in profile["possible_id_columns"], "Sales should NOT be classified as an ID"

    print("SUCCESS: sales.csv profiler test PASSED!")


def test_titanic_profiler():
    print("Testing train.csv (Titanic) profiler...")
    df = load_csv("train.csv")
    profile = inspect_dataset(df)

    assert profile["rows"] == 891, f"Expected 891 rows, got {profile['rows']}"
    assert profile["columns"] == 12, f"Expected 12 columns, got {profile['columns']}"

    missing = profile["missing_values"]
    assert missing["Age"] == 177, f"Expected 177 missing Age, got {missing['Age']}"
    assert missing["Cabin"] == 687, f"Expected 687 missing Cabin, got {missing['Cabin']}"
    assert missing["Embarked"] == 2, f"Expected 2 missing Embarked, got {missing['Embarked']}"

    possible_ids = profile["possible_id_columns"]
    assert "PassengerId" in possible_ids, f"PassengerId should be in possible_id_columns: {possible_ids}"
    assert "Name" not in possible_ids, f"Name should NOT be in possible_id_columns: {possible_ids}"
    assert "Ticket" not in possible_ids, f"Ticket should NOT be in possible_id_columns: {possible_ids}"

    print("SUCCESS: train.csv profiler test PASSED!")


if __name__ == "__main__":
    test_sales_profiler()
    test_titanic_profiler()
    print("\nALL PROFILER UNIT TESTS PASSED SUCCESSFULLY!")
