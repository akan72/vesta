# Vesta

Display equity and crypto prices on your Vestaboard, with a color
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

If either market data provider rate-limits a preview, Vesta automatically uses fixed BTC, SPCX,
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
if the provider rate-limits or any quote is unavailable, Vesta exits nonzero without
updating the board.

## Market data providers

Yahoo Finance remains the default, with no market data credentials required:

```bash
vesta --provider yahoo --preview --symbols BTC-USD,SPCX,GLD,GOOG,META,VTI
```

Alpaca uses its free IEX feed for stocks/ETFs and delayed five-minute bars for
crypto. Set `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` in your environment;
these are separate from the Vestaboard key. Do not commit credentials. Then run:

```bash
vesta --provider alpaca --preview --symbols BTC/USD,SPCX,GLD,GOOG,META,VTI
vesta --provider alpaca --dry-run
vesta --provider alpaca --preview-file /tmp/vesta-preview.html
```

Set `VESTA_PROVIDER=alpaca` to make Alpaca the default. `--demo` works offline
with either provider and requires no keys. Rate limits fall back to the same
six sample rows in local previews; sending never substitutes synthetic prices.

Alpaca batches all stocks into one snapshot request and all crypto into one
bars request, with at most two concurrent requests and no retries. A stock's
sampled minute close is compared with its previous daily close. Crypto bars are
explicitly delayed by 20 minutes for free historical-data access; changes compare
with the last five-minute bar before the sampled UTC day's midnight. The free
IEX feed covers one exchange and can differ from consolidated market prices.
Missing, invalid or incomplete data fails the whole fetch without updating the
board. These are sampled prices, not streaming quotes.

Alpaca crypto must use USD pairs such as `BTC/USD` or `ETH/USD`. The exact alias
`BTC-USD` is accepted as `BTC/USD`; bare `BTC` remains an equity ticker. Provider
identifiers are passed separately from display labels, which use the pair's base
symbol for crypto. Other Yahoo-style crypto IDs should be written as Alpaca pairs.

## Symbols and prices

For Yahoo, Vesta fetches market data through `yfinance`. Inputs to `--symbols` /
`-s` or `VESTA_SYMBOLS` must use Yahoo Finance ticker syntax, with one to six
unique tickers. Defaults: `BTC-USD,GLD,GOOG`. Bitcoin is `BTC-USD`; `BTC` is
a separate ETF ticker.

Use USD-denominated instruments; prices have a dollar sign and Vesta does
not convert currencies or validate the quote currency returned by the provider.

Yahoo quotes are the latest available adjusted daily closes and changes from the
preceding closes, not streaming prices. Five days of history allow for
non-trading days. Missing quotes are never displayed as fabricated zero prices.

The complete input ticker is passed unchanged to yfinance. For display only,
Vesta removes the exact trailing `-USD`, then limits the label to six characters.
It does not strip arbitrary `-<currency>` or exchange suffixes. This is a
temporary convention for the current USD display: `BTC-USD` and the ETF ticker
`BTC` both render as BTC, and truncation can also produce identical labels.

The Alpaca adapter keeps input IDs separate from board labels and uses explicit
USD-pair syntax plus the Bitcoin alias above. Neither provider converts
non-USD Yahoo instruments into dollars.

The rightmost board cell contains the color square. Terminal previews add a space
before the square for readability. If the price or percentage cannot fit, the
command reports an error without updating the board.

## License

MIT
