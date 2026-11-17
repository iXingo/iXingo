"""Render the profile cards from the pinned Stats Action's SVG data."""

from html import escape
from pathlib import Path
from sys import argv
from xml.etree import ElementTree as ET

WIDTH, HEIGHT, PAD = 350, 324, 22
NS = "{http://www.w3.org/2000/svg}"
SUMMARY = (("stars", "Stars earned"), ("commits", "Commits · 1 year"), ("prs", "Pull requests"))
DETAILS = (
    ("prs_merged", "PRs merged"),
    ("prs_merged_percentage", "PR merge rate"),
    ("reviews", "PRs reviewed"),
    ("issues", "Issues opened"),
    ("discussions_started", "Discussions started"),
    ("discussions_answered", "Discussions answered"),
    ("contribs", "Repos contributed to · 1 year"),
)
LANGUAGE_COLORS = ("#3877ec", "#7a62d6", "#2c957e", "#d28b47", "#5089af", "#8c97aa")

STYLES = """
    svg {
      font-family: -apple-system, BlinkMacSystemFont, system-ui, "Segoe UI", sans-serif;
      font-variant-numeric: tabular-nums;
      --surface: #f7f8fa;
      --edge: #e0e4eb;
      --strong: #171c26;
      --muted: #495569;
      --accent: #215ac4;
      --accent-soft: #e8effc;
    }
    @media (prefers-color-scheme: dark) {
      svg {
        --surface: #171b23;
        --edge: #303744;
        --strong: #f2f5fa;
        --muted: #aeb9cc;
        --accent: #a8c6ff;
        --accent-soft: #253551;
      }
    }
    .surface { fill: var(--surface); stroke: var(--edge); }
    .rule { stroke: var(--edge); }
    .heading { fill: var(--strong); font-size: 19px; font-weight: 650; letter-spacing: -.35px; }
    .big { fill: var(--strong); font-size: 27px; font-weight: 660; letter-spacing: -.55px; }
    .caption { fill: var(--muted); font-size: 12px; }
    .label { fill: var(--muted); font-size: 13px; }
    .value { fill: var(--strong); font-size: 13px; font-weight: 620; }
    .rank-bg { fill: var(--accent-soft); }
    .rank { fill: var(--accent); font-size: 11px; font-weight: 640; }
    .value, .rank { text-anchor: end; }
"""


def svg_text(root, key):
    matches = root.findall(f".//{NS}text[@data-testid='{key}']")
    if not matches:
        raise ValueError(f"Missing {key} in generated SVG")
    return [" ".join("".join(node.itertext()).split()) for node in matches]


def text(x, y, css_class, value):
    return f'<text x="{x}" y="{y}" class="{css_class}">{escape(value)}</text>'


def card(title, description, body):
    content = "\n  ".join(body)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title description">
  <title id="title">{escape(title)}</title>
  <desc id="description">{escape(description)}</desc>
  <style>{STYLES}  </style>
  <rect class="surface" x="3.5" y="3.5" width="{WIDTH - 7}" height="{HEIGHT - 7}" rx="17"/>
  {text(PAD, 37, "heading", title)}
  {content}
</svg>
"""


def activity(source):
    root = ET.parse(source).getroot()
    values = {key: svg_text(root, key)[0] for key, _ in SUMMARY + DETAILS}
    values["prs_merged_percentage"] = values["prs_merged_percentage"].replace(" %", "%")
    rank = svg_text(root, "level-rank-icon")[0]
    body = [
        '<rect class="rank-bg" x="261" y="20" width="67" height="24" rx="12"/>',
        text(317, 36, "rank", f"Rank {rank}"),
    ]
    for index, (key, label) in enumerate(SUMMARY):
        x = PAD + 105 * index
        body.extend((text(x, 84, "big", values[key]), text(x, 105, "caption", label)))
    body.append(f'<path class="rule" d="M{PAD} 121H{WIDTH - PAD}"/>')
    for index, (key, label) in enumerate(DETAILS):
        y = 146 + 25 * index
        body.extend((text(PAD, y, "label", label), text(WIDTH - PAD, y, "value", values[key])))
    description = ", ".join(f"{label}: {values[key]}" for key, label in SUMMARY + DETAILS)
    return card("GitHub activity", f"{description}. Rank: {rank}.", body)


def languages(source):
    root = ET.parse(source).getroot()
    entries = [label.rsplit(maxsplit=1) for label in svg_text(root, "lang-name")]
    shares = [float(percent.removesuffix("%")) for _, percent in entries]
    total = sum(shares)
    if len(shares) > len(LANGUAGE_COLORS) or not all(0 <= share <= 100 for share in shares) or total == 0:
        raise ValueError("Unexpected language distribution")

    bar_width = WIDTH - 2 * PAD
    clip = f'<defs><clipPath id="bar"><rect x="{PAD}" y="78" width="{bar_width}" height="11" rx="5.5"/></clipPath></defs>'
    segments = []
    x = PAD
    for share, color in zip(shares, LANGUAGE_COLORS):
        part = share / total * bar_width
        segments.append(f'<rect x="{x:.3f}" y="78" width="{part:.3f}" height="11" fill="{color}"/>')
        x += part
    body = [
        text(PAD, 60, "caption", "Share of code in public repositories"),
        clip,
        '<g clip-path="url(#bar)">' + "".join(segments) + "</g>",
    ]
    for index, ((name, percent), color) in enumerate(zip(entries, LANGUAGE_COLORS)):
        y = 124 + 33 * index
        body.extend((
            f'<circle cx="{PAD + 4}" cy="{y - 4}" r="4" fill="{color}"/>',
            text(PAD + 20, y, "label", name),
            text(WIDTH - PAD, y, "value", percent),
        ))
    description = ", ".join(f"{name}: {percent}" for name, percent in entries)
    return card("Top languages", f"Share of code in public repositories. {description}.", body)


if __name__ == "__main__":
    source = Path(argv[1])
    output = Path(__file__).resolve().parents[2] / "profile"
    cards = {
        "stats.svg": activity(source / "stats.svg"),
        "top-langs.svg": languages(source / "top-langs.svg"),
    }
    for name, svg in cards.items():
        (output / name).write_text(svg, encoding="utf-8")
