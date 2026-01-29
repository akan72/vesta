"""Fetch prices from Yahoo Finance."""

from dataclasses import dataclass

import requests
import yfinance as yf


class RateLimitError(Exception):
    """Raised when Yahoo Finance rate limits the request."""

    pass

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class PriceData:
    """Price information for a single symbol."""

    symbol: str
    price: float
    change_percent: float


def _create_session() -> requests.Session:
    """Create a requests session with custom user agent."""
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    return session


def fetch_prices(symbols: list[str]) -> list[PriceData]:
    """Fetch current prices and daily change for the given symbols.

    Uses yf.download() to fetch all tickers in a single batched API call.

    Args:
        symbols: List of Yahoo Finance symbols (e.g., ["BTC-USD", "GLD", "GOOG"])

    Returns:
        List of PriceData objects with current price and daily change percentage
    """
    session = _create_session()

    # Download last 2 days of data for all symbols in one call
    data = yf.download(
        tickers=symbols,
        period="2d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        session=session,
        progress=False,
    )

    results = []

    for symbol in symbols:
        # Handle single vs multiple ticker column structure
        if len(symbols) == 1:
            ticker_data = data
        else:
            ticker_data = data[symbol] if symbol in data.columns.get_level_values(0) else None

        if ticker_data is None or ticker_data.empty:
            # Symbol not found, add with zero values
            display_symbol = symbol.split("-")[0] if "-" in symbol else symbol
            results.append(PriceData(symbol=display_symbol, price=0.0, change_percent=0.0))
            continue

        # Get the latest close price
        closes = ticker_data["Close"].dropna()

        if len(closes) == 0:
            display_symbol = symbol.split("-")[0] if "-" in symbol else symbol
            results.append(PriceData(symbol=display_symbol, price=0.0, change_percent=0.0))
            continue

        price = float(closes.iloc[-1])

        # Calculate change percentage from previous close
        if len(closes) >= 2:
            prev_close = float(closes.iloc[-2])
            change_percent = ((price - prev_close) / prev_close) * 100 if prev_close != 0 else 0.0
        else:
            change_percent = 0.0

        # Use short symbol for display (strip -USD suffix for crypto)
        display_symbol = symbol.split("-")[0] if "-" in symbol else symbol

        results.append(
            PriceData(
                symbol=display_symbol,
                price=price,
                change_percent=change_percent,
            )
        )

    # Check if all prices are zero (indicates rate limiting)
    if all(p.price == 0.0 for p in results):
        raise RateLimitError("Rate limited by Yahoo Finance. Board not updated.")

    return results
