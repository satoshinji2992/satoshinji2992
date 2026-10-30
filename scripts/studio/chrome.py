"""Page furniture: the header, navigation tabs, section labels and the footer."""

from __future__ import annotations

import json
import math
import random

from .data import long_date
from .svg import SRC, Svg, cap_height, data_uri, delay, measure, num
from .theme import GOLD, PAGE, crosshair, frame, grain, polyline, torn_rect

TAGLINE = ["Agents", "·", "Reinforcement", "learning", "·", "Robotics"]


def header(data: dict) -> str:
    w, h = 1600, 560
    svg = Svg(w, h, "Agents, reinforcement learning, robotics")
    svg.add(f'<image href="{data_uri(SRC / "header-clean.webp")}" width="{w}" height="{h}"/>')

    # A slow light passing over the torn paper strip, clipped to its traced outline.
    strip, sheen = svg.uid("strip"), svg.uid("sheen")
    outline = json.loads((SRC / "header-strip.json").read_text())
    edge = [(x, max(y, 184)) for x, y in outline["top"] if x <= 960]
    bottom = outline["bottom"]
    svg.define(
        f'<clipPath id="{strip}"><path d="{polyline(edge + [(960, bottom), (0, bottom)], close=True)}"/></clipPath>',
        f'<linearGradient id="{sheen}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
    )
    svg.style(
        "@keyframes sweep{0%{transform:translateX(-320px)}38%,100%{transform:translateX(1100px)}}",
        ".sweep{animation:sweep 11s cubic-bezier(.5,0,.4,1) 1.2s infinite both;mix-blend-mode:overlay}",
    )
    svg.add(f'<g clip-path="url(#{strip})"><rect class="sweep" x="0" y="170" width="300" height="90" fill="url(#{sheen})"/></g>')

    # Drafting marks over the dark field: a ruler, compass arcs and crosshairs.
    ticks = "".join(f"M{x} 318v{9 if (x - 76) % 80 == 0 else 4}" for x in range(76, 541, 16))
    svg.add(
        f'<g fill="none" stroke="#4a4847" stroke-width="1.1">'
        f'<path class="draw" {delay(0.2)} pathLength="1" d="M76 318H540"/>'
        f'<path class="fade" {delay(0.9)} d="{ticks}"/></g>',
        f'<g fill="none" stroke="#3d3b3a" stroke-width="1.2">'
        f'<path class="draw" style="animation-delay:.4s;animation-duration:3.2s" pathLength="1" d="{arc(210, 640, 250, 205, 318)}"/>'
        f'<path class="draw" style="animation-delay:.7s;animation-duration:3.2s" pathLength="1" d="{arc(210, 640, 196, 210, 300)}"/></g>',
        crosshair(612, 116, 9, "#5b5856", 1, 'class="breathe" style="animation-delay:.5s"'),
        crosshair(936, 300, 9, "#5b5856", 1, 'class="breathe" style="animation-delay:2.2s"'),
        crosshair(52, 488, 9, "#5b5856", 1, 'class="breathe" style="animation-delay:1.4s"'),
    )

    # The tagline, word by word, then a caret.
    size, x, y = 45, 74, 392
    space = measure(" ", "serif-m", size)
    for i, word in enumerate(TAGLINE):
        svg.add(f'<g class="rise" {delay(0.35 + i * 0.13)}>' + svg.text(x, y, word, "serif-m", size, "#a99a9f") + "</g>")
        x += measure(word, "serif-m", size) + space
    svg.style("@keyframes caret{0%,49%{opacity:.9}50%,100%{opacity:0}}", ".caret{animation:caret 1.1s steps(1) infinite}")
    svg.add(
        f'<g class="fade" style="animation-delay:1.2s;animation-duration:.01s">'
        f'<rect class="caret" x="{num(x + 2)}" y="{num(y - cap_height("serif-m", size) - 4)}" width="2" '
        f'height="{num(cap_height("serif-m", size) + 10)}" fill="#a99a9f"/></g>'
    )

    # Dust drifting through the light.
    rng = random.Random(7)
    drifts = []
    for k in range(4):
        dx, dy = rng.uniform(30, 90) * (1 if k % 2 else -1), -rng.uniform(80, 160)
        drifts.append(
            f"@keyframes mote{k}{{0%{{transform:translate(0,0);opacity:0}}15%{{opacity:var(--o)}}"
            f"85%{{opacity:var(--o)}}100%{{transform:translate({num(dx)}px,{num(dy)}px);opacity:0}}}}"
        )
    svg.style(*drifts)
    motes = []
    for k in range(30):
        mx, my = rng.uniform(20, 980), rng.uniform(40, 540)
        duration = rng.uniform(14, 26)
        motes.append(
            f'<circle cx="{num(mx)}" cy="{num(my)}" r="{num(rng.uniform(0.7, 1.9))}" fill="#e9e1e3" opacity="0" '
            f'style="--o:{num(rng.uniform(0.18, 0.5))};animation:mote{k % 4} {num(duration)}s linear -{num(rng.uniform(0, duration))}s infinite"/>'
        )
    svg.add(*motes)
    return svg.render()


def arc(cx: float, cy: float, r: float, start: float, end: float) -> str:
    a0, a1 = math.radians(start), math.radians(end)
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    large = 1 if (end - start) % 360 > 180 else 0
    return f"M{num(x0)} {num(y0)}A{num(r)} {num(r)} 0 {large} 1 {num(x1)} {num(y1)}"


