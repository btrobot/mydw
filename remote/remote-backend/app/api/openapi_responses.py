from __future__ import annotations

from typing import Any

from app.schemas.auth import ErrorResponse


_DEFAULT_ERROR_DESCRIPTIONS = {
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    429: 'Too Many Requests',
}


def error_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    return {
        status_code: {
            'model': ErrorResponse,
            'description': _DEFAULT_ERROR_DESCRIPTIONS[status_code],
        }
        for status_code in status_codes
    }
