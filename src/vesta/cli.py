"""CLI entry point for Vesta."""

import tempfile
import webbrowser
from pathlib import Path

import click

from vesta.board import send_to_board
from vesta.formatter import board_to_text, format_for_board
from vesta.preview import write_preview
from vesta.prices import PriceData, PriceFetchError, RateLimitError, fetch_prices

DEFAULT_SYMBOLS = ["BTC-USD", "GLD", "GOOG"]
DEMO_PRICES = [
    PriceData("BTC", 83_436, 2.8),
    PriceData("SPCX", 169, 1.7),
    PriceData("GLD", 377, -1.5),
    PriceData("GOOG", 343, -0.5),
    PriceData("META", 723, 2.1),
    PriceData("VTI", 380, 0.0),
]


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--symbols",
    "-s",
    envvar="VESTA_SYMBOLS",
    default=",".join(DEFAULT_SYMBOLS),
    show_default=True,
    show_envvar=True,
    help="yfinance tickers (1–6); Bitcoin: BTC-USD.",
)
@click.option(
    "--api-key",
    "-k",
    envvar="VESTABOARD_RW_KEY",
    show_envvar=True,
    help="Vestaboard Read/Write API key; required only when sending.",
)
@click.option(
    "--dry-run", "-d", is_flag=True, help="Print the board without sending it."
)
@click.option(
    "--preview", is_flag=True, help="Open a local visual preview without sending."
)
@click.option(
    "--preview-file",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Write an HTML preview without opening a browser or sending.",
)
@click.option(
    "--demo",
    is_flag=True,
    help="Preview six fixed sample instruments offline; never sends.",
)
def main(
    symbols: str,
    api_key: str | None,
    dry_run: bool,
    preview: bool,
    preview_file: Path | None,
    demo: bool,
) -> None:
    """Display the prices of stocks and crypto on your Vestaboard!

    \b
    Sending market data to your board requires a Vestaboard API key.
    Local preview mode doesn't require an API key. You can also preview
    the expected output using synthetic data.
    Synthetic data is used automatically in local previews if the market
    data provider rate-limits you.

    Symbols currently use yfinance's Yahoo Finance ticker format.

    Examples:

    \b
      Send the default instruments:
        vesta

    \b
      Send selected instruments:
        vesta --symbols BTC-USD,SPCX,GLD,GOOG,META,VTI

    \b
      Preview selected instruments in the terminal:
        vesta --dry-run --symbols AAPL,MSFT,NVDA

    \b
      Open a visual preview of selected instruments:
        vesta --preview --symbols BTC-USD,SPCX,GLD,GOOG,META,VTI

    \b
      Save an HTML preview to a path without opening a browser:
        vesta --symbols GLD,GOOG --preview-file /tmp/vesta-preview.html

    \b
      Preview all six demo instruments offline:
        vesta --demo --preview

    \b
      Save an offline demo preview (quote paths containing spaces):
        vesta --demo --preview-file "./board preview.html"
    """
    preview_only = dry_run or preview or preview_file is not None or demo
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not 1 <= len(symbol_list) <= 6:
        raise click.UsageError("Provide between 1 and 6 symbols.")
    if len(set(symbol_list)) != len(symbol_list):
        raise click.UsageError("Provide each symbol only once.")
    if not preview_only and not api_key:
        raise click.ClickException(
            "Set VESTABOARD_RW_KEY or use --dry-run / --preview."
        )

    use_demo = demo
    if not use_demo:
        click.echo(f"Fetching daily closes for: {', '.join(symbol_list)}")
        try:
            prices = fetch_prices(symbol_list)
        except RateLimitError as exc:
            if not preview_only:
                raise click.ClickException(f"{exc} Board not updated.") from exc
            click.echo(
                "Yahoo Finance rate limited the request; using demo data for this preview.",
                err=True,
            )
            use_demo = True
        except PriceFetchError as exc:
            raise click.ClickException(f"{exc} Board not updated.") from exc
        except Exception as exc:
            raise click.ClickException(
                f"Error fetching prices: {exc}. Board not updated."
            ) from exc
    if use_demo:
        demo_symbols = ", ".join(price.symbol for price in DEMO_PRICES)
        click.echo(f"Demo: fixed {demo_symbols} sample values, not live quotes.")
        prices = DEMO_PRICES

    try:
        board = format_for_board(prices)
    except ValueError as exc:
        raise click.ClickException(f"Cannot format board: {exc}") from exc

    click.echo("\nBoard preview:\n" + "─" * 22)
    click.echo(board_to_text(board))
    click.echo("─" * 22)
    if preview or preview_file:
        try:
            if preview_file is None:
                with tempfile.NamedTemporaryFile(
                    prefix="vesta-", suffix=".html", delete=False
                ) as output:
                    preview_file = Path(output.name)
            write_preview(board, preview_file, demo=use_demo)
            click.echo(f"HTML preview: {preview_file.resolve()}")
            if preview and not webbrowser.open(preview_file.resolve().as_uri()):
                click.echo(
                    "Could not open a browser; open the HTML preview file manually.",
                    err=True,
                )
        except OSError as exc:
            raise click.ClickException(f"Cannot save preview: {exc}") from exc

    if preview_only:
        click.echo("\nPreview only — board not updated.")
        return
    click.echo("\nSending to Vestaboard...")
    try:
        send_to_board(board, api_key)
    except Exception as exc:
        raise click.ClickException(f"Error sending to board: {exc}") from exc
    click.echo("Sent to Vestaboard.")


if __name__ == "__main__":
    main()
