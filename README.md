# Vesta

Display equity and crypto daily closing prices on your Vestaboard, with a color
square on the right: green for positive changes, red for negative changes, and
black when the displayed change rounds to `0.0%`.

## Install

Install with [uv](https://docs.astral.sh/uv/guides/tools/) and Python 3.10 or newer:

```bash
uv tool install git+https://github.com/akan72/vesta
vesta --help
```

Use `vesta -h` or `vesta --help` for options, environment variables, and concrete
examples of sending, selecting symbols, and saving previews.

For a local checkout, an editable installation follows source changes after a
`git pull`:

```bash
uv tool install --editable .
```

For an existing non-editable local installation, refresh it after pulling:

```bash
uv tool install --reinstall .
```

## Preview

Preview in the terminal or open a local HTML rendering. Neither requires board
credentials or sends anything to Vestaboard:

```bash
vesta --dry-run
vesta --dry-run --symbols AAPL,MSFT,NVDA
vesta --preview
```

For a headless session, save the HTML without opening a browser:

```bash
vesta --symbols GLD,GOOG --preview-file /tmp/vesta-preview.html
```

If Yahoo Finance rate-limits a preview, Vesta automatically uses fixed BTC, SPCX,
GLD, GOOG, META, and VTI sample values. Both the terminal and HTML label them as
demo data. Other fetch failures produce an error instead of sample data.

To preview the sample layout offline:

```bash
vesta --demo
vesta --demo --preview
vesta --demo --preview-file "./board preview.html"
```

Demo mode always previews, and uses its fixed sample symbols regardless of
`--symbols`. It never sends sample prices to the board.
The six rows show three green squares (BTC, SPCX, META), two red squares (GLD,
GOOG), and one black square (VTI).
Bitcoin's fixed sample price is $83,436, displayed as BTC.

For a market-data preview of the same six instruments, use Bitcoin's Yahoo
Finance symbol `BTC-USD`:

```bash
vesta --preview --symbols BTC-USD,SPCX,GLD,GOOG,META,VTI
```

`BTC` alone is an ETF ticker, not Bitcoin. Both display as BTC on the board.
Without `--symbols`, Vesta uses its three default instruments: BTC-USD, GLD,
and GOOG. `--demo` always uses six fixed sample rows.

![Six-instrument demo board](docs/demo-preview.png)

## Send

Vesta sends through the Vestaboard Python SDK using your Read/Write API key:

```bash
export VESTABOARD_RW_KEY="your-read-write-api-key"
vesta
vesta --symbols AAPL,MSFT,NVDA
```

You can also supply the key with `--api-key`. A normal send fetches fresh prices;
if Yahoo rate-limits or any quote is unavailable, Vesta exits nonzero without
updating the board.

## Symbols and prices

For now, Vesta fetches market data through `yfinance`. Inputs to `--symbols` /
`-s` or `VESTA_SYMBOLS` must use Yahoo Finance ticker syntax, with one to six
unique tickers. Defaults: `BTC-USD,GLD,GOOG`. Bitcoin is `BTC-USD`; `BTC` is
a separate ETF ticker.

Use USD-denominated instruments; prices have a dollar sign and Vesta does
not convert currencies or validate the quote currency returned by the provider.

Quotes are the latest available adjusted daily closes and changes from the
preceding closes, not streaming prices. Five days of history allow for
non-trading days. Missing quotes are never displayed as fabricated zero prices.

The complete input ticker is passed unchanged to yfinance. For display only,
Vesta removes the exact trailing `-USD`, then limits the label to six characters.
It does not strip arbitrary `-<currency>` or exchange suffixes. This is a
temporary convention for the current USD display: `BTC-USD` and the ETF ticker
`BTC` both render as BTC, and truncation can also produce identical labels.

When adding another provider or currency support, keep the provider's instrument
ID separate from the board label, asset type, and quote currency. Use explicit
instrument metadata or mappings for those fields rather than inferring them
from ticker suffixes.

The rightmost board cell contains the color square. Terminal previews add a space
before the square for readability. If the price or percentage cannot fit, the
command reports an error without updating the board.

## License

MIT
