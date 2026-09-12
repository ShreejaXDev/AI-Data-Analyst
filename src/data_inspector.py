import datetime
import pandas as pd
import numpy as np


# ============================================================
# BASIC DATASET FUNCTIONS
# ============================================================

def load_dataset(file_path):
    """
    Load a CSV file into a Pandas DataFrame.
    """
    return pd.read_csv(file_path)


def get_dataset_overview(df):
    """
    Return basic information about the dataset.
    """
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist()
    }


def get_column_info(df):
    """
    Return information about each column and its data type.
    """
    return {
        column: str(dtype)
        for column, dtype in df.dtypes.items()
    }


def get_missing_values(df):
    """
    Return the number of missing values in each column.
    """
    return {
        column: int(value)
        for column, value in df.isnull().sum().items()
    }


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


# ============================================================
# COLUMN TYPE DETECTION
# ============================================================

def detect_column_types(df):
    """
    Detect numeric, categorical, boolean and datetime columns.
    """

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    boolean_columns = df.select_dtypes(
        include="bool"
    ).columns.tolist()

    datetime_columns = df.select_dtypes(
        include=["datetime", "datetimetz"]
    ).columns.tolist()

    categorical_columns = [
        column
        for column in df.columns
        if column not in numeric_columns
        and column not in boolean_columns
        and column not in datetime_columns
    ]

    return {
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "boolean_columns": boolean_columns,
        "datetime_columns": datetime_columns
    }


# ============================================================
# POSSIBLE ID DETECTION
# ============================================================

def detect_possible_id_columns(df):
    """
    Detect columns that may represent identifiers.

    This is a heuristic, not a guarantee.
    """

    possible_ids = []

    measure_keywords = [
        "sales", "price", "amount", "cost", "revenue", "fare", "fee",
        "weight", "height", "age", "quantity", "score", "rate",
        "percentage", "val", "value", "count", "survived", "pclass",
        "sibsp", "parch"
    ]

    id_name_patterns = [
        "id", "identifier", "code", "key", "uuid", "guid"
    ]

    for column in df.columns:

        column_lower = str(column).lower()

        non_null_count = int(df[column].notna().sum())

        if non_null_count == 0:
            continue

        unique_count = int(df[column].nunique(dropna=True))

        uniqueness_ratio = unique_count / non_null_count

        # Exclude known financial/numerical measure names from ID detection
        if any(kw in column_lower for kw in measure_keywords):
            continue

        # Check explicit ID name patterns
        name_match = False

        for pattern in id_name_patterns:
            if pattern in column_lower:
                if pattern == "id":
                    if (
                        column_lower == "id"
                        or column_lower.endswith("_id")
                        or column_lower.endswith("id")
                        or "_id_" in column_lower
                        or "id_" in column_lower
                        or "id" in str(column)
                    ):
                        name_match = True
                else:
                    name_match = True

        if name_match and uniqueness_ratio >= 0.7:
            possible_ids.append(column)

        elif uniqueness_ratio >= 0.98:
            # High uniqueness column without explicit name match
            if pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_string_dtype(df[column]):
                sample_str = df[column].dropna().astype(str).head(20)
                has_spaces = sample_str.str.contains(r"\s").mean() > 0.2
                avg_len = sample_str.str.len().mean()
                if not has_spaces and avg_len <= 30:
                    possible_ids.append(column)

            elif pd.api.types.is_integer_dtype(df[column]):
                possible_ids.append(column)

    return possible_ids


# ============================================================
# POSSIBLE DATE DETECTION
# ============================================================

def detect_possible_date_columns(df):
    """
    Detect columns that may contain dates.

    Existing datetime columns are included.
    Object/string and numeric columns are tested heuristically.
    """

    possible_dates = []

    date_name_patterns = [
        "date", "time", "timestamp", "year", "month", "day", "dob", "created", "updated"
    ]

    for column in df.columns:

        if pd.api.types.is_datetime64_any_dtype(df[column]):
            possible_dates.append(column)
            continue

        column_lower = str(column).lower()

        name_match = any(
            pattern in column_lower
            for pattern in date_name_patterns
        )

        non_null_count = int(df[column].notna().sum())

        if non_null_count == 0:
            continue

        if name_match:
            if pd.api.types.is_numeric_dtype(df[column]):
                min_val = df[column].min()
                max_val = df[column].max()
                if "year" in column_lower and (1900 <= min_val <= 2100):
                    possible_dates.append(column)
                    continue
                elif "month" in column_lower and (1 <= min_val <= 12):
                    possible_dates.append(column)
                    continue

            try:
                converted = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

                valid_ratio = (
                    converted.notna().sum() / non_null_count
                )

                if valid_ratio >= 0.7:
                    possible_dates.append(column)

            except Exception:
                pass
        else:
            if pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_string_dtype(df[column]):
                sample_series = df[column].dropna().astype(str).head(10)
                if sample_series.str.contains(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}").mean() >= 0.7:
                    try:
                        converted = pd.to_datetime(
                            df[column],
                            errors="coerce"
                        )

                        valid_ratio = (
                            converted.notna().sum() / non_null_count
                        )

                        if valid_ratio >= 0.7:
                            possible_dates.append(column)

                    except Exception:
                        pass

    return possible_dates


# ============================================================
# COLUMN PROFILE
# ============================================================

def get_column_profile(df, column):
    """
    Generate detailed information about one column.
    """

    series = df[column]

    total_rows = len(df)

    missing_count = int(
        series.isna().sum()
    )

    non_null_count = int(
        series.notna().sum()
    )

    unique_count = int(
        series.nunique(dropna=True)
    )

    if non_null_count > 0:
        uniqueness_ratio = (
            unique_count / non_null_count
        )
    else:
        uniqueness_ratio = 0.0

    profile = {
        "dtype": str(series.dtype),
        "non_null_count": non_null_count,
        "missing_count": missing_count,
        "missing_percentage": round(
            (
                missing_count / total_rows * 100
                if total_rows > 0
                else 0
            ),
            2
        ),
        "unique_count": unique_count,
        "uniqueness_ratio": round(
            uniqueness_ratio,
            4
        ),
        "sample_values": [
            make_json_safe(value)
            for value in series.dropna()
            .head(5)
            .tolist()
        ]
    }

    # --------------------------------------------------------
    # NUMERIC INFORMATION
    # --------------------------------------------------------

    if pd.api.types.is_numeric_dtype(series):

        clean_series = series.dropna()

        if len(clean_series) > 0:

            profile["statistics"] = {
                "min": make_json_safe(
                    clean_series.min()
                ),
                "max": make_json_safe(
                    clean_series.max()
                ),
                "mean": make_json_safe(
                    clean_series.mean()
                ),
                "median": make_json_safe(
                    clean_series.median()
                ),
                "std": make_json_safe(
                    clean_series.std()
                ),
                "q25": make_json_safe(
                    clean_series.quantile(0.25)
                ),
                "q75": make_json_safe(
                    clean_series.quantile(0.75)
                )
            }

    # --------------------------------------------------------
    # CATEGORICAL INFORMATION
    # --------------------------------------------------------

    else:

        value_counts = (
            series
            .dropna()
            .value_counts()
            .head(5)
        )

        profile["top_values"] = {
            str(key): int(value)
            for key, value
            in value_counts.items()
        }

    return profile


# ============================================================
# CORRELATION
# ============================================================

def get_numeric_correlations(df):
    """
    Return correlations between numeric columns.
    """

    numeric_df = df.select_dtypes(
        include="number"
    )

    if numeric_df.shape[1] < 2:
        return {}

    correlation_matrix = numeric_df.corr()

    result = {}

    for column in correlation_matrix.columns:

        result[column] = {}

        for other_column in correlation_matrix.columns:

            value = correlation_matrix.loc[
                column,
                other_column
            ]

            if pd.notna(value):
                result[column][
                    other_column
                ] = round(float(value), 4)

    return result


# ============================================================
# ANALYSIS HINTS
# ============================================================

def generate_analysis_hints(
    df,
    column_profiles,
    possible_ids,
    possible_dates
):
    """
    Generate useful deterministic hints for the AI analyst.
    """

    hints = []

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        exclude="number"
    ).columns.tolist()

    if numeric_columns:
        hints.append(
            "Numeric columns are suitable for "
            "statistics, aggregations, comparisons "
            "and correlations."
        )

    if categorical_columns:
        hints.append(
            "Categorical columns are suitable for "
            "grouping, segmentation and comparisons."
        )

    if possible_ids:
        hints.append(
            "Possible identifier column(s) detected: "
            + ", ".join(possible_ids)
            + ". Avoid using them as normal "
              "numeric measures."
        )

    if possible_dates:
        hints.append(
            "Possible date/time column(s) detected: "
            + ", ".join(possible_dates)
            + ". These may support trend or "
              "time-based analysis."
        )

    high_missing_columns = []

    for column, profile in column_profiles.items():

        if profile["missing_percentage"] >= 15:

            high_missing_columns.append(
                f"{column} ({profile['missing_percentage']}%)"
            )

    if high_missing_columns:

        hints.append(
            "High missingness detected in: "
            + ", ".join(high_missing_columns)
            + "."
        )

    low_card_cat = []

    for column in categorical_columns:

        profile = column_profiles.get(column, {})

        u_count = profile.get("unique_count", 0)

        if 2 <= u_count <= 20:

            low_card_cat.append(
                f"{column} ({u_count} unique values)"
            )

    if low_card_cat:

        hints.append(
            "Key grouping candidates: "
            + ", ".join(low_card_cat)
            + "."
        )

    if len(df) == 0:

        hints.append(
            "The dataset contains no rows."
        )

    if get_duplicate_count(df) > 0:

        hints.append(
            "Duplicate rows are present and should "
            "be considered during analysis."
        )

    return hints


