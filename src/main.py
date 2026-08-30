import pandas as pd

from data_inspector import inspect_dataset


def main():
    file_path = input("Enter CSV file path: ")

    try:
        inspect_dataset(file_path)

    except FileNotFoundError:
        print("\nError: File not found.")
        print("Please check the CSV file path.")

    except pd.errors.EmptyDataError:
        print("\nError: The CSV file is empty.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    main()