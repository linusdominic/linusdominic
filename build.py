"""Build the profile page: SVG visuals for light and dark themes, and README.md.

    python build.py            rebuild from profile.toml and the saved CI states
    python build.py --live     first ask GitHub for each project's CI state (needs GH_TOKEN)

Standard library only. Every image on the page is a file in this repository, so nothing
depends on a third-party badge or stats service.
"""

import json
import os
import sys
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
STATUS = ROOT / "status.json"

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO_ADVANCE = 0.602  # width of one monospace character, in ems

THEMES = {
    "dark": {
        "card": "#0d1117", "raised": "#161b22", "border": "#30363d", "text": "#e6edf3",
        "soft": "#c9d1d9", "muted": "#8b949e", "accent": "#58a6ff", "accent2": "#bc8cff",
        "good": "#3fb950", "bad": "#f85149", "chip": "#21262d",
    },
    "light": {
        "card": "#ffffff", "raised": "#f6f8fa", "border": "#d0d7de", "text": "#1f2328",
        "soft": "#424a53", "muted": "#656d76", "accent": "#0969da", "accent2": "#8250df",
        "good": "#1a7f37", "bad": "#cf222e", "chip": "#eaeef2",
    },
}  # fmt: skip

REPO_ICON = (
    "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 "
    "0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 "
    "11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 "
    ".25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 "
    "0L5.4 15.7a.25.25 0 0 1-.4-.2Z"
)  # GitHub's Octicons repo icon, MIT licensed

# Text is visible by default and hidden only while its animation is waiting to start, so a
# viewer that does not run animations still shows everything.
ANIMATION = """
.k,.o{animation:in .01s linear backwards}
.o{animation-duration:.4s}
@keyframes in{from{fill-opacity:0}}
.cur{animation:blink 1.1s steps(1) infinite}
@keyframes blink{50%{fill-opacity:0}}
@media (prefers-reduced-motion:reduce){.k,.o,.cur{animation:none}}
"""


def svg(width: int, height: int, label: str, body: str, style: str = "") -> str:
    css = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">'
        f"<title>{escape(label)}</title>{css}{body}</svg>\n"
    )


def text(x: float, y: float, content: str, *, size: float, fill: str, font: str = SANS, **attrs) -> str:
    names = {"class_": "class", "xml_space": "xml:space"}
    extra = "".join(
        f' {names.get(key, key.replace("_", "-"))}="{value}"' for key, value in attrs.items()
    )
    return (
        f'<text x="{x:g}" y="{y:g}" font-family="{font}" font-size="{size:g}" '
        f'fill="{fill}"{extra}>{content}</text>'
    )


def chips(items: list[str], x: float, y: float, c: dict) -> tuple[str, float]:
    """A row of rounded labels starting at x. Returns the markup and where the row ends."""
    out = []
    for item in items:
        width = len(item) * 11 * MONO_ADVANCE + 20
        out.append(
            f'<rect x="{x:g}" y="{y:g}" width="{width:.1f}" height="22" rx="11" fill="{c["chip"]}" '
            f'stroke="{c["border"]}"/>'
            + text(x + 10, y + 15, escape(item), size=11, fill=c["soft"], font=MONO)
        )
        x += width + 6
    return "".join(out), x


def typed(command: str, x: float, y: float, start: float, c: dict) -> tuple[str, float]:
    """A shell command that appears one character at a time. Returns markup and its end time."""
    step = 0.05
    letters = "".join(
        f'<tspan class="k" style="animation-delay:{start + i * step:.2f}s">{escape(ch)}</tspan>'
        for i, ch in enumerate(command)
    )
    prompt = f'<tspan fill="{c["good"]}">$ </tspan>'
    line = text(x, y, prompt + letters, size=14, fill=c["text"], font=MONO, xml_space="preserve")
    return line, start + len(command) * step


