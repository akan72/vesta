"""Batch USD stock snapshots and delayed crypto bars from Alpaca's free feeds."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from math import isfinite
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from vesta.prices import PriceData, PriceFetchError, RateLimitError


class NoRedirects(HTTPRedirectHandler):
    """Never forward authentication headers to a redirect destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _request(path: str, parameters: dict, credentials: tuple[str, str]) -> dict:
    url = "https://data.alpaca.markets" + path + "?" + urlencode(parameters)
    request = Request(url, headers={
        "Accept": "application/json",
        "APCA-API-KEY-ID": credentials[0],
        "APCA-API-SECRET-KEY": credentials[1],
    })
    try:
        with build_opener(NoRedirects()).open(request, timeout=30) as response:
            payload = response.read(1_048_577)
        if len(payload) > 1_048_576:
            raise PriceFetchError("Alpaca returned an oversized response.")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Not an object")
        return data
    except HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError("Alpaca rate limited the request; try again later.") from None
        if exc.code in (401, 403):
            raise PriceFetchError("Alpaca rejected the credentials or data entitlement.") from None
        raise PriceFetchError(f"Alpaca returned HTTP {exc.code}.") from None
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise PriceFetchError("Could not retrieve valid Alpaca data; retry later.") from None


def _close(bar: dict) -> tuple[datetime, float]:
    at = datetime.fromisoformat(bar["t"].replace("Z", "+00:00"))
    value = bar["c"]
    if at.tzinfo is None or isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
        raise ValueError("Invalid close")
    return at.astimezone(timezone.utc), float(value)


def fetch_alpaca_prices(symbols: list[str]) -> list[PriceData]:
    """Make at most two requests: one stock batch and one crypto batch."""
    key = os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise PriceFetchError("Set APCA_API_KEY_ID and APCA_API_SECRET_KEY for Alpaca market data.")
    credentials = (key, secret)
    # Only the explicit Yahoo Bitcoin ID is an alias; BTC remains an ETF ticker.
    instruments = ["BTC/USD" if symbol == "BTC-USD" else symbol for symbol in symbols]
    if len(set(instruments)) != len(instruments):
        raise PriceFetchError("Provide each instrument only once (BTC-USD and BTC/USD are the same instrument).")
    crypto = [symbol for symbol in instruments if "/" in symbol]
    stocks = [symbol for symbol in instruments if "/" not in symbol]
    if any(len(symbol.split("/")) != 2 or not symbol.endswith("/USD") or not symbol.split("/")[0] for symbol in crypto):
        raise PriceFetchError("Alpaca crypto symbols must be USD pairs such as BTC/USD or ETH/USD.")
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    jobs = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        if stocks:
            jobs["stocks"] = pool.submit(_request, "/v2/stocks/snapshots", {"symbols": ",".join(stocks), "feed": "iex", "currency": "USD"}, credentials)
        if crypto:
            jobs["crypto"] = pool.submit(_request, "/v1beta3/crypto/us/bars", {
                "symbols": ",".join(crypto), "timeframe": "5Min",
                "start": (day_start - timedelta(days=2)).isoformat(),
                "end": (now - timedelta(minutes=20)).isoformat(),
                "limit": "10000", "sort": "asc",
            }, credentials)
        results, failures = {}, []
        for kind, future in jobs.items():
            try:
                results[kind] = future.result()
            except PriceFetchError as exc:
                failures.append(exc)
        if failures:
            # A rate limit in either batch must use the same preview fallback.
            raise next((exc for exc in failures if isinstance(exc, RateLimitError)), failures[0])
    prices = []
    for symbol in instruments:
        try:
            if symbol in stocks:
                snapshot = results["stocks"][symbol]
                at, price = _close(snapshot["minuteBar"])
                previous_at, previous = _close(snapshot["prevDailyBar"])
                if previous_at >= at or now - at > timedelta(days=7):
                    raise ValueError("Invalid comparison")
                label = symbol
            else:
                response = results["crypto"]
                if response.get("next_page_token"):
                    raise ValueError("Incomplete batch")
                bars = [_close(bar) for bar in response["bars"][symbol]]
                if not bars or any(bars[i][0] <= bars[i-1][0] for i in range(1, len(bars))):
                    raise ValueError("Invalid bar order")
                at, price = bars[-1]
                reference = at.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(minutes=5)
                previous = next(close for timestamp, close in bars if timestamp == reference)
                if now - at > timedelta(hours=1):
                    raise ValueError("Stale crypto data")
                label = symbol.split("/")[0]
            if at > now + timedelta(minutes=1):
                raise ValueError("Future quote")
            change = (price - previous) / previous * 100
            if not isfinite(change):
                raise ValueError("Invalid change")
            prices.append(PriceData(label, price, change))
        except (KeyError, TypeError, ValueError, StopIteration, IndexError, AttributeError):
            raise PriceFetchError(f"Incomplete or invalid Alpaca quotes for {symbol}; retry later.") from None
    return prices
