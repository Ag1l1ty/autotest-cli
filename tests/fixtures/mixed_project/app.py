"""Application module with a data-processing pipeline."""

from typing import Any


def process_data(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Clean and transform a list of records.

    Steps:
        1. Strip whitespace from all string values.
        2. Drop records that have no 'id' key.
        3. Add a 'processed' flag set to True.

    Args:
        raw: A list of dictionaries representing raw records.

    Returns:
        A new list of cleaned records.
    """
    results = []
    for record in raw:
        if "id" not in record:
            continue
        cleaned = {}
        for key, value in record.items():
            cleaned[key] = value.strip() if isinstance(value, str) else value
        cleaned["processed"] = True
        results.append(cleaned)
    return results