def hero(profile: dict, c: dict) -> str:
    width, pad = 840, 40
    first, second, third = profile["wordmark"]
    repos = [project["repo"] for project in profile["projects"]]
    columns = 3
    rows = -(-len(repos) // columns)
    height = 337 + rows * 21  # the listing grows a line for every three projects
    out = [
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="{c["card"]}" stroke="{c["border"]}"/>',
        f'<path d="M0.5 44.5h{width - 1}" stroke="{c["border"]}"/>',
        '<circle cx="24" cy="22" r="6" fill="#ff5f57"/><circle cx="44" cy="22" r="6" fill="#febc2e"/>'
        '<circle cx="64" cy="22" r="6" fill="#28c840"/>',
        text(width / 2, 27, f"{first} — agents — zsh", size=12, fill=c["muted"], font=MONO, text_anchor="middle"),
    ]

    # The name, written like a path: linus.dominic/nathaniel
    size = 40
    mark = (
        f"{first}<tspan fill='{c['accent']}'>.</tspan>{second}"
        f"<tspan fill='{c['muted']}'>/</tspan><tspan fill='{c['accent2']}'>{third}</tspan>"
    )
    out.append(text(pad, 108, mark, size=size, fill=c["text"], font=MONO, font_weight=700))
    letters = len(first) + len(second) + len(third) + 2
    out.append(
        f'<rect class="cur" x="{pad + letters * size * MONO_ADVANCE + 8:.1f}" y="76" width="20" '
        f'height="38" rx="2" fill="{c["accent"]}"/>'
    )
    for i, line in enumerate(profile["tagline"]):
        out.append(text(pad, 150 + i * 25, escape(line), size=17, fill=c["soft"]))

    # A short terminal session that types itself out.
    y = 228
    line, done = typed("cat RULE", pad, y, 0.6, c)
    out.append(line)
    out.append(
        text(pad, y + 24, escape(profile["rule"]), size=14, fill=c["text"], font=MONO,
             class_="o", style=f"animation-delay:{done + 0.25:.2f}s")
    )  # fmt: skip
    y += 58
    line, done = typed("ls projects/", pad, y, done + 1.0, c)
    out.append(line)
    for index, repo in enumerate(repos):
        row, column = divmod(index, columns)
        out.append(
            text(pad + column * 256, y + 24 + row * 21, f"{escape(repo)}/", size=13.5, fill=c["accent"],
                 font=MONO, class_="o", style=f"animation-delay:{done + 0.25 + row * 0.12:.2f}s")
        )  # fmt: skip
    y += 24 + rows * 21 + 12
    end = done + 0.25 + rows * 0.12 + 0.5
    out.append(
        f'<g class="o" style="animation-delay:{end:.2f}s">'
        + text(pad, y, "$", size=14, fill=c["good"], font=MONO)
        + f'<rect class="cur" x="{pad + 17}" y="{y - 12}" width="9" height="16" fill="{c["text"]}"/></g>'
    )
    label = f"{profile['name']}. {' '.join(profile['tagline'])} {profile['rule']}"
    return svg(width, height, label, "".join(out), ANIMATION)


def card(project: dict, ci: str | None, c: dict) -> str:
    width, height, pad = 410, 208, 20
    out = [
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{c["card"]}" stroke="{c["border"]}"/>',
        f'<path transform="translate({pad} 20)" d="{REPO_ICON}" fill="{c["muted"]}"/>',
        text(pad + 24, 33, escape(project["repo"]), size=15, fill=c["accent"], font=MONO, font_weight=700),
    ]
    if ci in ("success", "failure"):
        colour, word = (c["good"], "CI passing") if ci == "success" else (c["bad"], "CI failing")
        dot = width - pad - len(word) * 11 * MONO_ADVANCE - 10
        out.append(f'<circle cx="{dot:.1f}" cy="28.5" r="4" fill="{colour}"/>')
        out.append(text(width - pad, 32.5, word, size=11, fill=c["muted"], font=MONO, text_anchor="end"))
    for i, line in enumerate(project["what"]):
        out.append(text(pad, 62 + i * 18, escape(line), size=13, fill=c["soft"]))
    out.append(text(pad, 124, escape(project["metric"]), size=25, fill=c["text"], font_weight=700))
    out.append(text(pad, 144, escape(project["label"]), size=12.5, fill=c["muted"]))
    out.append(text(pad, 163, escape(project["caveat"]), size=11.5, fill=c["muted"], font_style="italic"))
    out.append(chips(project["stack"], pad, 174, c)[0])
    label = (
        f"{project['repo']}: {' '.join(project['what'])} {project['metric']}: "
        f"{project['label']}. {project['caveat']}"
    )
    return svg(width, height, label, "".join(out))


def principles(profile: dict, c: dict) -> str:
    width, gap, height = 840, 18, 132
    each = (width - 2 * gap) / 3
    out = []
    for index, item in enumerate(profile["principles"]):
        x = index * (each + gap)
        out.append(
            f'<rect x="{x + 0.5:g}" y="0.5" width="{each - 1:g}" height="{height - 1}" rx="12" '
            f'fill="{c["card"]}" stroke="{c["border"]}"/>'
        )
        out.append(text(x + 20, 30, f"0{index + 1}", size=12, fill=c["accent"], font=MONO, font_weight=700))
        out.append(text(x + 46, 30.5, escape(item["title"]), size=15, fill=c["text"], font_weight=700))
        for i, line in enumerate(item["text"]):
            out.append(text(x + 20, 58 + i * 19, escape(line), size=12.5, fill=c["muted"]))
    label = "How I work. " + " ".join(f"{p['title']}: {' '.join(p['text'])}" for p in profile["principles"])
    return svg(width, height, label, "".join(out))


def stack(profile: dict, c: dict) -> str:
    width, row = 840, 36
    height = len(profile["stack"]) * row + 24
    out = [
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{c["card"]}" stroke="{c["border"]}"/>'
    ]
    for index, group in enumerate(profile["stack"]):
        y = 14 + index * row
        out.append(
            text(24, y + 21, escape(group["group"].upper()), size=11, fill=c["muted"], font=MONO,
                 letter_spacing="0.06em")
        )  # fmt: skip
        out.append(chips(group["items"], 170, y + 6, c)[0])
    label = "What I work with. " + ". ".join(
        f"{group['group']}: {', '.join(group['items'])}" for group in profile["stack"]
    )
    return svg(width, height, label, "".join(out))


def picture(name: str, alt: str, width: str) -> str:
    return (
        "<picture>"
        f'<source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
        f'<img src="assets/{name}-light.svg" alt="{escape(alt)}" width="{width}">'
        "</picture>"
    )


def readme(profile: dict) -> str:
    owner = profile["owner"]
    links = " &nbsp;·&nbsp; ".join(
        f'<a href="{link["url"]}"><b>{escape(link["label"])}</b></a>' for link in profile["links"]
    )
    intro = f"{profile['name']}. {' '.join(profile['tagline'])}"
    parts = [
        "<!-- Generated by build.py from profile.toml and details.md. Edit those three files, not this one. -->",
        f'<p align="center">{picture("hero", intro, "100%")}</p>',
        f'<p align="center">{links}</p>',
    ]
    sections: dict[str, list[dict]] = {}
    for project in profile["projects"]:
        sections.setdefault(project["section"], []).append(project)
    for title, projects in sections.items():
        cards = "\n".join(
            f'<a href="https://github.com/{owner}/{p["repo"]}">'
            + picture(f"card-{p['repo']}", f"{p['repo']}: {' '.join(p['what'])} {p['metric']}: {p['label']}. {p['caveat']}", "49%")
            + "</a>"
            for p in projects
        )
        parts += [f"### {title}", f'<p align="center">\n{cards}\n</p>']
    parts += [
        "### How I work",
        f'<p align="center">{picture("principles", "Run it. Measure it. Say what was not verified.", "100%")}</p>',
        "### What I work with",
        f'<p align="center">{picture("stack", "Languages, warehouses, pipelines, infrastructure and AI tools", "100%")}</p>',
        "<details>\n<summary><b>All of this as plain text</b>, with each project's full caveats</summary>\n",
        (ROOT / "details.md").read_text().strip(),
        "\n</details>",
        '<p align="center"><sub>This page is built from <a href="profile.toml">profile.toml</a> by '
        '<a href="build.py">build.py</a> and rebuilt daily by a '
        '<a href=".github/workflows/build.yml">GitHub Action</a>, so the CI lights are current. '
        "Every image is a file in this repository.</sub></p>",
    ]
    return "\n\n".join(parts) + "\n"


def fetch_status(profile: dict) -> dict[str, str]:
    """Each project's latest finished CI run on main: success, failure, or absent."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("--live needs GH_TOKEN or GITHUB_TOKEN")
    states = {}
    for project in profile["projects"]:
        url = (
            f"https://api.github.com/repos/{profile['owner']}/{project['repo']}"
            "/actions/runs?branch=main&status=completed&per_page=1"
        )
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            runs = json.load(response)["workflow_runs"]
        if runs:
            states[project["repo"]] = runs[0]["conclusion"]
    return states


def build(live: bool = False) -> list[Path]:
    profile = tomllib.loads((ROOT / "profile.toml").read_text())
    if live:
        STATUS.write_text(json.dumps(fetch_status(profile), indent=2, sort_keys=True) + "\n")
    states = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    ASSETS.mkdir(exist_ok=True)
    written = []
    for theme, colours in THEMES.items():
        images = {
            "hero": hero(profile, colours),
            "principles": principles(profile, colours),
            "stack": stack(profile, colours),
        }
        for project in profile["projects"]:
            images[f"card-{project['repo']}"] = card(project, states.get(project["repo"]), colours)
        for name, content in images.items():
            ET.fromstring(content)  # fail here, not on the page, if the markup is broken
            path = ASSETS / f"{name}-{theme}.svg"
            path.write_text(content)
            written.append(path)
    (ROOT / "README.md").write_text(readme(profile))
    return written


if __name__ == "__main__":
    files = build(live="--live" in sys.argv)
    print(f"{len(files)} images and README.md written.")
