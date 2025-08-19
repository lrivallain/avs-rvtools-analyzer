"""
Utility functions and Jinja2 helpers for the RVTools Analyzer application.
"""

def convert_mib_to_human_readable(value):
    """
    Convert MiB to human-readable format (MB, GB, TB).
    :param value: Value in MiB
    :return: Human-readable string
    """
    try:
        value = float(value)
        # 1 MiB = 1.048576 MB
        value_in_mb = value * 1.048576

        if value_in_mb >= 1024 * 1024:
            return f"{value_in_mb / (1024 * 1024):.2f} TB"
        elif value_in_mb >= 1024:
            return f"{value_in_mb / 1024:.2f} GB"
        else:
            return f"{value_in_mb:.2f} MB"
    except (ValueError, TypeError):
        return "Invalid input"


def get_risk_badge_class(risk_level):
    """Map risk levels to Bootstrap badge classes."""
    risk_mapping = {
        'info': 'text-bg-info',
        'warning': 'text-bg-warning',
        'danger': 'text-bg-danger',
        'blocking': 'text-bg-danger'
    }
    return risk_mapping.get(risk_level, 'text-bg-secondary')


def get_risk_display_name(risk_level):
    """Map risk levels to display names."""
    risk_mapping = {
        'info': 'Info',
        'warning': 'Warning',
        'danger': 'Blocking',
        'blocking': 'Blocking'
    }
    return risk_mapping.get(risk_level, 'Unknown')


def allowed_file(filename, allowed_extensions=None):
    """Check if uploaded file has an allowed extension."""
    if allowed_extensions is None:
        allowed_extensions = {'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def register_jinja_helpers(app):
    """Register all Jinja2 filters and global functions with the Flask app."""
    # Register filters
    app.jinja_env.filters['convert_mib_to_human_readable'] = convert_mib_to_human_readable

    # Register global functions
    app.jinja_env.globals['get_risk_badge_class'] = get_risk_badge_class
    app.jinja_env.globals['get_risk_display_name'] = get_risk_display_name
