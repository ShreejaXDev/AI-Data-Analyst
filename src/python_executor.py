import matplotlib.pyplot as plt

def execute_python(code, df):

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    local_variables = {
        "df": df,
        "pd": pd,
        "np": np,
        "plt": plt
    }

    try:

        exec(
            code,
            {},
            local_variables
        )

        if "result" not in local_variables:

            return {
                "success": False,
                "error": (
                    "The generated code did not "
                    "create a variable named 'result'."
                )
            }

        return {
            "success": True,
            "result": local_variables["result"]
        }

    except Exception as e:

        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }