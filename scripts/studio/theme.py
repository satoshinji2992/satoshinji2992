"""Shared materials: aged palettes, grain, torn paper, engraved frames and ornaments.

Every card is a plate from the same old archive: lamp-black or parchment,
speckled grain, a double engraved frame with diamond corners, a "Plate"
number in small capitals and gold-leaf ornaments. Each card then has its own
material and layout on top of that.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache

from .svg import SRC, Svg, cap_height, data_uri, delay, measure, num


@dataclass(frozen=True)
class Palette:
    bg: str
    panel: str
    line: str
    ink: str
    dim: str
    accent: str
    accent2: str
    accent3: str = ""


GOLD = "#b99b62"

# Lamp-black, umber and parchment, with the header's mauve and gold leaf.
PAGE = Palette("#0e0c0a", "#16130f", "#2d2721", "#e9dfca", "#9c9180", GOLD, "#8e6f77", "#7d7b7a")
AUTOKEEPER = Palette("#100b0a", "#1a1210", "#3a2620", "#eadcc2", "#a08f7a", "#b04a3c", "#b39660")
COMPSKILL = Palette("#e4d7bb", "#d8c8a8", "#b4a181", "#2a2017", "#6a5b47", "#983a28", "#3b4f78")
DEEP = Palette("#131a16", "#19221d", "#28342d", "#e6e1d3", "#98a59b", "#dccb8e", "#d9a199", "#9dbfcc")
SEIYUU = Palette("#110e16", "#18141f", "#2b2434", "#e8e1ee", "#9b93a8", "#a99ac8", "#d9a6b8", "#cdb27a")
LEROBOT = Palette("#0f1412", "#151c19", "#26332d", "#e2e6dc", "#8f9a8f", "#86ab9b", GOLD)
HBALL = Palette("#110f0b", "#1a1710", "#332c1d", "#ebe2c8", "#9d927a", "#c2a160", "#a8683c")
NAILONG = Palette("#100b07", "#1a130b", "#3a2a17", "#f0dcb8", "#a2875f", "#d9a052", "#b45e2e")
FPGA = Palette("#120d0b", "#1b1411", "#3a2a22", "#eedccc", "#a48b7c", "#c8754d", "#ddd0b6")
PRIZES = Palette("#150f11", "#1d1518", "#352a2e", "#ece2d0", "#a3959a", "#c58f9b", GOLD, "#e6dcc8")

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

# Candlelight: an uneven, slow breathing of a warm glow.
FLICKER = (
    "@keyframes flicker{0%,100%{opacity:.82}9%{opacity:.7}17%{opacity:.9}31%{opacity:.76}"
    "44%{opacity:1}58%{opacity:.8}71%{opacity:.93}86%{opacity:.74}}"
    ".flicker{animation:flicker 7s ease-in-out infinite}"
)


@lru_cache(maxsize=1)
def grain_uri() -> str:
    return data_uri(SRC / "grain.png")


def grain(svg: Svg, x: float, y: float, w: float, h: float, opacity: float = 0.6) -> str:
    """Speckle overlay; the tile is defined once per document."""
    pattern = getattr(svg, "_grain", None)
    if pattern is None:
        pattern = svg.uid("grain")
        svg.define(
            f'<pattern id="{pattern}" width="160" height="160" patternUnits="userSpaceOnUse">'
            f'<image href="{grain_uri()}" width="160" height="160"/></pattern>'
        )
        svg._grain = pattern  # type: ignore[attr-defined]
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="url(#{pattern})" opacity="{num(opacity)}"/>'


def torn(x0: float, x1: float, y: float, amp: float, seed: int, step: float = 7.0) -> list[tuple[float, float]]:
    """A torn edge from x0 to x1 around y: slow waves plus fibre jitter."""
    rng = random.Random(seed)
    waves = [
        (rng.uniform(0.003, 0.006), rng.uniform(0, math.tau), 0.5),
        (rng.uniform(0.012, 0.02), rng.uniform(0, math.tau), 0.3),
        (rng.uniform(0.04, 0.07), rng.uniform(0, math.tau), 0.2),
    ]
    points = []
    x = x0
    while True:
        offset = sum(a * math.sin(f * x + p) for f, p, a in waves) + rng.uniform(-0.3, 0.3)
        points.append((x, y + amp * offset))
        if x >= x1:
            return points
        x = min(x1, x + step * rng.uniform(0.5, 1.5))


def polyline(points: list[tuple[float, float]], close: bool = False) -> str:
    d = "M" + "L".join(f"{num(x, 1)} {num(y, 1)}" for x, y in points)
    return d + ("Z" if close else "")


def torn_rect(x: float, y: float, w: float, h: float, amp: float, seed: int, edges: str = "lr") -> str:
    """A paper scrap; the edges named in `edges` (l, r, t, b) are torn."""
    def edge(a0: float, a1: float, at: float, name: str, salt: int) -> list[tuple[float, float]]:
        return torn(a0, a1, at, amp if name in edges else amp * 0.12, seed + salt, step=5.0)

    top = edge(x, x + w, y, "t", 1)
    right = [(v, t) for t, v in edge(y, y + h, x + w, "r", 2)]
    bottom = edge(x, x + w, y + h, "b", 3)[::-1]
    left = [(v, t) for t, v in edge(y, y + h, x, "l", 4)][::-1]
    return polyline(top + right + bottom + left, close=True)


def crosshair(x: float, y: float, r: float, color: str, width: float = 1, attrs: str = "") -> str:
    return (
        f'<g stroke="{color}" stroke-width="{num(width)}" fill="none" {attrs}>'
        f'<path d="M{num(x - r)} {num(y)}H{num(x + r)}M{num(x)} {num(y - r)}V{num(y + r)}"/>'
        f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r * 0.42)}"/></g>'
    )


def frame(w: float, h: float, rx: float, line: str, ornament: str, inset: float = 8) -> str:
    """A double engraved border; each inner corner carries a diamond and a bracket."""
    i, arm, gap = inset, 20, 5
    diamonds, brackets = [], []
    for sx, sy, cx, cy in ((1, 1, i, i), (-1, 1, w - i, i), (-1, -1, w - i, h - i), (1, -1, i, h - i)):
        diamonds.append(
            f"M{num(cx)} {num(cy - 3.5)}L{num(cx + 3.5)} {num(cy)}L{num(cx)} {num(cy + 3.5)}L{num(cx - 3.5)} {num(cy)}Z"
        )
        bx, by = cx + sx * gap, cy + sy * gap
        brackets.append(f"M{num(bx)} {num(by + sy * arm)}V{num(by)}H{num(bx + sx * arm)}")
        brackets.append(f"M{num(bx + sx * 4)} {num(by + sy * (arm - 6))}V{num(by + sy * 4)}H{num(bx + sx * (arm - 6))}")
    return (
        f'<rect x=".5" y=".5" width="{num(w - 1)}" height="{num(h - 1)}" rx="{num(rx)}" fill="none" stroke="{line}"/>'
        f'<rect x="{num(i)}" y="{num(i)}" width="{num(w - 2 * i)}" height="{num(h - 2 * i)}" rx="{num(max(rx - i, 2))}" '
        f'fill="none" stroke="{ornament}" stroke-opacity=".26" stroke-width="1.25"/>'
        f'<path d="{"".join(brackets)}" fill="none" stroke="{ornament}" stroke-opacity=".5" stroke-width="1.25"/>'
        f'<path d="{"".join(diamonds)}" fill="{ornament}" opacity=".75"/>'
    )


class Plate:
    """Card base: background, clip, grain, engraved frame and plate number."""

    def __init__(self, svg: Svg, pal: Palette, rx: float = 16) -> None:
        self.svg = svg
        self.pal = pal
        self.rx = rx
        self.clip = svg.uid("plate")
        svg.define(
            f'<clipPath id="{self.clip}"><rect width="{svg.width}" height="{svg.height}" rx="{num(rx)}"/></clipPath>'
        )

    def open(self, fill: str | None = None) -> None:
        svg = self.svg
        svg.add(
            f'<g clip-path="url(#{self.clip})">',
            f'<rect width="{svg.width}" height="{svg.height}" fill="{fill or self.pal.bg}"/>',
        )

    def close(self, number: int = 0, grain_opacity: float = 0.6, corner: str = "tr", ornament: str = GOLD) -> None:
        svg, pal = self.svg, self.pal
        w, h = svg.width, svg.height
        svg.add(grain(svg, 0, 0, w, h, grain_opacity), "</g>", frame(w, h, self.rx, pal.line, ornament))
        if number:
            x = w - 30 if "r" in corner else 30
            y = 38 if "t" in corner else h - 24
            anchor = "end" if "r" in corner else "start"
            svg.add(svg.text(x, y, f"Plate {ROMAN[number]}", "allsc", 15, pal.dim, anchor, tracking=2.4, attrs='opacity=".85"'))


def kicker(svg: Svg, x: float, y: float, text: str, color: str, size: float = 17, at: float = 0.1, anchor: str = "start") -> str:
    return f'<g class="fade" {delay(at)}>' + svg.text(x, y, text, "allsc", size, color, anchor, tracking=2.6) + "</g>"


def ornament_rule(svg: Svg, x0: float, x1: float, y: float, color: str, glyph: str = "❦", size: float = 20, at: float = 0.5) -> str:
    """Hairlines either side of a fleuron, as between sections of an old book."""
    mid = (x0 + x1) / 2
    half = measure(glyph, "serif", size) / 2 + 8
    return (
        f'<g class="fade" {delay(at)}><path d="M{num(x0)} {num(y)}H{num(mid - half)}M{num(mid + half)} {num(y)}H{num(x1)}" '
        f'stroke="{color}" stroke-opacity=".55"/>'
        + svg.text(mid, y + size * 0.3, glyph, "serif", size, color, "middle")
        + "</g>"
    )


def bullet_lines(
    svg: Svg,
    x: float,
    y: float,
    lines: list[str],
    color: str,
    mark: str,
    size: float = 20,
    leading: float = 30,
    at: float = 0.6,
    face: str = "italic",
) -> str:
    out = []
    for i, line in enumerate(lines):
        yy = y + i * leading
        cy = yy - size * 0.3
        out.append(
            f'<g class="rise" {delay(at + i * 0.12)}>'
            f'<path d="M{num(x + 3.5)} {num(cy - 3.5)}L{num(x + 7)} {num(cy)}L{num(x + 3.5)} {num(cy + 3.5)}L{num(x)} {num(cy)}Z" fill="{mark}"/>'
            + svg.text(x + 19, yy, line, face, size, color)
            + "</g>"
        )
    return "".join(out)


def button(label: str, pal: Palette, width: int = 300, height: int = 50) -> str:
    """A museum label: chamfered corners, double rule, a manicule and small capitals."""
    svg = Svg(width, height, label)
    c, w, h = 9, width, height

    def label_path(i: float) -> str:
        return (
            f"M{num(i + c)} {num(i)}H{num(w - i - c)}L{num(w - i)} {num(i + c)}V{num(h - i - c)}"
            f"L{num(w - i - c)} {num(h - i)}H{num(i + c)}L{num(i)} {num(h - i - c)}V{num(i + c)}Z"
        )

    base = h / 2 + cap_height("allsc", 18) * 0.36
    svg.add(
        f'<path d="{label_path(0.5)}" fill="{pal.panel}" stroke="{pal.line}"/>',
        f'<path d="{label_path(5)}" fill="none" stroke="{GOLD}" stroke-opacity=".3"/>',
        svg.text(20, h / 2 + 9, "☞", "serif", 30, GOLD),
        svg.text(62, base + 3, label, "allsc", 18, pal.ink, tracking=2.2),
    )
    return svg.render()


def star(x: float, y: float, r: float, fill: str, attrs: str = "") -> str:
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r * 0.45
        points.append((x + radius * math.cos(angle), y + radius * math.sin(angle)))
    return f'<path d="{polyline(points, True)}" fill="{fill}" {attrs}/>'


def arrow(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 1.4,
          head: float = 7, attrs: str = "", dash: str = "") -> str:
    width = width * 1.4  # drawn a little heavier than specified, to read at README scale
    angle = math.atan2(y2 - y1, x2 - x1)
    left = (x2 - head * math.cos(angle - 0.42), y2 - head * math.sin(angle - 0.42))
    right = (x2 - head * math.cos(angle + 0.42), y2 - head * math.sin(angle + 0.42))
    dashed = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<g fill="none" stroke="{color}" stroke-width="{num(width)}" stroke-linecap="round" '
        f'stroke-linejoin="round" {attrs}><path d="M{num(x1)} {num(y1)}L{num(x2)} {num(y2)}"{dashed}/>'
        f'<path d="M{num(left[0])} {num(left[1])}L{num(x2)} {num(y2)}L{num(right[0])} {num(right[1])}"/></g>'
    )


def seal(cx: float, cy: float, r: float, color: str, width: float = 1) -> str:
    """A drafting compass rose: rings, degree ticks and an eight-point star."""
    width = width * 1.6
    ticks = []
    for degree in range(0, 360, 5):
        a = math.radians(degree)
        inner = r * (0.78 if degree % 30 == 0 else 0.84)
        ticks.append(
            f"M{num(cx + inner * math.cos(a))} {num(cy + inner * math.sin(a))}"
            f"L{num(cx + r * 0.9 * math.cos(a))} {num(cy + r * 0.9 * math.sin(a))}"
        )
    star_points = []
    for i in range(16):
        a = -math.pi / 2 + i * math.pi / 8
        radius = r * (0.7 if i % 4 == 0 else 0.42 if i % 2 == 0 else 0.16)
        star_points.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return (
        f'<g fill="none" stroke="{color}" stroke-width="{num(width)}">'
        f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}"/>'
        f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r * 0.9)}"/>'
        f'<path d="{"".join(ticks)}"/><path d="{polyline(star_points, True)}"/>'
        f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r * 0.06)}"/></g>'
    )


def sketch_loop(cx: float, cy: float, rx: float, ry: float, seed: int, turns: float = 1.12, tilt: float = -4) -> str:
    """A hand-drawn ring that overshoots its start, like a chalk or pencil circle."""
    rng = random.Random(seed)
    phase = rng.uniform(0, math.tau)
    start = rng.uniform(0, math.tau)
    t_cos, t_sin = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    points = []
    steps = 56
    for i in range(int(steps * turns) + 1):
        t = start + i / steps * math.tau
        wobble = 1 + 0.035 * math.sin(3 * t + phase) + rng.uniform(-0.012, 0.012) + 0.05 * i / steps
        x, y = rx * wobble * math.cos(t), ry * wobble * math.sin(t)
        points.append((cx + x * t_cos - y * t_sin, cy + x * t_sin + y * t_cos))
    return polyline(points)


def sketch_line(x1: float, y1: float, x2: float, y2: float, seed: int, amp: float = 1.4, steps: int = 9) -> str:
    rng = random.Random(seed)
    points = []
    for i in range(steps + 1):
        t = i / steps
        bend = math.sin(t * math.pi) * amp * 0.8
        points.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t + bend + rng.uniform(-amp, amp) * 0.35))
    return polyline(points)
