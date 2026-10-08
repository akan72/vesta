"""Provider batching, credential handling, and preview/send safety checks."""

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.error import HTTPError

from click.testing import CliRunner

from vesta import alpaca
from vesta.cli import main
from vesta.prices import PriceData, PriceFetchError, RateLimitError


class FixedClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 8, 18, 47, tzinfo=timezone.utc)


class AlpacaTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "APCA_API_KEY_ID": "fixture-key", "APCA_API_SECRET_KEY": "fixture-secret",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    @staticmethod
    def batch(path, params, credentials):
        if path.endswith("snapshots"):
            return {symbol: {
                "minuteBar": {"t": "2026-10-08T18:45:00Z", "c": 110},
                "prevDailyBar": {"t": "2026-10-07T04:00:00Z", "c": 100},
            } for symbol in params["symbols"].split(",")}
        return {"bars": {symbol: [
            {"t": "2026-10-07T23:55:00Z", "c": 80000},
            {"t": "2026-10-08T18:25:00Z", "c": 84000},
        ] for symbol in params["symbols"].split(",")}, "next_page_token": None}

    def test_batches_six_instruments_and_preserves_order_and_labels(self):
        with patch.object(alpaca, "_request", side_effect=self.batch) as request, patch.object(alpaca, "datetime", FixedClock):
            prices = alpaca.fetch_alpaca_prices(["BTC-USD", "SPCX", "GLD", "GOOG", "META", "VTI"])
        self.assertEqual(request.call_count, 2)
        self.assertEqual([q.symbol for q in prices], ["BTC", "SPCX", "GLD", "GOOG", "META", "VTI"])
        self.assertEqual(prices[0].price, 84000)
        self.assertEqual(prices[0].change_percent, 5)
        parameters = {call.args[0]: call.args[1] for call in request.call_args_list}
        self.assertEqual(parameters["/v2/stocks/snapshots"]["symbols"], "SPCX,GLD,GOOG,META,VTI")
        self.assertEqual(parameters["/v1beta3/crypto/us/bars"]["symbols"], "BTC/USD")

    def test_bare_btc_remains_an_equity_and_crypto_is_batched(self):
        with patch.object(alpaca, "_request", side_effect=self.batch) as request, patch.object(alpaca, "datetime", FixedClock):
            alpaca.fetch_alpaca_prices(["BTC", "BTC/USD", "ETH/USD"])
        parameters = {call.args[0]: call.args[1] for call in request.call_args_list}
        self.assertEqual(parameters["/v2/stocks/snapshots"]["symbols"], "BTC")
        self.assertEqual(parameters["/v1beta3/crypto/us/bars"]["symbols"], "BTC/USD,ETH/USD")

    def test_missing_credentials_do_not_make_requests(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(alpaca, "_request") as request:
            with self.assertRaises(PriceFetchError):
                alpaca.fetch_alpaca_prices(["GLD"])
        request.assert_not_called()

    def test_duplicate_bitcoin_aliases_fail_before_fetch(self):
        with patch.object(alpaca, "_request") as request:
            with self.assertRaises(PriceFetchError):
                alpaca.fetch_alpaca_prices(["BTC-USD", "BTC/USD"])
        request.assert_not_called()

    def test_partial_stock_batch_is_rejected(self):
        with patch.object(alpaca, "_request", return_value={}), patch.object(alpaca, "datetime", FixedClock):
            with self.assertRaises(PriceFetchError):
                alpaca.fetch_alpaca_prices(["GLD"])

    def test_crypto_pagination_is_rejected(self):
        response = self.batch("bars", {"symbols": "BTC/USD"}, None)
        response["next_page_token"] = "more"
        with patch.object(alpaca, "_request", return_value=response), patch.object(alpaca, "datetime", FixedClock):
            with self.assertRaises(PriceFetchError):
                alpaca.fetch_alpaca_prices(["BTC/USD"])

    def test_http_429_is_a_rate_limit(self):
        with patch.object(alpaca, "build_opener") as opener:
            opener.return_value.open.side_effect = HTTPError("fixture", 429, "fixture", {}, None)
            with self.assertRaises(RateLimitError):
                alpaca._request("/v2/stocks/snapshots", {"symbols": "GLD"}, ("fixture-key", "fixture-secret"))

    def test_redirect_is_not_followed(self):
        handler = alpaca.NoRedirects()
        self.assertIsNone(handler.redirect_request(None, None, 302, "", {}, "https://example.com"))

    def test_alpaca_preview_429_uses_demo_without_sending(self):
        with patch("vesta.cli.fetch_alpaca_prices", side_effect=RateLimitError("Alpaca rate limited")), patch("vesta.cli.send_to_board") as send:
            result = CliRunner().invoke(main, ["--provider", "alpaca", "--dry-run"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("$83,436", result.output)
        send.assert_not_called()

    def test_alpaca_send_429_does_not_send_demo(self):
        with patch("vesta.cli.fetch_alpaca_prices", side_effect=RateLimitError("Alpaca rate limited")), patch("vesta.cli.send_to_board") as send:
            result = CliRunner().invoke(main, ["--provider", "alpaca", "--api-key", "fixture-board-key"])
        self.assertEqual(result.exit_code, 1)
        self.assertNotIn("$83,436", result.output)
        send.assert_not_called()

    def test_yahoo_remains_default(self):
        with patch("vesta.cli.fetch_prices", return_value=[PriceData("GLD", 377, 1)]) as yahoo, patch("vesta.cli.fetch_alpaca_prices") as other:
            result = CliRunner().invoke(main, ["--dry-run"])
        self.assertEqual(result.exit_code, 0, result.output)
        yahoo.assert_called_once()
        other.assert_not_called()

    def test_demo_needs_no_credentials_or_provider_request(self):
        with patch.dict(os.environ, {}, clear=True), patch("vesta.cli.fetch_alpaca_prices") as fetch:
            result = CliRunner().invoke(main, ["--provider", "alpaca", "--demo"])
        self.assertEqual(result.exit_code, 0, result.output)
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
