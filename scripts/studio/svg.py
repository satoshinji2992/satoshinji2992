"""SVG documents whose text is set from pre-extracted glyph outlines.

prepare_assets.py stores the outlines, advances and kerning of five faces in
assets/src/glyphs.json.gz. A document defines only the glyphs it uses and
places them with <use>, so cards need no web fonts and every line can be
measured before it is placed.
"""

from __future__ import annotations

import base64
import gzip
import html
import json
from functools import lru_cache
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "src"

# Short tags keep glyph ids small: "s41" is "A" in the serif face, "s66_69" its fi ligature.
FACE_TAGS = {"serif": "s", "serif-m": "m", "italic": "i", "sc": "c", "allsc": "a", "mono": "o", "mono-b": "b"}

BASE_CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(14px)}}"
    "@keyframes fade{from{opacity:0}}"
    "@keyframes draw{from{stroke-dasharray:1 1;stroke-dashoffset:1}"
    "to{stroke-dasharray:1 1;stroke-dashoffset:0}}"
    "@keyframes grow{from{transform:scaleX(0)}}"
    "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
    "@keyframes breathe{0%,100%{opacity:.3}50%{opacity:1}}"
    "@keyframes spin{to{transform:rotate(360deg)}}"
    ".rise{animation:rise 1s cubic-bezier(.2,.7,.2,1) both}"
    ".fade{animation:fade 1.2s ease both}"
    ".draw{animation:draw 2s cubic-bezier(.65,0,.3,1) both}"
    ".grow{animation:grow 1.4s cubic-bezier(.65,0,.3,1) both;transform-box:fill-box;transform-origin:0 50%}"
    ".blink{animation:blink 1.1s steps(1) infinite}"
    ".breathe{animation:breathe 4s ease-in-out infinite}"
    ".spin{animation:spin 90s linear infinite;transform-box:fill-box;transform-origin:center}"
)
REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def num(value: float, digits: int = 2) -> str:
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def delay(seconds: float, duration: float | None = None) -> str:
    style = f"animation-delay:{num(seconds)}s"
    if duration is not None:
        style += f";animation-duration:{num(duration)}s"
    return f'style="{style}"'


def data_uri(path: Path) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}[path.suffix]
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


class Face:
    def __init__(self, key: str, data: dict) -> None:
        self.key = key
        self.tag = FACE_TAGS[key]
        self.upm = data["upm"]
        self.cap = data["cap"]
        self.glyphs: dict[str, tuple[int, str]] = {
            char: (advance, path) for char, (advance, path) in data["glyphs"].items()
        }
        # Ligatures share the table, keyed by their character sequence.
        self.ligatures = sorted(data.get("ligatures", {}), key=len, reverse=True)
        self.glyphs.update({seq: (advance, path) for seq, (advance, path) in data.get("ligatures", {}).items()})
        self.kern: dict[str, int] = data["kern"]

    def glyph_id(self, key: str) -> str:
        return self.tag + "_".join(f"{ord(char):x}" for char in key)

    def layout(self, text: str, tracking: float = 0.0) -> tuple[list[tuple[str, float]], float]:
        """Place each glyph; returns (key, x) in font units and the advance.

        Ligatures apply only to untracked text, as in print."""
        placed: list[tuple[str, float]] = []
        pen = 0.0
        previous = ""
        i = 0
        while i < len(text):
            key = next((seq for seq in self.ligatures if not tracking and text.startswith(seq, i)), text[i])
            if key not in self.glyphs:
                key = "?"
            if previous:
                pen += self.kern.get(previous[-1] + key[0], 0) + tracking
            placed.append((key, pen))
            pen += self.glyphs[key][0]
            previous = key
            i += max(1, len(key) if key != "?" else 1)
        return placed, pen


@lru_cache(maxsize=1)
def faces() -> dict[str, Face]:
    with gzip.open(SRC / "glyphs.json.gz", "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    return {key: Face(key, value) for key, value in data.items()}


def measure(text: str, face: str = "mono", size: float = 16, tracking: float = 0) -> float:
    font = faces()[face]
    scale = size / font.upm
    return font.layout(text, tracking / scale)[1] * scale


def cap_height(face: str, size: float) -> float:
    font = faces()[face]
    return font.cap * size / font.upm


def wrap(text: str, face: str, size: float, width: float, tracking: float = 0) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}" if line else word
        if line and measure(trial, face, size, tracking) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def fit(text: str, face: str, size: float, width: float, tracking: float = 0) -> float:
    """Largest size not above `size` at which the text fits `width`."""
    actual = measure(text, face, size, tracking)
    return size if actual <= width else size * width / actual


class Svg:
    def __init__(self, width: int, height: int, label: str) -> None:
        self.width = width
        self.height = height
        self.label = label
        self.defs: list[str] = []
        self.css: list[str] = []
        self.body: list[str] = []
        self.used: dict[str, set[str]] = {}
        self._count = 0

    def uid(self, prefix: str) -> str:
        self._count += 1
        return f"{prefix}-{self._count}"

    def add(self, *parts: str) -> None:
        self.body.extend(part for part in parts if part)

    def define(self, *parts: str) -> None:
        self.defs.extend(parts)

    def style(self, *rules: str) -> None:
        self.css.extend(rules)

    def text(
        self,
        x: float,
        y: float,
        text: str,
        face: str = "mono",
        size: float = 16,
        fill: str = "#fff",
        anchor: str = "start",
        tracking: float = 0,
        attrs: str = "",
        glyph_attrs: Callable[[int, str], str] | None = None,
    ) -> str:
        """A run of text with its baseline at y; anchor is start, middle or end."""
        font = faces()[face]
        scale = size / font.upm
        placed, advance = font.layout(text, tracking / scale)
        if anchor == "middle":
            x -= advance * scale / 2
        elif anchor == "end":
            x -= advance * scale
        used = self.used.setdefault(face, set())
        uses = []
        for index, (key, pen) in enumerate(placed):
            if not font.glyphs[key][1]:
                continue
            used.add(key)
            extra = f" {glyph_attrs(index, key)}" if glyph_attrs else ""
            uses.append(f'<use href="#{font.glyph_id(key)}" x="{num(pen, 1)}"{extra}/>')
        extra = f" {attrs}" if attrs else ""
        return (
            f'<g transform="translate({num(x)} {num(y)}) scale({num(scale, 5)})" '
            f'fill="{fill}"{extra}>{"".join(uses)}</g>'
        )

    def lines(
        self,
        x: float,
        y: float,
        lines: list[str],
        leading: float,
        **kwargs,
    ) -> str:
        return "".join(self.text(x, y + i * leading, line, **kwargs) for i, line in enumerate(lines))

    def render(self) -> str:
        glyph_defs = []
        for face in sorted(self.used):
            font = faces()[face]
            for key in sorted(self.used[face]):
                glyph_defs.append(f'<path id="{font.glyph_id(key)}" d="{font.glyphs[key][1]}"/>')
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title">'
            f"<title id=\"title\">{esc(self.label)}</title>"
            f'<defs>{"".join(glyph_defs)}{"".join(self.defs)}</defs>'
            f"<style>{BASE_CSS}{''.join(self.css)}{REDUCED_MOTION}</style>"
            f'{"".join(self.body)}</svg>\n'
        )
