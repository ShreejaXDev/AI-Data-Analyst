from python_executor import execute_python


# ============================================================
# TOOL 1 — INSPECT DATASET
# ============================================================

def inspect_dataset(df):

    return {
        "rows": len(df),

        "columns": len(df.columns),

        "column_names": df.columns.tolist(),

        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        },

        "missing_values": {
            column: int(df[column].isna().sum())
            for column in df.columns
        }
    }


# ============================================================
# TOOL 2 — BASIC STATISTICS
# ============================================================

def get_basic_statistics(df):

    numeric_df = df.select_dtypes(
        include="number"
    )

    statistics = {}

    for column in numeric_df.columns:

        statistics[column] = {

            "count": int(
                numeric_df[column].count()
            ),

            "mean": float(
                numeric_df[column].mean()
            ),

            "median": float(
                numeric_df[column].median()
            ),

            "min": float(
                numeric_df[column].min()
            ),

            "max": float(
                numeric_df[column].max()
            )
        }

    return statistics


# ============================================================
# TOOL 3 — EXECUTE ANALYSIS
# ============================================================

def execute_analysis(code, df):

    result = execute_python(
        code,
        df
    )

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------

    if not result["success"]:

        return {
            "success": False,
            "error": result["error"]
        }

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    value = result["result"]

    return serialize_result(
        value
    )


# ============================================================
# SERIALIZE PYTHON RESULT
# ============================================================

def serialize_result(value):

    import pandas as pd
    import numpy as np

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    if isinstance(
        value,
        pd.DataFrame
    ):

        return {
            "success": True,

            "type": "dataframe",

            "columns": value.columns.tolist(),

            "rows": value.replace(
                {np.nan: None}
            ).to_dict(
                orient="records"
            )
        }

    # --------------------------------------------------------
    # SERIES
    # --------------------------------------------------------

    if isinstance(
        value,
        pd.Series
    ):

        return {
            "success": True,

            "type": "series",

            "data": value.replace(
                {np.nan: None}
            ).to_dict()
        }

    # --------------------------------------------------------
    # NUMPY NUMBER
    # --------------------------------------------------------

    if isinstance(
        value,
        np.generic
    ):

        return {
            "success": True,

            "type": "value",

            "value": value.item()
        }

    # --------------------------------------------------------
    # NORMAL PYTHON VALUE
    # --------------------------------------------------------

    return {
        "success": True,

        "type": "value",

        "value": value
    }