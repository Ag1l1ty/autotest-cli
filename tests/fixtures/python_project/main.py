"""Main module with core business logic."""


def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


def divide(a: float, b: float) -> float:
    """Return the division of a by b.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def greet(name: str, formal: bool = False) -> str:
    """Return a greeting message.

    Args:
        name: The name of the person to greet.
        formal: Whether to use a formal greeting.

    Returns:
        A greeting string.
    """
    if not name or not name.strip():
        raise ValueError("Name cannot be empty")
    name = name.strip()
    if formal:
        return f"Good day, {name}. How do you do?"
    return f"Hey, {name}!"
