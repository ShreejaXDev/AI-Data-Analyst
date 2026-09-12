import os
import json
import pandas as pd
from data_inspector import get_smart_profile


# ============================================================
# DATASET INSPECTION TOOL
# ============================================================

def inspect_dataset(df):
    """
    Inspect the dataset and return rich smart profile information
    for the AI agent.
    """

    return get_smart_profile(df)


# ============================================================
# JSON SAFE CONVERSION
# ============================================================

def make_json_safe(value):
    """
    Convert pandas/numpy objects into JSON-safe Python objects.
    """

    if isinstance(value, pd.DataFrame):
        return {
            "type": "dataframe",
            "columns": value.columns.tolist(),
            "data": value.to_dict(orient="records")
        }

    if isinstance(value, pd.Series):
        return {
            "type": "series",
            "name": value.name,
            "data": value.to_dict()
        }

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    try:
        return value.item()
    except AttributeError:
        return value


# ============================================================
# PYTHON ANALYSIS TOOL
# ============================================================

def execute_analysis(code, df):

    """
    Execute AI-generated Python/Pandas analysis code.
    """

    try:

        local_variables = {
            "df": df,
            "pd": pd
        }

        exec(code, {}, local_variables)

        if "result" not in local_variables:

            return {
                "success": False,
                "error": (
                    "The generated code did not create "
                    "a variable named 'result'."
                )
            }

        result = local_variables["result"]

        return {
            "success": True,
            "result": make_json_safe(result)
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# VISUALIZATION TOOL
# ============================================================

def generate_visualization(
    code,
    df,
    output_path="outputs/chart.png"
):

    """
    Execute AI-generated Matplotlib visualization code.
    """

    try:

        import matplotlib

        matplotlib.use("Agg")

        import matplotlib.pyplot as plt

        local_variables = {
            "df": df,
            "pd": pd,
            "plt": plt
        }

        # Execute AI-generated visualization code
        exec(code, {}, local_variables)

        # Check whether a figure was created
        figure_numbers = plt.get_fignums()

        if not figure_numbers:

            return {
                "success": False,
                "error": (
                    "The visualization code did not "
                    "create a Matplotlib figure."
                )
            }

        # Create output directory
        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True
        )

        # Get current figure
        figure = plt.gcf()

        # Save figure
        figure.savefig(
            output_path,
            bbox_inches="tight",
            dpi=150
        )

        # Verify file
        if not os.path.exists(output_path):

            return {
                "success": False,
                "error": "Chart file was not created."
            }

        return {
            "success": True,
            "type": "visualization",
            "path": output_path
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

    finally:

        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass