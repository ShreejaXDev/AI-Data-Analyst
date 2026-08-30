def execute_python(code, df):
    """
    Execute LLM-generated Python code using the provided DataFrame.
    """

    local_variables = {
        "df": df
    }

    exec(code, {}, local_variables)

    if "result" not in local_variables:
        raise ValueError(
            "Generated code did not create a variable named 'result'."
        )

    return local_variables["result"]