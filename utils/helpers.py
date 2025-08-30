def format_currency(value):
    return f"${value:,.2f}"


def get_app_dir():
    """Get the directory of the running application."""
    import sys
    import os

    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))