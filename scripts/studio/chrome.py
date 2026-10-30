"""Page furniture: the header, navigation tabs, section labels and the footer."""

from __future__ import annotations

import json
import math
import random

from .data import short_date
from .svg import SRC, Svg, cap_height, data_uri, delay, measure, num
from .theme import PAGE, crosshair, grain, polyline, torn_rect

TAGLINE = ["Agents", "·", "Reinforcement", "learning", "·", "Robotics"]


def header(data: dict) -> str:
    w, h = 1600, 560
    svg = Svg(w, h, "Qi Shen: agents, reinforcement learning, robotics")
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

    # The tagline, word by word, then a caret and a small plate label.
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
    svg.add(f'<g class="fade" {delay(1.3)}>' + svg.text(76, 448, "QI SHEN  ·  BUPT  ·  BEIJING", "mono-b", 17, "#776e71", tracking=5) + "</g>")

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
    ("III", "Pulse", "pulse"),
    ("IV", "Toolkit", "toolkit"),
]


def nav(index: int) -> str:
    numeral, label, _ = NAV[index]
    pal = PAGE
    w, h = 400, 80
    svg = Svg(w, h, f"{numeral}. {label}")
    svg.style(
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(4px)}}",
        f".bob{{animation:bob 1.6s ease-in-out {num(1 + index * 0.15)}s 3 both}}",
    )
    numeral_w = measure(numeral, "italic", 38)
    svg.add(
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{pal.bg}" stroke="{pal.line}"/>',
        grain(svg, 0, 0, w, h, 0.4),
        f'<g class="fade" {delay(index * 0.1)}>' + svg.text(24, 50, numeral, "italic", 38, pal.accent) + "</g>",
        f'<g class="fade" {delay(0.1 + index * 0.1)}>'
        + svg.text(24 + numeral_w + 16, 48, label.upper(), "mono-b", 21, pal.ink, tracking=2.6)
        + "</g>",
        f'<g class="bob">' + svg.text(w - 24, 49, "↓", "mono-b", 22, pal.dim, "end") + "</g>",
        f'<rect x="24" y="63" width="{w - 48}" height="1" fill="{pal.line}"/>',
        f'<rect class="grow" {delay(0.3 + index * 0.12)} x="24" y="62" width="56" height="2.5" fill="{pal.accent}"/>',
    )
    return svg.render()


def section(index: int, meta: str) -> str:
    numeral, title, _ = NAV[index]
    pal = PAGE
    w, h = 1200, 112
    svg = Svg(w, h, f"{numeral}. {title}")
    numeral_w = measure(numeral, "italic", 30)
    title_w = measure(title, "serif", 40)
    scrap_w = 48 + numeral_w + 16 + title_w
    scrap = torn_rect(22, 26, scrap_w, 60, 3.2, seed=40 + index, edges="lr")
    paper = svg.uid("paper")
    svg.define(
        f'<linearGradient id="{paper}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9b9998"/>'
        '<stop offset="1" stop-color="#7f7d7c"/></linearGradient>'
    )
    clip = svg.uid("scrap")
    svg.define(f'<clipPath id="{clip}"><path d="{scrap}"/></clipPath>')
    line_x = 22 + scrap_w + 28
    meta_w = measure(meta, "mono-b", 12, 2.4)
    ticks = "".join(f"M{num(x)} 56v5" for x in range(int(line_x) + 40, int(w - 40 - meta_w - 30), 40))
    svg.add(
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{pal.bg}" stroke="{pal.line}"/>',
        grain(svg, 0, 0, w, h, 0.4),
        f'<g class="fade" {delay(0.05)}><path d="{scrap}" transform="translate(3 4)" fill="#000" opacity=".45"/>'
        f'<path d="{scrap}" fill="url(#{paper})"/><g clip-path="url(#{clip})">{grain(svg, 0, 0, w, h, 0.9)}</g>'
        + svg.text(46, 68, numeral, "italic", 30, "#2a2626")
        + svg.text(46 + numeral_w + 16, 69, title, "serif", 40, "#171414")
        + "</g>",
        f'<path class="draw" {delay(0.25)} pathLength="1" d="M{num(line_x)} 56H{num(w - 40 - meta_w - 24)}" stroke="{pal.line}" stroke-width="1.2" fill="none"/>',
        f'<path class="fade" {delay(0.9)} d="{ticks}" stroke="{pal.line}" stroke-width="1.2"/>',
        f'<g class="fade" {delay(0.6)}>' + svg.text(w - 40, 60, meta, "mono-b", 12, pal.dim, "end", tracking=2.4) + "</g>",
    )
    return svg.render()


def footer(data: dict) -> str:
    pal = PAGE
    w, h = 1200, 150
    svg = Svg(w, h, "Refreshed daily by GitHub Actions")
    strip = torn_rect(-10, 40, w + 20, 50, 5, seed=12, edges="tb")
    paper, clip = svg.uid("paper"), svg.uid("strip")
    svg.define(
        f'<linearGradient id="{paper}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6d6b6a"/>'
        '<stop offset=".55" stop-color="#8d8b8a"/><stop offset="1" stop-color="#6a6867"/></linearGradient>',
        f'<clipPath id="{clip}"><path d="{strip}"/></clipPath>',
    )
    refreshed = short_date(data["refreshed"] + "T00:00:00Z").upper()
    svg.add(
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{pal.bg}" stroke="{pal.line}"/>',
        f'<path d="{strip}" transform="translate(0 4)" fill="#000" opacity=".5"/>',
        f'<path d="{strip}" fill="url(#{paper})"/>',
        f'<g clip-path="url(#{clip})">{grain(svg, 0, 0, w, h, 0.9)}</g>',
        svg.text(40, 71, f"SATOSHINJI2992  ·  REFRESHED {refreshed} BY GITHUB ACTIONS", "mono-b", 13, "#1b1919", tracking=2.6),
        svg.text(w - 40, 71, "↑  BACK TO TOP", "mono-b", 13, "#1b1919", "end", tracking=2.6),
        svg.text(40, 126, "SET IN CORMORANT GARAMOND AND JETBRAINS MONO  ·  DRAWN BY A STANDARD-LIBRARY PYTHON SCRIPT", "mono", 11, pal.dim, tracking=1.8),
    )
    return svg.render()
