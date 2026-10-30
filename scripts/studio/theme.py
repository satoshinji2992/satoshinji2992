"""Shared materials: palettes, grain, torn paper, drafting marks and plates.

Every card is a dark (or paper) plate with the same grain, hairline border,
corner registration marks and catalogue number; each one has its own palette
and its own layout on top of that.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache

from .svg import SRC, Svg, cap_height, data_uri, delay, num


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


# The header's graphite, torn grey paper and mauve.
PAGE = Palette("#100f0e", "#181615", "#2d2a28", "#ece6dd", "#958d86", "#b59ca4", "#735960", "#7d7b7a")
AUTOKEEPER = Palette("#110c0b", "#1b1311", "#37251f", "#ecdfc8", "#a89785", "#c95c4d", "#a6a268")
COMPSKILL = Palette("#e9e2d3", "#ded5c3", "#bfb5a2", "#1e1b17", "#5f584e", "#b4432f", "#2e5592")
DEEP = Palette("#141d19", "#1a2620", "#2a3a32", "#ece8dc", "#9caba1", "#e9d590", "#e8a79e", "#a3cad8")
SEIYUU = Palette("#15121b", "#1c1824", "#2f2839", "#eee8f6", "#a59db4", "#bda8e4", "#e8a8c6", "#e4c584")
LEROBOT = Palette("#0d1715", "#12201d", "#22372f", "#e2eee8", "#8fa99f", "#66bca5", "#cb8c5a")
HBALL = Palette("#0b120f", "#101c16", "#1e3228", "#ece7d2", "#98a190", "#d3ad60", "#bb763e")
NAILONG = Palette("#120c06", "#1a1209", "#3d2b12", "#ffd99e", "#a77b3e", "#f7ae42", "#dc722e")
FPGA = Palette("#110b0a", "#1a1110", "#3a2720", "#f2ded1", "#a98c7c", "#e48a5b", "#ebd3b5")
PRIZES = Palette("#161012", "#1f171a", "#36292e", "#ece3d3", "#a8999c", "#d69da9", "#c9b37f", "#e9e0cf")


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


def corner_marks(w: float, h: float, inset: float, size: float, color: str, opacity: float = 1) -> str:
    i, s = inset, size
    d = (
        f"M{i} {i + s}V{i}H{i + s}M{w - i - s} {i}H{w - i}V{i + s}"
        f"M{w - i} {h - i - s}V{h - i}H{w - i - s}M{i + s} {h - i}H{i}V{h - i - s}"
    )
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.2" opacity="{num(opacity)}"/>'


def crosshair(x: float, y: float, r: float, color: str, width: float = 1, attrs: str = "") -> str:
    return (
        f'<g stroke="{color}" stroke-width="{num(width)}" fill="none" {attrs}>'
        f'<path d="M{num(x - r)} {num(y)}H{num(x + r)}M{num(x)} {num(y - r)}V{num(y + r)}"/>'
        f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r * 0.42)}"/></g>'
    )


class Plate:
    """Card base: background, clip, grain, border, marks and catalogue number."""

    def __init__(self, svg: Svg, pal: Palette, rx: float = 18) -> None:
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

    def close(self, number: str = "", grain_opacity: float = 0.55, corner: str = "tr") -> None:
        svg, pal = self.svg, self.pal
        w, h = svg.width, svg.height
        svg.add(grain(svg, 0, 0, w, h, grain_opacity), "</g>")
        svg.add(
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{num(self.rx)}" '
            f'fill="none" stroke="{pal.line}"/>',
            corner_marks(w, h, 12, 9, pal.dim, 0.45),
        )
        if number:
            x = w - 30 if "r" in corner else 30
            y = 36 if "t" in corner else h - 26
            anchor = "end" if "r" in corner else "start"
            svg.add(svg.text(x, y, number, "mono", 12, pal.dim, anchor, tracking=2.2, attrs='opacity=".8"'))


def kicker(svg: Svg, x: float, y: float, text: str, color: str, size: float = 13, at: float = 0.1) -> str:
    return f'<g class="fade" {delay(at)}>' + svg.text(x, y, text, "mono-b", size, color, tracking=2.6) + "</g>"


def bullet_lines(
    svg: Svg,
    x: float,
    y: float,
    lines: list[str],
    color: str,
    mark: str,
    size: float = 15,
    leading: float = 27,
    at: float = 0.6,
    face: str = "mono",
) -> str:
    out = []
    for i, line in enumerate(lines):
        yy = y + i * leading
        out.append(
            f'<g class="rise" {delay(at + i * 0.12)}>'
            f'<rect x="{num(x)}" y="{num(yy - cap_height(face, size) / 2 - 3)}" width="6" height="6" '
            f'transform="rotate(45 {num(x + 3)} {num(yy - cap_height(face, size) / 2)})" fill="{mark}"/>'
            + svg.text(x + 20, yy, line, face, size, color)
            + "</g>"
        )
    return "".join(out)


def button(label: str, pal: Palette, width: int = 300, height: int = 50, icon: str = "↗") -> str:
    svg = Svg(width, height, label)
    base = height / 2 + cap_height("mono-b", 15) / 2
    svg.add(
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{pal.panel}" stroke="{pal.line}"/>',
        f'<rect x="18" y="{num(height / 2 - 8)}" width="3" height="16" rx="1.5" fill="{pal.accent}"/>',
        svg.text(34, base, label.upper(), "mono-b", 15, pal.ink, tracking=1.6),
        svg.text(width - 20, base + 1, icon, "mono-b", 17, pal.accent, "end"),
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
