"""Offline behavior tests for the right-hand price-change indicator."""

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from vesta.cli import main
from vesta.formatter import board_to_text, format_change, format_for_board
from vesta.prices import PriceData


class PriceChangeColorTests(unittest.TestCase):
    def test_color_matches_displayed_change_in_rightmost_cell(self):
        cases = [
            (2.3, 66, "+2.3%", "🟩"),
            (-0.5, 63, "-0.5%", "🟥"),
            (0.0, 70, "+0.0%", "⬛"),
            (-0.0, 70, "+0.0%", "⬛"),
            (0.049, 70, "+0.0%", "⬛"),
            (-0.049, 70, "+0.0%", "⬛"),
            (0.051, 66, "+0.1%", "🟩"),
            (-0.051, 63, "-0.1%", "🟥"),
        ]
        for change, color, percentage, square in cases:
            with self.subTest(change=change):
                board = format_for_board([PriceData("BTC", 97500, change)])
                self.assertEqual(len(board), 6)
                self.assertTrue(all(len(row) == 22 for row in board))
                self.assertEqual(board[0][-1], color)
                preview = board_to_text(board).splitlines()
                self.assertTrue(preview[0].endswith(percentage + " " + square))
                self.assertIn("BTC", preview[0])
                self.assertIn("$97,500", preview[0])
                self.assertTrue(all(row == [0] * 22 for row in board[1:]))

    def test_all_six_rows_receive_their_own_color(self):
        prices = [
            PriceData(f"TEST{i}", 123.0, change)
            for i, change in enumerate([1, -1, 0, 0.01, -0.01, 0.1])
        ]
        board = format_for_board(prices)
        self.assertEqual([row[-1] for row in board], [66, 63, 70, 70, 70, 66])

    def test_btc_price_still_fits_at_six_figures(self):
        board = format_for_board([PriceData("BTC", 123456, 2.3)])
        self.assertIn("$123,456", board_to_text(board))
        self.assertEqual(board[0][-1], 66)

    def test_displayed_negative_zero_is_normalized(self):
        self.assertEqual(format_change(-0.049), "+0.0%")

    def test_oversized_fields_are_not_silently_clipped(self):
        for price, change in [(10_000_000, 2.3), (97500, 1234.0)]:
            with self.subTest(price=price, change=change):
                with self.assertRaises(ValueError):
                    format_for_board([PriceData("BTC", price, change)])

    def test_dry_run_renders_colors_without_sending(self):
        prices = [
            PriceData("BTC", 97500, 2.3),
            PriceData("GLD", 245, -0.5),
            PriceData("GOOG", 192, -0.049),
        ]
        with (
            patch("vesta.cli.fetch_prices", return_value=prices),
            patch("vesta.cli.send_to_board") as send,
        ):
            result = CliRunner().invoke(main, ["--dry-run"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("+2.3% 🟩", result.output)
        self.assertIn("-0.5% 🟥", result.output)
        self.assertIn("+0.0% ⬛", result.output)
        send.assert_not_called()

    def test_oversized_fields_fail_cleanly_without_sending(self):
        with (
            patch(
                "vesta.cli.fetch_prices",
                return_value=[PriceData("BTC", 10_000_000, 2.3)],
            ),
            patch("vesta.cli.send_to_board") as send,
        ):
            result = CliRunner().invoke(main, ["--api-key", "test-only"])
        self.assertEqual(result.exit_code, 1, result.output)
        self.assertIn("Cannot format board", result.output)
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
