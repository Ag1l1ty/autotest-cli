"""Utility functions for string and validation operations."""

import re


def format_name(first: str, last: str) -> str:
    """Format a full name from first and last name.

    Args:
        first: First name.
        last: Last name.

    Returns:
        Formatted full name in title case.
    """
    if not first or not last:
        raise ValueError("Both first and last name are required")
    return f"{first.strip().title()} {last.strip().title()}"


def validate_email(email: str) -> bool:
    """Check whether an email address is valid.

    Args:
        email: The email address to validate.

    Returns:
        True if the email matches a basic pattern, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))
