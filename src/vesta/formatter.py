"""Format prices for Vestaboard display."""

from vesta.prices import PriceData

# Vestaboard character codes
CHAR_CODES = {
    " ": 0,
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 10, "K": 11, "L": 12, "M": 13, "N": 14, "O": 15, "P": 16, "Q": 17,
    "R": 18, "S": 19, "T": 20, "U": 21, "V": 22, "W": 23, "X": 24, "Y": 25, "Z": 26,
    "1": 27, "2": 28, "3": 29, "4": 30, "5": 31, "6": 32, "7": 33, "8": 34, "9": 35, "0": 36,
    "!": 37, "@": 38, "#": 39, "$": 40, "(": 41, ")": 42, "-": 44, "+": 46,
    "&": 47, "=": 48, ";": 49, ":": 50, "'": 52, '"': 53, "%": 54, ",": 55,
    ".": 56, "/": 59, "?": 60, "°": 62,
}

# Board dimensions
ROWS = 6
COLS = 22

# Vestaboard color chips; each occupies one physical cell.
RED = 63
GREEN = 66
BLACK = 70
COLOR_CHARS = {RED: "🟥", GREEN: "🟩", BLACK: "⬛"}


def text_to_codes(text: str) -> list[int]:
    """Convert a text string to Vestaboard character codes."""
    codes = []
    for char in text.upper():
        code = CHAR_CODES.get(char, 0)  # Default to blank for unknown chars
        codes.append(code)
    return codes


def format_price(price: float) -> str:
    """Format a price value for display."""
    if price >= 10000:
        # Large numbers: $97,500
        return f"${price:,.0f}"
    elif price >= 1000:
        # Medium numbers: $1,234
        return f"${price:,.0f}"
    elif price >= 100:
        # Hundreds: $245
        return f"${price:.0f}"
    elif price >= 10:
        # Tens: $45.50
        return f"${price:.2f}"
    else:
        # Small numbers: $0.45
        return f"${price:.2f}"


def format_change(change_percent: float) -> str:
    """Format a change percentage for display."""
    change_percent = round(change_percent, 1)
    if change_percent == 0:
        change_percent = 0.0  # Avoid displaying negative zero.
    sign = "+" if change_percent >= 0 else ""
    return f"{sign}{change_percent:.1f}%"


def change_color(change_percent: float) -> int:
    """Match the color to the displayed percentage, including rounded zero."""
    displayed_change = round(change_percent, 1)
    if displayed_change > 0:
        return GREEN
    if displayed_change < 0:
        return RED
    return BLACK


def format_row(price_data: PriceData) -> str:
    """Format a single price row for the Vestaboard.

    Format: SYMBOL    PRICE  CHANGE [color cell]
    The last of the 22 cells is reserved for the color chip.
    """
    symbol = price_data.symbol[:6].ljust(6)  # 6 chars, left-aligned
    price_str = format_price(price_data.price)
    change_str = format_change(price_data.change_percent)

    middle_section = f"{price_str:>8}"  # 8 chars for price, right-aligned
    right_section = f"{change_str:>6}"  # 6 chars for change, right-aligned

    row = f"{symbol} {middle_section}{right_section} "

    # Ensure exactly 22 characters
    if len(row) > COLS:
        raise ValueError("Price and percentage do not fit alongside the color chip.")
    elif len(row) < COLS:
        row = row.ljust(COLS)

    return row


def format_for_board(prices: list[PriceData]) -> list[list[int]]:
    """Convert a list of prices to a 6x22 Vestaboard character code array.

    Args:
        prices: List of PriceData objects (max 6)

    Returns:
        6x22 array of integer character codes
    """
    board = []

    for i in range(ROWS):
        if i < len(prices):
            row_text = format_row(prices[i])
            row_codes = text_to_codes(row_text)
            row_codes[-1] = change_color(prices[i].change_percent)
        else:
            # Empty row
            row_codes = [0] * COLS

        # Ensure exactly 22 columns
        row_codes = row_codes[:COLS]
        while len(row_codes) < COLS:
            row_codes.append(0)

        board.append(row_codes)

    return board


def board_to_text(board: list[list[int]]) -> str:
    """Convert a board array back to text for display/debugging.

    Args:
        board: 6x22 array of character codes

    Returns:
        Human-readable string representation
    """
    # Reverse mapping
    code_to_char = {v: k for k, v in CHAR_CODES.items()}
    code_to_char[0] = " "  # Ensure space is correct
    code_to_char.update({code: f" {char}" for code, char in COLOR_CHARS.items()})

    lines = []
    for row in board:
        line = "".join(code_to_char.get(code, "?") for code in row)
        lines.append(line)

    return "\n".join(lines)
