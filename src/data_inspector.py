import pandas as pd


def load_dataset(file_path):
    """
    Load a CSV file into a Pandas DataFrame.
    """
    df = pd.read_csv(file_path)
    return df


def get_dataset_overview(df):
    """
    Return basic information about the dataset.
    """
    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_names": df.columns.tolist()
    }


def get_column_info(df):
    """
    Return information about each column and its data type.
    """
    return df.dtypes.astype(str).to_dict()


def get_missing_values(df):
    """
    Return the number of missing values in each column.
    """
    return df.isnull().sum().to_dict()


def get_duplicate_count(df):
    """
    Return the number of duplicate rows.
    """
    return int(df.duplicated().sum())


def get_sample_data(df, n=5):
    """
    Return the first n rows of the dataset.
    """
    return df.head(n)


def get_statistics(df):
    """
    Return descriptive statistics for the dataset.
    """
    return df.describe(include="all")


def inspect_dataset(file_path):
    """
    Run all basic inspection operations.
    """

    df = load_dataset(file_path)

    print("\n===== DATASET OVERVIEW =====")
    overview = get_dataset_overview(df)

    print(f"Rows: {overview['rows']}")
    print(f"Columns: {overview['columns']}")
    print(f"Column names: {overview['column_names']}")

    print("\n===== COLUMN INFORMATION =====")
    print(get_column_info(df))

    print("\n===== MISSING VALUES =====")
    print(get_missing_values(df))

    print("\n===== DUPLICATES =====")
    print(f"Duplicate rows: {get_duplicate_count(df)}")

    print("\n===== SAMPLE DATA =====")
    print(get_sample_data(df))

    print("\n===== STATISTICS =====")
    print(get_statistics(df))

    return df