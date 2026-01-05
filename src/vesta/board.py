"""Vestaboard API wrapper."""

from vestaboard import Board


def send_to_board(rows: list[list[int]], api_key: str) -> None:
    """Send a character code array to the Vestaboard.

    Args:
        rows: 6x22 array of integer character codes
        api_key: Vestaboard Read/Write API key
    """
    board = Board(apiKey=api_key, readWrite=True)
    board.raw(rows)
