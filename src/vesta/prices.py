"""Fetch daily closes from Yahoo Finance without hiding rate-limit failures."""

from dataclasses import dataclass
from math import isfinite

import yfinance as yf
from yfinance.exceptions import YFRateLimitError


class PriceFetchError(Exception):
    """Raised when a complete, valid set of quotes is unavailable."""


class RateLimitError(PriceFetchError):
    """Raised when a market data provider explicitly reports a rate limit."""


@dataclass
class PriceData:
    """Latest daily close and percentage change for a display symbol."""

    symbol: str
    price: float
    change_percent: float


def fetch_prices(symbols: list[str]) -> list[PriceData]:
    """Require two valid closes for every symbol; never fabricate zero quotes."""
    results = []
    for symbol in symbols:
        try:
            # download() catches this exception internally; history() surfaces it.
            data = yf.Ticker(symbol).history(
                period="5d", interval="1d", auto_adjust=True, actions=False, timeout=15
            )
        except YFRateLimitError as exc:
            raise RateLimitError(
                "Yahoo Finance rate limited the request; try again later."
            ) from exc
        except Exception as exc:
            raise PriceFetchError(f"Could not fetch {symbol}: {exc}") from exc

        if data is None or data.empty or "Close" not in data.columns:
            raise PriceFetchError(
                f"No daily closes for {symbol}. Check the symbol or retry later."
            )
        closes = data["Close"].dropna()
        if len(closes) < 2:
            raise PriceFetchError(
                f"Two daily closes are required for {symbol}; retry later."
            )
        previous, price = float(closes.iloc[-2]), float(closes.iloc[-1])
        if not isfinite(price) or not isfinite(previous) or previous == 0:
            raise PriceFetchError(f"Invalid daily closes for {symbol}; retry later.")
        change = (price - previous) / abs(previous) * 100
        if not isfinite(change):
            raise PriceFetchError(
                f"Invalid percentage change for {symbol}; retry later."
            )
        results.append(PriceData(symbol.removesuffix("-USD"), price, change))
    return results
