from base64 import b64encode
from pathlib import Path

github_dir = Path(__file__).resolve().parents[1]
# Latin variable WOFF2 from @fontsource-variable/geist 5.3.0 (SIL OFL 1.1).
font = b64encode((github_dir / "fonts/Geist-latin.woff2").read_bytes()).decode("ascii")
typography = f"""
    @font-face {{
      font-family: "Geist";
      src: url("data:font/woff2;base64,{font}") format("woff2");
      font-weight: 100 900;
      font-style: normal;
    }}
    .header, .stat, .rank-text, .lang-name {{
      font-family: "Geist", "Segoe UI", Arial, sans-serif;
      font-variant-numeric: tabular-nums;
    }}
    .stat.bold {{ font-weight: 600; }}
    .lang-name {{ font-weight: 500; }}
"""

for name in ("stats.svg", "top-langs.svg"):
    card = github_dir.parent / "profile" / name
    svg = card.read_text(encoding="utf-8")
    closing_style = "\n        </style>"
    if svg.count(closing_style) != 1 or "data:font/woff2;base64," in svg:
        raise ValueError(f"Expected one unmodified stylesheet in {card}")
    card.write_text(svg.replace(closing_style, typography + "        </style>"), encoding="utf-8")
