# ===============================
# MODULE RANGE FILTER
# ===============================

def get_module_range(max_valid_module: int):
    """
    Ask user for start and end module.
    Validate boundaries.
    """

    print(f"\nAvailable Modules: 1 to {max_valid_module}")

    try:
        start_module = int(input("Enter Start Module: ").strip())
        end_module = int(input("Enter End Module: ").strip())
    except ValueError:
        raise ValueError("Module numbers must be integers.")

    if start_module < 1:
        raise ValueError("Start module must be >= 1.")

    if end_module > max_valid_module:
        raise ValueError(f"End module must be <= {max_valid_module}.")

    if start_module > end_module:
        raise ValueError("Start module cannot be greater than End module.")

    print(f"\n✅ Selected Module Range: {start_module} to {end_module}")

    return start_module, end_module


def filter_modules(modules: list, start_module: int, end_module: int):
    """
    Filter syllabus modules within selected range.
    """

    selected_modules = [
        m for m in modules
        if start_module <= m["module_id"] <= end_module
    ]

    if not selected_modules:
        raise ValueError("No modules found in selected range.")

    return selected_modules