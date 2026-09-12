import os
import pandas as pd


# ============================================================
# DATA DIRECTORY
# ============================================================

DATA_DIRECTORY = "data"


# ============================================================
# FIND CSV FILES
# ============================================================

def list_csv_files():
    """
    Return all CSV files available inside the data directory.
    """

    if not os.path.exists(DATA_DIRECTORY):
        os.makedirs(DATA_DIRECTORY)

    csv_files = [
        file
        for file in os.listdir(DATA_DIRECTORY)
        if file.lower().endswith(".csv")
    ]

    csv_files.sort()

    return csv_files


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(filename):
    """
    Load a selected CSV file into a Pandas DataFrame.
    """

    file_path = os.path.join(
        DATA_DIRECTORY,
        filename
    )

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    if not filename.lower().endswith(".csv"):

        raise ValueError(
            "Only CSV files are supported."
        )

    df = pd.read_csv(file_path)

    return df


# ============================================================
# DISPLAY DATASETS
# ============================================================

def display_available_datasets():
    """
    Display all available CSV datasets.
    """

    csv_files = list_csv_files()

    if not csv_files:

        print(
            "\nNo CSV files found in the data directory."
        )

        return []

    print(
        "\nAvailable datasets:"
    )

    print(
        "-" * 40
    )

    for index, filename in enumerate(
        csv_files,
        start=1
    ):

        print(
            f"{index}. {filename}"
        )

    print(
        "-" * 40
    )

    return csv_files


# ============================================================
# INTERACTIVE DATASET SELECTION
# ============================================================

def choose_dataset():
    """
    Ask the user to select a CSV dataset.
    """

    csv_files = display_available_datasets()

    if not csv_files:

        return None

    while True:

        choice = input(
            "\nChoose dataset number: "
        ).strip()

        try:

            choice_number = int(choice)

        except ValueError:

            print(
                "Please enter a valid number."
            )

            continue

        if (
            choice_number < 1
            or choice_number > len(csv_files)
        ):

            print(
                "Invalid choice. "
                "Please select one of the listed numbers."
            )

            continue

        selected_file = csv_files[
            choice_number - 1
        ]

        print(
            f"\nSelected dataset: {selected_file}"
        )

        return selected_file