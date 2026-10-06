"""A self-contained HTML rendering of the exact board payload."""

from datetime import datetime, timezone
from html import escape
from pathlib import Path

from vesta.board import validate_board
from vesta.formatter import CHAR_CODES, board_to_text

COLORS = {
    63: "#eb4842",
    64: "#f48a39",
    65: "#f4ce49",
    66: "#51aa6a",
    67: "#4a87cd",
    68: "#9c69c6",
    69: "#f5f2e8",
    70: "#151515",
    71: "#f5f2e8",
}


def render_preview(rows: list[list[int]], *, demo: bool = False) -> str:
    """Render every cell from character codes, using no external assets or scripts."""
    validate_board(rows)
    characters = {code: char for char, code in CHAR_CODES.items()}
    cells = []
    for row in rows:
        for code in row:
            if code in COLORS:
                cells.append(
                    f'<span class="tile chip" style="background:{COLORS[code]}" '
                    f'aria-label="Color chip {code}"></span>'
                )
            else:
                char = escape(characters[code])
                cells.append(f'<span class="tile">{char}</span>')
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = escape(board_to_text(rows))
    description = (
        "Sample prices for layout testing. These are not live quotes."
        if demo
        else "Inspect the layout before sending it to your Vestaboard."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vesta — Board preview</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin:0; min-height:100vh; background:#eeeae2; color:#252720;
 font-family:system-ui,sans-serif; padding:clamp(24px,6vw,88px); }}
main {{ max-width:1120px; margin:auto; }}
header {{ display:flex; justify-content:space-between; align-items:center; gap:20px; }}
.brand {{ font-size:15px; font-weight:750; letter-spacing:.2em; text-transform:uppercase; }}
.badge {{ font-size:12px; border:1px solid #bdc6b7; background:#e3e8df;
 padding:8px 12px; border-radius:20px; white-space:nowrap; }}
h1 {{ font-family:Georgia,serif; font-size:clamp(32px,5vw,58px); font-weight:400;
 letter-spacing:-.035em; margin:60px 0 14px; }}
p {{ color:#62655c; line-height:1.6; }}
.board {{ display:grid; grid-template-columns:repeat(22,minmax(0,1fr));
 gap:clamp(2px,.45vw,6px); padding:clamp(10px,2vw,26px); background:#111210;
 border-radius:12px; border:1px solid #383a33; box-shadow:0 20px 40px #25272022;
 margin:36px 0 28px; }}
.tile {{ position:relative; display:flex; align-items:center; justify-content:center;
 aspect-ratio: .72; border-radius:3px; background:linear-gradient(#292b27,#20221e);
 color:#f2f0e8; font-family:ui-monospace,Menlo,Consolas,monospace;
 font-size:clamp(9px,2.3vw,30px); font-weight:600; box-shadow:inset 0 0 0 1px #34362f; }}
.tile::after {{ content:""; position:absolute; left:0; right:0; top:50%;
 border-top:1px solid #090a08; opacity:.75; }}
.meta {{ display:flex; justify-content:space-between; gap:16px; color:#74776d;
 font-size:12px; border-bottom:1px solid #d6d5cc; padding-bottom:24px; }}
details {{ margin-top:28px; color:#62655c; font-size:13px; }}
summary {{ cursor:pointer; }}
pre {{ overflow:auto; padding:20px; background:#e4e1d8; line-height:1.8; }}
</style>
</head>
<body><main>
<header><span class="brand">Vesta</span><span class="badge">Preview · board unchanged</span></header>
<h1>Your next board.</h1>
<p>{description}</p>
<div class="board" role="img" aria-label="Vestaboard preview: {escape(board_to_text(rows), quote=True)}">
{"".join(cells)}
</div>
<div class="meta"><span>{timestamp}</span></div>
<details><summary>Text view</summary><pre>{text}</pre></details>
</main></body>
</html>
"""


def write_preview(rows: list[list[int]], path: Path, *, demo: bool = False) -> None:
    path.write_text(render_preview(rows, demo=demo), encoding="utf-8")