# ============================================================
# JSON SAFE VALUE
# ============================================================

def make_json_safe(value):
    """
    Convert NumPy/Pandas values into JSON-safe values.
    """

    if value is None:
        return None

    if pd.isna(value):
        return None

    if isinstance(
        value,
        (np.integer, int)
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating, float)
    ):
        if np.isnan(value) or np.isinf(value):
            return None

        return float(value)

    if isinstance(
        value,
        (np.bool_, bool)
    ):
        return bool(value)

    if isinstance(
        value,
        (pd.Timestamp, datetime.date, datetime.datetime)
    ):
        return str(value)

    if isinstance(value, dict):
        return {
            str(k): make_json_safe(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    try:
        val = value.item()
        if isinstance(val, (int, float, bool, str)):
            return val
    except (AttributeError, ValueError):
        pass

    return str(value) if not isinstance(value, (int, float, bool, str)) else value


# ============================================================
# SMART DATASET PROFILE
# ============================================================

def get_smart_profile(df):
    """
    Generate a comprehensive deterministic profile
    of the dataset.

    This function does not use an LLM.
    """

    overview = get_dataset_overview(df)

    column_types = detect_column_types(df)

    missing_values = get_missing_values(df)

    total_missing = int(
        df.isnull().sum().sum()
    )

    total_cells = (
        df.shape[0] * df.shape[1]
    )

    overall_missing_percentage = (
        total_missing / total_cells * 100
        if total_cells > 0
        else 0
    )

    possible_ids = (
        detect_possible_id_columns(df)
    )

    possible_dates = (
        detect_possible_date_columns(df)
    )

    column_profiles = {}

    for column in df.columns:

        column_profiles[column] = (
            get_column_profile(
                df,
                column
            )
        )

    correlations = (
        get_numeric_correlations(df)
    )

    analysis_hints = generate_analysis_hints(
        df,
        column_profiles,
        possible_ids,
        possible_dates
    )

    return {
        "rows": overview["rows"],
        "columns": overview["columns"],
        "column_names": overview["column_names"],

        "data_types": get_column_info(df),

        "missing_values": missing_values,

        "total_missing_values": total_missing,

        "overall_missing_percentage": round(
            overall_missing_percentage,
            2
        ),

        "duplicate_rows": get_duplicate_count(df),

        "numeric_columns": column_types[
            "numeric_columns"
        ],

        "categorical_columns": column_types[
            "categorical_columns"
        ],

        "boolean_columns": column_types[
            "boolean_columns"
        ],

        "datetime_columns": column_types[
            "datetime_columns"
        ],

        "possible_id_columns": possible_ids,

        "possible_date_columns": possible_dates,

        "column_profiles": column_profiles,

        "numeric_correlations": correlations,

        "analysis_hints": analysis_hints
    }


# ============================================================
# LEGACY CONSOLE INSPECTION
# ============================================================

def inspect_dataset(file_path):
    """
    Run all inspection operations and print them.

    Kept for compatibility with the earlier project code.
    """

    df = load_dataset(file_path)

    print("\n===== DATASET OVERVIEW =====")

    overview = get_dataset_overview(df)

    print(
        f"Rows: {overview['rows']}"
    )

    print(
        f"Columns: {overview['columns']}"
    )

    print(
        f"Column names: "
        f"{overview['column_names']}"
    )

    print("\n===== COLUMN INFORMATION =====")

    print(
        get_column_info(df)
    )

    print("\n===== MISSING VALUES =====")

    print(
        get_missing_values(df)
    )

    print("\n===== DUPLICATES =====")

    print(
        f"Duplicate rows: "
        f"{get_duplicate_count(df)}"
    )

    print("\n===== SAMPLE DATA =====")

    print(
        get_sample_data(df)
    )

    print("\n===== STATISTICS =====")

    print(
        get_statistics(df)
    )

    return df