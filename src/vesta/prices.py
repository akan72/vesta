"""Fetch prices from Yahoo Finance."""

import time
from dataclasses import dataclass

import requests
import yfinance as yf

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

    Args:
        symbols: List of Yahoo Finance symbols (e.g., ["BTC-USD", "GLD", "GOOG"])

    Returns:
        List of PriceData objects with current price and daily change percentage
    """
    results = []
    session = _create_session()

    for i, symbol in enumerate(symbols):
        # Small delay between requests to avoid rate limiting
        if i > 0:
            time.sleep(1.0)

        ticker = yf.Ticker(symbol, session=session)
        info = ticker.info

        # Get current price - try multiple fields as availability varies
        price = info.get("regularMarketPrice") or info.get("currentPrice") or 0.0

        # Get previous close to calculate change
        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose") or price

        # Calculate change percentage
        if prev_close and prev_close != 0:
            change_percent = ((price - prev_close) / prev_close) * 100
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

    return results
