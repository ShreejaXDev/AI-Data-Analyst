import pandas as pd

from data_inspector import (
    load_dataset,
    get_dataset_overview,
    get_column_info,
)

from llm import generate_python_code

from python_executor import execute_python


def main():

    # -----------------------------------------
    # 1. Get CSV path
    # -----------------------------------------

    file_path = input("Enter CSV file path: ")

    try:

        # -----------------------------------------
        # 2. Load dataset
        # -----------------------------------------

        df = load_dataset(file_path)

        print("\nDataset loaded successfully.")

        # -----------------------------------------
        # 3. Get dataset information
        # -----------------------------------------

        overview = get_dataset_overview(df)
        column_info = get_column_info(df)

        dataset_info = {
            "rows": overview["rows"],
            "columns": overview["columns"],
            "column_names": overview["column_names"],
            "data_types": column_info,
        }

        print("\n===== DATASET =====")
        print(dataset_info)

        # -----------------------------------------
        # 4. Get user question
        # -----------------------------------------

        user_question = input(
            "\nWhat would you like to know about the dataset?\n> "
        )

        # -----------------------------------------
        # 5. Ask LLM to generate Python
        # -----------------------------------------

        print("\nGenerating Python analysis...\n")

        python_code = generate_python_code(
            dataset_info,
            user_question
        )

        print("===== GENERATED PYTHON =====")
        print(python_code)

        # -----------------------------------------
        # 6. Execute generated Python
        # -----------------------------------------

        print("\nExecuting analysis...\n")

        result = execute_python(
            python_code,
            df
        )

        print("===== PYTHON RESULT =====")
        print(result)

    except FileNotFoundError:

        print("\nError: File not found.")
        print("Please check the CSV file path.")

    except pd.errors.EmptyDataError:

        print("\nError: The CSV file is empty.")

    except Exception as e:

        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()