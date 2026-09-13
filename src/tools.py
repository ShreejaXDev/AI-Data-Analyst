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
    import numpy as np

    if value is None:
        return None

    if isinstance(value, pd.DataFrame):
        return {
            "type": "dataframe",
            "columns": [str(c) for c in value.columns.tolist()],
            "data": make_json_safe(value.to_dict(orient="records"))
        }

    if isinstance(value, pd.Series):
        return {
            "type": "series",
            "name": make_json_safe(value.name),
            "data": make_json_safe(value.to_dict())
        }

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple, set, np.ndarray)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, (np.integer, int)):
        return int(value)

    if isinstance(value, (np.floating, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)

    if isinstance(value, (np.bool_, bool)):
        return bool(value)

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    try:
        val = value.item()
        if isinstance(val, (int, float, bool, str)):
            return val
    except (AttributeError, ValueError):
        pass

    return str(value) if not isinstance(value, (int, float, bool, str)) else value




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


# ============================================================
# DATA TRANSFORMATION TOOL (PHASE 13)
# ============================================================

def execute_transformation(code, df, description=""):
    """
    Execute AI-generated Pandas transformation code on a working copy of active_df.
    Validates the result and produces a structured audit record.
    """
    import numpy as np

    # 1. Create explicit working copy
    working_df = df.copy()

    # 2. Record pre-transformation metrics
    rows_before = len(df)
    cols_before = df.columns.tolist()
    missing_before = int(df.isnull().sum().sum())
    dtypes_before = {c: str(d) for c, d in df.dtypes.items()}
    duplicates_before = int(df.duplicated().sum())

    try:
        local_variables = {
            "df": working_df,
            "pd": pd,
            "np": np
        }

        # 3. Execute code
        exec(code, {}, local_variables)

        # 4. Extract updated dataframe
        new_df = None
        if "df" in local_variables and isinstance(local_variables["df"], pd.DataFrame):
            new_df = local_variables["df"]
        elif "result" in local_variables and isinstance(local_variables["result"], pd.DataFrame):
            new_df = local_variables["result"]
        else:
            return {
                "success": False,
                "error": "Transformation code did not return or update a valid Pandas DataFrame in 'df' or 'result'.",
                "active_df": df,
                "audit": {
                    "description": description,
                    "transformation_code": code,
                    "success": False,
                    "error": "No valid DataFrame produced."
                }
            }

        # 5. Validation Check
        if not isinstance(new_df, pd.DataFrame):
            return {
                "success": False,
                "error": "Transformation output is not a Pandas DataFrame.",
                "active_df": df,
                "audit": {
                    "description": description,
                    "transformation_code": code,
                    "success": False,
                    "error": "Non-DataFrame output."
                }
            }

        rows_after = len(new_df)
        cols_after = new_df.columns.tolist()
        missing_after = int(new_df.isnull().sum().sum())
        dtypes_after = {c: str(d) for c, d in new_df.dtypes.items()}
        duplicates_after = int(new_df.duplicated().sum())

        # Determine affected columns
        affected = []
        for col in set(cols_before + cols_after):
            if col not in cols_before or col not in cols_after:
                affected.append(col)
            elif dtypes_before.get(col) != dtypes_after.get(col):
                affected.append(col)
            elif col in df.columns and col in new_df.columns:
                try:
                    if not df[col].equals(new_df[col]):
                        affected.append(col)
                except Exception:
                    affected.append(col)

        audit_record = {
            "description": description or "Dataset transformation",
            "transformation_code": code,
            "columns_affected": affected,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "missing_values_before": missing_before,
            "missing_values_after": missing_after,
            "columns_before": cols_before,
            "columns_after": cols_after,
            "duplicates_before": duplicates_before,
            "duplicates_after": duplicates_after,
            "success": True
        }

        return {
            "success": True,
            "active_df": new_df,
            "audit": audit_record
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "active_df": df,
            "audit": {
                "description": description,
                "transformation_code": code,
                "success": False,
                "error": str(e)
            }
        }


# ============================================================
# EXPORT DATASET TOOL (PHASE 13)
# ============================================================

def export_dataset(df, dataset_name="dataset.csv", output_path=None):
    """
    Save the active transformed DataFrame to a safe CSV path (default: outputs/cleaned_<name>.csv).
    """
    try:
        clean_name = os.path.basename(dataset_name)
        if not clean_name.lower().endswith(".csv"):
            clean_name += ".csv"

        if not output_path:
            output_path = os.path.join("outputs", f"cleaned_{clean_name}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        df.to_csv(output_path, index=False)

        if not os.path.exists(output_path):
            return {
                "success": False,
                "error": "Failed to create exported CSV file."
            }

        return {
            "success": True,
            "path": output_path,
            "rows": len(df),
            "columns": len(df.columns)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }