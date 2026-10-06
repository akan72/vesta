"""Validate and send the Vestaboard character grid."""

from vestaboard import Board

from vesta.formatter import CHAR_CODES, COLS, ROWS

VALID_CODES = set(CHAR_CODES.values()) | set(range(63, 72))


def validate_board(rows: list[list[int]]) -> None:
    """Reject malformed grids before previewing or making a request."""
    if not isinstance(rows, list) or len(rows) != ROWS:
        raise ValueError("Board must contain exactly 6 rows.")
    for row in rows:
        if not isinstance(row, list) or len(row) != COLS:
            raise ValueError("Each board row must contain exactly 22 character codes.")
        if any(type(code) is not int or code not in VALID_CODES for code in row):
            raise ValueError("Board contains an unsupported character code.")
    if not any(code for row in rows for code in row):
        raise ValueError("Vestaboard does not accept an entirely blank message.")


def send_to_board(rows: list[list[int]], api_key: str) -> None:
    """Send the validated grid through the Vestaboard SDK's Read/Write API."""
    validate_board(rows)
    Board(apiKey=api_key, readWrite=True).raw(rows)
