import pandas as pd


def inspect_dataset(file_path):
    df = pd.read_csv(file_path)

    print("\n===== DATASET OVERVIEW =====")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\n===== COLUMNS =====")
    print(df.columns.tolist())

    print("\n===== DATA TYPES =====")
    print(df.dtypes)

    print("\n===== MISSING VALUES =====")
    print(df.isnull().sum())

    print("\n===== DUPLICATES =====")
    print(f"Duplicate rows: {df.duplicated().sum()}")

    print("\n===== SAMPLE DATA =====")
    print(df.head())

    print("\n===== STATISTICS =====")
    print(df.describe(include="all"))


if __name__ == "__main__":
    file_path = input("Enter CSV file path: ")

    inspect_dataset(file_path)