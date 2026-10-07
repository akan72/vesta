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
    PriceData("BTC", 97500, 2.3),
    PriceData("GLD", 245, -0.5),
    PriceData("GOOG", 192, 0.0),
]


@click.command()
@click.option(
    "--symbols",
    "-s",
    envvar="VESTA_SYMBOLS",
    default=",".join(DEFAULT_SYMBOLS),
    help="Comma-separated Yahoo Finance symbols (1–6).",
)
@click.option(
    "--api-key", "-k", envvar="VESTABOARD_RW_KEY", help="Vestaboard Read/Write API key."
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
    "--demo", is_flag=True, help="Preview fixed sample prices offline; never sends."
)
def main(
    symbols: str,
    api_key: str | None,
    dry_run: bool,
    preview: bool,
    preview_file: Path | None,
    demo: bool,
) -> None:
    """Display daily closing prices on a Vestaboard.

    vesta --dry-run      Preview in your terminal.

    vesta --preview      Preview in your browser.

    vesta --demo         Preview offline sample data.

    vesta                Fetch fresh prices and send to your board.
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
        click.echo("Demo: fixed BTC, GLD, GOOG sample values, not live quotes.")
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