NAV = [
    ("I", "Featured", "featured"),
    ("II", "Projects", "projects"),
    ("III", "Almanac", "almanac"),
    ("IV", "Instruments", "instruments"),
]


def nav(index: int) -> str:
    numeral, label, _ = NAV[index]
    pal = PAGE
    w, h = 400, 84
    svg = Svg(w, h, f"{numeral}. {label}")
    svg.style(
        "@keyframes bob{0%,100%{transform:translateX(0)}50%{transform:translateX(5px)}}",
        f".bob{{animation:bob 1.8s ease-in-out {num(1 + index * 0.15)}s 3 both}}",
    )
    numeral_w = measure(numeral, "italic", 40)
    hand_x, hand_y = w - 34, 40
    svg.add(
        f'<rect width="{w}" height="{h}" rx="10" fill="{pal.bg}"/>',
        grain(svg, 0, 0, w, h, 0.5),
        frame(w, h, 10, pal.line, GOLD, 6),
        f'<g class="fade" {delay(index * 0.1)}>' + svg.text(26, 55, numeral, "italic", 40, GOLD) + "</g>",
        f'<g class="fade" {delay(0.1 + index * 0.1)}>' + svg.text(26 + numeral_w + 14, 53, label, "allsc", 24, pal.ink, tracking=2.2) + "</g>",
        f'<g class="bob">' + svg.text(hand_x, hand_y + 10, "☞", "serif", 32, GOLD, "middle", attrs='opacity=".8"') + "</g>",
    )
    return svg.render()


def section(index: int, meta: str) -> str:
    numeral, title, _ = NAV[index]
    pal = PAGE
    w, h = 1200, 112
    svg = Svg(w, h, f"{numeral}. {title}")
    numeral_w = measure(numeral, "italic", 32)
    title_w = measure(title, "serif", 42)
    scrap_w = 48 + numeral_w + 16 + title_w
    scrap = torn_rect(24, 26, scrap_w, 60, 3.2, seed=40 + index, edges="lr")
    paper, clip = svg.uid("paper"), svg.uid("scrap")
    svg.define(
        f'<linearGradient id="{paper}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a3a09d"/>'
        '<stop offset="1" stop-color="#85817c"/></linearGradient>',
        f'<clipPath id="{clip}"><path d="{scrap}"/></clipPath>',
    )
    line_x = 24 + scrap_w + 30
    meta_w = measure(meta, "italic", 22)
    end_x = w - 44 - meta_w - 26
    svg.add(
        f'<rect width="{w}" height="{h}" rx="12" fill="{pal.bg}"/>',
        grain(svg, 0, 0, w, h, 0.5),
        frame(w, h, 12, pal.line, GOLD, 7),
        f'<g class="fade" {delay(0.05)}><path d="{scrap}" transform="translate(3 4)" fill="#000" opacity=".45"/>'
        f'<path d="{scrap}" fill="url(#{paper})"/><g clip-path="url(#{clip})">{grain(svg, 0, 0, w, h, 0.9)}</g>'
        + svg.text(48, 69, numeral, "italic", 32, "#2a2626")
        + svg.text(48 + numeral_w + 16, 70, title, "serif", 42, "#171414")
        + "</g>",
        f'<path class="draw" {delay(0.25)} pathLength="1" d="M{num(line_x)} 57H{num(end_x)}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="1.3" fill="none"/>',
        f'<g class="fade" {delay(0.9)}>' + svg.text((line_x + end_x) / 2, 64, "❦", "serif", 22, GOLD, "middle") + "</g>",
        f'<g class="fade" {delay(0.6)}>' + svg.text(w - 44, 64, meta, "italic", 22, pal.dim, "end") + "</g>",
    )
    return svg.render()


def footer(data: dict) -> str:
    pal = PAGE
    w, h = 1200, 156
    svg = Svg(w, h, "Refreshed daily by GitHub Actions")
    strip = torn_rect(-10, 38, w + 20, 54, 5, seed=12, edges="tb")
    paper, clip = svg.uid("paper"), svg.uid("strip")
    svg.define(
        f'<linearGradient id="{paper}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#76736f"/>'
        '<stop offset=".55" stop-color="#9a9691"/><stop offset="1" stop-color="#726f6b"/></linearGradient>',
        f'<clipPath id="{clip}"><path d="{strip}"/></clipPath>',
    )
    refreshed = long_date(data["refreshed"] + "T00:00:00Z")
    svg.add(
        f'<rect width="{w}" height="{h}" rx="12" fill="{pal.bg}"/>',
        f'<path d="{strip}" transform="translate(0 4)" fill="#000" opacity=".5"/>',
        f'<path d="{strip}" fill="url(#{paper})"/>',
        f'<g clip-path="url(#{clip})">{grain(svg, 0, 0, w, h, 0.9)}</g>',
        svg.text(44, 73, f"satoshinji2992 · refreshed {refreshed} by GitHub Actions", "allsc", 18, "#1b1919", tracking=2.2),
        svg.text(w - 44, 73, "Back to top ↑", "allsc", 18, "#1b1919", "end", tracking=2.2),
        svg.text(w / 2, 132, "Set in Cormorant Garamond; drawn by a standard-library Python script.", "italic", 20, pal.dim, "middle"),
        frame(w, h, 12, pal.line, GOLD, 7),
    )
    return svg.render()
