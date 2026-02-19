"""
Centralized response helpers for API endpoints.
Reduces boilerplate in route handlers.
"""

from flask import jsonify


def service_response(result: dict, success_code: int = 200, error_code: int = 400):
    """
    Convert service result dict to Flask response.

    Usage:
        result = some_service()
        return service_response(result)  # Returns 200 or 400 based on result

        # Or specify custom codes:
        return service_response(result, 201, 422)
    """
    if "error" in result:
        return jsonify(result), error_code
    return jsonify(result), success_code


def paginated_response(items: list, total: int, page: int, per_page: int, key: str = "items"):
    """
    Create standardized paginated response.

    Usage:
        return paginated_response(
            items=[...],
            total=100,
            page=1,
            per_page=25,
            key="contracts"  # Optional, defaults to "items"
        )

    Returns:
        {
            "contracts": [...],
            "total": 100,
            "page": 1,
            "pages": 4
        }
    """
    return {
        key: items,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }
