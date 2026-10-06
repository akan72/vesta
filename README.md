# vesta

Display crypto and equity prices on your Vestaboard.

## Installation

```bash
# Install as a uv tool (recommended)
uv tool install git+https://github.com/akan72/vesta

# Or run directly without installing
uvx --from git+https://github.com/akan72/vesta vesta

# Or install from local source
uv tool install .
```

## Setup

1. Get your Vestaboard Read/Write API key from [web.vestaboard.com](https://web.vestaboard.com). 
    - You need to have "Owner" access in the Vetaboard org to obtain the API key.
2. Set the environment variable:

```bash
export VESTABOARD_RW_KEY="your-api-key-here"
```

## Usage

```bash
# Display default symbols (BTC, GLD, GOOG)
vesta

# Display custom symbols
vesta --symbols AAPL,MSFT,NVDA,TSLA

# Preview without sending to Vestaboard
vesta --dry-run

# Set symbols via environment variable
export VESTA_SYMBOLS="SPY,QQQ,IWM"
vesta
```

## Symbols

Use any valid Yahoo Finance symbol:

- **Crypto**: `BTC-USD`, `ETH-USD`, `SOL-USD`
- **Stocks**: `AAPL`, `GOOG`, `MSFT`, `NVDA`
- **ETFs**: `SPY`, `QQQ`, `GLD`, `SLV`
- **Futures**: `GC=F` (Gold), `CL=F` (Oil)

Maximum 6 symbols can be displayed (one per row).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VESTABOARD_RW_KEY` | Required. Your Vestaboard Read/Write API key |
| `VESTA_SYMBOLS` | Optional. Comma-separated list of symbols (default: BTC-USD,GLD,GOOG) |

## Display Format

Each row shows:
- Symbol (6 characters)
- Current price
- Daily change percentage
- A color square in the far-right cell: green for a positive change, red for a
  negative change, and black when the displayed percentage rounds to `0.0%`.
  The signed percentage remains visible alongside the color.

Example:
```
BTC     $97,500 +2.3%🟩
GLD        $245 -0.5%🟥
GOOG       $192 +0.0%⬛
```

Color squares represent one physical board cell each; their width in a terminal
depends on the terminal's emoji font. Prices and percentages that cannot fit
alongside the color cell cause an error without updating the board.

Run the formatter tests without fetching quotes or contacting Vestaboard:

```bash
python -m unittest discover -s tests -v
```

## License

MIT
