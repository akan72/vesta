"""CLI entry point for Vesta."""

import os
import sys

import click

from vesta.board import send_to_board
from vesta.formatter import board_to_text, format_for_board
from vesta.prices import fetch_prices

DEFAULT_SYMBOLS = ["BTC-USD", "GLD", "GOOG"]


@click.command()
@click.option(
    "--symbols",
    "-s",
    envvar="VESTA_SYMBOLS",
    default=",".join(DEFAULT_SYMBOLS),
    help="Comma-separated list of Yahoo Finance symbols (max 6)",
)
@click.option(
    "--api-key",
    "-k",
    envvar="VESTABOARD_RW_KEY",
    help="Vestaboard Read/Write API key",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Preview the board without sending to Vestaboard",
)
def main(symbols: str, api_key: str | None, dry_run: bool) -> None:
    """Display equity and crypto prices on a Vestaboard.

    Fetches current prices from Yahoo Finance and displays them on your
    Vestaboard. Each symbol shows the current price and daily change percentage.

    Examples:

        vesta                          # Use defaults (BTC, GLD, GOOG)

        vesta -s AAPL,MSFT,NVDA        # Custom symbols

        vesta --dry-run                # Preview without sending

        VESTA_SYMBOLS=SPY,QQQ vesta    # Via environment variable
    """
    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]

    if not symbol_list:
        click.echo("Error: No symbols provided", err=True)
        sys.exit(1)

    if len(symbol_list) > 6:
        click.echo("Warning: Only first 6 symbols will be displayed", err=True)
        symbol_list = symbol_list[:6]

    # Check for API key if not dry run
    if not dry_run and not api_key:
        click.echo(
            "Error: VESTABOARD_RW_KEY environment variable or --api-key required",
            err=True,
        )
        click.echo("Get your API key at https://web.vestaboard.com", err=True)
        sys.exit(1)

    # Fetch prices
    click.echo(f"Fetching prices for: {', '.join(symbol_list)}")
    try:
        prices = fetch_prices(symbol_list)
    except Exception as e:
        click.echo(f"Error fetching prices: {e}", err=True)
        sys.exit(1)

    # Format for board
    board = format_for_board(prices)

    # Preview
    click.echo("\nBoard preview:")
    click.echo("-" * 22)
    click.echo(board_to_text(board))
    click.echo("-" * 22)

    # Send to board
    if dry_run:
        click.echo("\nDry run - not sending to Vestaboard")
    else:
        click.echo("\nSending to Vestaboard...")
        try:
            send_to_board(board, api_key)
            click.echo("Done!")
        except Exception as e:
            click.echo(f"Error sending to board: {e}", err=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
