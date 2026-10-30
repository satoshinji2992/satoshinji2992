"""Six half-width plates, each an object from the same old archive."""

from __future__ import annotations

import math
import random

from .data import long_date, month_year
from .featured import crossfade, meta_stars
from .svg import Svg, delay, fit, measure, num
from .theme import (
    FLICKER,
    FPGA,
    GOLD,
    HBALL,
    LEROBOT,
    NAILONG,
    PRIZES,
    SEIYUU,
    Plate,
    bullet_lines,
    grain,
    kicker,
    seal,
    torn_rect,
)

W, H = 600, 380


def _title(svg: Svg, x: float, y: float, text: str, size: float, color: str, at: float = 0.15, face: str = "serif") -> str:
    return f'<g class="rise" {delay(at)}>' + svg.text(x, y, text, face, size, color) + "</g>"


def _foot(svg: Svg, x: float, y: float, text: str, color: str, stars: int | None = None, at: float = 1.0) -> str:
    out, cx = [f'<g class="fade" {delay(at)}>'], x
    stars = stars or None  # a zero count is left off
    if stars is not None:
        markup, cx = meta_stars(svg, cx, y, stars, color, 18)
        out.append(markup)
        text = " · " + text
    out.append(svg.text(cx + (4 if stars is not None else 0), y, text, "italic", 18, color))
    return "".join(out) + "</g>"


def _hatch(svg: Svg, color: str, opacity: float, step: float = 6, angle: float = 45) -> str:
    pattern = svg.uid("hatch")
    svg.define(
        f'<pattern id="{pattern}" width="{num(step)}" height="{num(step)}" patternUnits="userSpaceOnUse" patternTransform="rotate({num(angle)})">'
        f'<path d="M0 0V{num(step)}" stroke="{color}" stroke-width="1.1" stroke-opacity="{num(opacity)}"/></pattern>'
    )
    return pattern


def _screw(x: float, y: float, color: str, angle: float) -> str:
    a = math.radians(angle)
    dx, dy = 3.2 * math.cos(a), 3.2 * math.sin(a)
    return (
        f'<circle cx="{num(x)}" cy="{num(y)}" r="4.2" fill="none" stroke="{color}" stroke-width="1.35" opacity=".7"/>'
        f'<path d="M{num(x - dx)} {num(y - dy)}L{num(x + dx)} {num(y + dy)}" stroke="{color}" stroke-width="1.35" opacity=".7"/>'
    )


def seiyuumatch(data: dict) -> str:
    pal = SEIYUU
    repo = data["repos"].get("SeiyuuMatch", {})
    svg = Svg(W, H, "SeiyuuMatch: face retrieval over 119 voice actors, charted as a sky; live at seiyuumatch.org")
    plate = Plate(svg, pal)
    plate.open()
    px, py, pw, ph = 24, 24, 552, 196
    chart, sky = svg.uid("chart"), svg.uid("sky")
    svg.define(
        f'<clipPath id="{chart}"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="4"/></clipPath>',
        f'<radialGradient id="{sky}" cx=".5" cy=".62" r=".7"><stop offset="0" stop-color="#2a2140"/>'
        f'<stop offset="1" stop-color="{pal.panel}"/></radialGradient>',
    )
    # Declination arcs and hour lines of a celestial chart, centred far below.
    ccx, ccy = 300, 860
    arcs = "".join(f'<circle cx="{ccx}" cy="{ccy}" r="{r}"/>' for r in range(660, 860, 34))
    hours = "".join(
        f'<path d="M{ccx} {ccy}L{num(ccx + 900 * math.sin(math.radians(a)))} {num(ccy - 900 * math.cos(math.radians(a)))}"/>'
        for a in range(-40, 41, 8)
    )
    ticks = "".join(f'<path d="M{x} {py}v{6 if (x - px) % 40 == 0 else 3}"/>' for x in range(px + 8, px + pw, 8))
    svg.add(
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="4" fill="url(#{sky})"/>',
        f'<g clip-path="url(#{chart})"><g fill="none" stroke="{pal.accent}" stroke-width="1.1" opacity=".16">{arcs}{hours}</g>'
        f'<g stroke="{GOLD}" stroke-width="1.15" opacity=".45">{ticks}</g>',
    )
    rng = random.Random(119)
    dots = []
    for i in range(119):
        if i < 64:
            cx, cy, color = rng.gauss(208, 66), rng.gauss(132, 30), pal.accent2
        else:
            cx, cy, color = rng.gauss(398, 60), rng.gauss(120, 30), pal.accent3
        cx = min(max(cx, px + 16), px + pw - 16)
        cy = min(max(cy, py + 46), py + ph - 14)
        dots.append((cx, cy, rng.uniform(1.1, 2.4), color, rng.uniform(0, 4)))
    stars = []
    for k, (x, y, r, c, d) in enumerate(dots):
        twinkle = f' class="breathe" style="animation-delay:-{num(d)}s;animation-duration:{num(3 + d)}s"' if k % 6 == 0 else ""
        stars.append(f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r)}" fill="{c}" opacity=".85"{twinkle}/>')
        if k % 17 == 0:
            stars.append(
                f'<path d="M{num(x - 7)} {num(y)}H{num(x + 7)}M{num(x)} {num(y - 7)}V{num(y + 7)}" stroke="{c}" stroke-width="1.1" opacity=".7"/>'
            )
    svg.add('<g class="fade" style="animation-delay:.2s;animation-duration:2.4s">' + "".join(stars) + "</g>")
    queries = [(150, 168), (306, 102), (452, 154)]
    svg.style(*(crossfade(f"sq{k}", 3, k, fade=3) for k in range(3)))
    numerals = ["i", "ii", "iii", "iv", "v"]
    for k, (qx, qy) in enumerate(queries):
        nearest = sorted(dots, key=lambda d: (d[0] - qx) ** 2 + (d[1] - qy) ** 2)[:5]
        svg.style(f".sq{k}{{animation:sq{k} 15s ease-in-out 1s infinite both}}")
        lines = "".join(
            f'<path d="M{qx} {qy}L{num(x)} {num(y)}" stroke="{pal.ink}" stroke-width="1.25" opacity="{.9 if rank == 0 else .5}"/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r + 3.2)}" fill="none" stroke="{pal.ink}" stroke-width="1.15"/>'
            + svg.text(x + 6, y - 6, numerals[rank], "italic", 12, pal.ink, attrs='opacity=".85"')
            for rank, (x, y, r, _, _) in enumerate(nearest)
        )
        hidden = ' opacity="0"' if k else ""
        svg.add(
            f'<g class="sq{k}"{hidden}>{lines}'
            f'<circle cx="{qx}" cy="{qy}" r="8" fill="none" stroke="{GOLD}" stroke-width="1.45"/>'
            f'<path d="M{qx} {qy - 13}V{qy - 4}M{qx} {qy + 4}V{qy + 13}M{qx - 13} {qy}H{qx - 4}M{qx + 4} {qy}H{qx + 13}" stroke="{GOLD}" stroke-width="1.25"/>'
            f'<circle cx="{qx}" cy="{qy}" r="1.8" fill="{GOLD}"/></g>'
        )
    svg.add(
        "</g>",
        f'<rect x="{px + .5}" y="{py + .5}" width="{pw - 1}" height="{ph - 1}" rx="4" fill="none" stroke="{GOLD}" stroke-opacity=".3"/>',
        f'<g opacity=".55">{seal(px + pw - 30, py + 32, 16, GOLD, 0.6)}</g>',
        f'<g class="fade" {delay(0.5)}>' + svg.text(px + 16, py + 30, "119 voice actors · five nearest faces", "allsc", 14.5, pal.dim, tracking=1.8) + "</g>",
    )
    svg.add(
        kicker(svg, 36, 258, "Face retrieval · a live site", pal.accent, 17),
        _title(svg, 33, 314, "SeiyuuMatch", fit("SeiyuuMatch", "serif", 50, 262), pal.ink),
        bullet_lines(svg, 330, 266, ["InsightFace, top-5 matches", "group photos and face swap", "11,000+ recognitions served"], pal.ink, GOLD, 18, 26, 0.6),
        _foot(svg, 36, 352, "v2.0.0 · seiyuumatch.org", pal.dim, int(repo.get("stars", 0))),
    )
    plate.close(4, corner="br")
    return svg.render()


def _rotate(point: tuple[float, float], center: tuple[float, float], degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    x, y = point[0] - center[0], point[1] - center[1]
    return (center[0] + x * math.cos(a) - y * math.sin(a), center[1] + x * math.sin(a) + y * math.cos(a))


def _gear(cx: float, cy: float, r: float, teeth: int) -> str:
    points = []
    for k in range(teeth * 4):
        a = 2 * math.pi * k / (teeth * 4)
        rr = r if k % 4 in (1, 2) else r * 0.88
        points.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return "M" + "L".join(f"{num(x)} {num(y)}" for x, y in points) + "Z"


def lerobot(data: dict) -> str:
    pal = LEROBOT
    svg = Svg(W, H, "LeRobot: merged upstream fix for asynchronous inference; ACT, pi0 and pi0.5 on a real arm")
    plate = Plate(svg, pal)
    plate.open()
    vx, vy, vw, vh = 316, 24, 260, 332
    patina, area = svg.uid("patina"), svg.uid("area")
    hatch = _hatch(svg, pal.accent, 0.07)
    svg.define(
        f'<radialGradient id="{patina}" cx=".6" cy=".35" r=".85"><stop offset="0" stop-color="#1e2c27"/>'
        f'<stop offset="1" stop-color="{pal.panel}"/></radialGradient>',
        f'<clipPath id="{area}"><rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="4"/></clipPath>',
    )
    corners = ((vx + 12, vy + 12), (vx + vw - 12, vy + 12), (vx + 12, vy + vh - 12), (vx + vw - 12, vy + vh - 12))
    svg.add(
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="4" fill="url(#{patina})"/>',
        f'<g clip-path="url(#{area})"><rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="url(#{hatch})"/>'
        f'<g opacity=".13"><g class="spin" style="animation-duration:140s"><path d="{_gear(452, 176, 104, 22)}" fill="none" stroke="{GOLD}" stroke-width="1.45"/>'
        f'<circle cx="452" cy="176" r="70" fill="none" stroke="{GOLD}" stroke-width="1.25"/></g></g></g>',
        f'<rect x="{vx + .5}" y="{vy + .5}" width="{vw - 1}" height="{vh - 1}" rx="4" fill="none" stroke="{GOLD}" stroke-opacity=".3"/>',
        "".join(_screw(x, y, GOLD, 30 + 40 * k) for k, (x, y) in enumerate(corners)),
        f'<path d="M{vx + 20} 322H{vx + vw - 20}" stroke="{pal.accent}" stroke-width="1.35" opacity=".7"/>'
        + "".join(f'<path d="M{x} 322l-6 7" stroke="{pal.accent}" stroke-width="1.15" opacity=".45"/>' for x in range(vx + 28, vx + vw - 20, 9)),
    )
    shoulder, elbow, wrist, tip = (424, 292), (378, 204), (462, 152), (488, 186)
    reach = (6, 50, -20)
    e2 = _rotate(elbow, shoulder, reach[0])
    w2 = _rotate(_rotate(wrist, shoulder, reach[0]), e2, reach[1])
    t2 = _rotate(_rotate(_rotate(tip, shoulder, reach[0]), e2, reach[1]), w2, reach[2])
    cube_x, cube_y = t2[0] - 13, 296
    svg.style(
        f"@keyframes j1{{0%,100%{{transform:rotate(0)}}45%,62%{{transform:rotate({reach[0]}deg)}}}}",
        f"@keyframes j2{{0%,100%{{transform:rotate(0)}}45%,62%{{transform:rotate({reach[1]}deg)}}}}",
        f"@keyframes j3{{0%,100%{{transform:rotate(0)}}45%,62%{{transform:rotate({reach[2]}deg)}}}}",
        "@keyframes grip{0%,40%{transform:rotate(-16deg)}50%,70%{transform:rotate(0)}85%,100%{transform:rotate(-16deg)}}",
        "@keyframes grip2{0%,40%{transform:rotate(16deg)}50%,70%{transform:rotate(0)}85%,100%{transform:rotate(16deg)}}",
        ".j1,.j2,.j3,.g1,.g2{transform-box:view-box;animation-duration:10s;animation-iteration-count:infinite;"
        "animation-timing-function:cubic-bezier(.45,0,.3,1);animation-delay:1.5s;animation-fill-mode:both}",
        ".j1{animation-name:j1}.j2{animation-name:j2}.j3{animation-name:j3}.g1{animation-name:grip}.g2{animation-name:grip2}",
        "@keyframes chunk{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}",
        ".chunk{animation:chunk 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 100%}",
    )

    def link(a: tuple[float, float], b: tuple[float, float]) -> str:
        d = f"M{num(a[0])} {num(a[1])}L{num(b[0])} {num(b[1])}"
        return (
            f'<path d="{d}" stroke="{pal.accent}" stroke-width="22" stroke-linecap="round" opacity=".9"/>'
            f'<path d="{d}" stroke="#16221d" stroke-width="19.5" stroke-linecap="round"/>'
            f'<path d="{d}" stroke="{pal.accent}" stroke-width="1.25" stroke-dasharray="2 5" stroke-linecap="round" opacity=".7"/>'
        )

    def joint(c: tuple[float, float]) -> str:
        return (
            f'<circle cx="{num(c[0])}" cy="{num(c[1])}" r="10.5" fill="{pal.bg}" stroke="{GOLD}" stroke-width="1.6"/>'
            f'<circle cx="{num(c[0])}" cy="{num(c[1])}" r="6.5" fill="none" stroke="{GOLD}" stroke-width="1.1" opacity=".7"/>'
            f'<circle cx="{num(c[0])}" cy="{num(c[1])}" r="2.4" fill="{GOLD}"/>'
        )

    fx, fy = tip
    fingers = (
        f'<g class="g1" style="transform-origin:{fx}px {fy}px"><path d="M{fx} {fy}l-11 6v16" fill="none" stroke="{pal.accent}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
        f'<g class="g2" style="transform-origin:{fx}px {fy}px"><path d="M{fx} {fy}l11 6v16" fill="none" stroke="{pal.accent}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
    )
    arm = (
        f'<g class="j1" style="transform-origin:{shoulder[0]}px {shoulder[1]}px">{link(shoulder, elbow)}'
        f'<g class="j2" style="transform-origin:{elbow[0]}px {elbow[1]}px">{link(elbow, wrist)}'
        f'<g class="j3" style="transform-origin:{wrist[0]}px {wrist[1]}px">{link(wrist, tip)}{fingers}{joint(wrist)}</g>'
        f"{joint(elbow)}</g>{joint(shoulder)}</g>"
    )
    svg.add(
        f'<g class="fade" {delay(0.4)}>'
        f'<path d="M{shoulder[0] + 34} {shoulder[1]}A34 34 0 0 0 {shoulder[0]} {shoulder[1] - 34}" fill="none" stroke="{GOLD}" stroke-width="1.15" stroke-dasharray="2 4" opacity=".6"/>'
        f'<rect x="{num(cube_x)}" y="{num(cube_y)}" width="26" height="26" rx="1" fill="{GOLD}" fill-opacity=".12" stroke="{GOLD}" stroke-width="1.55"/>'
        f'<path d="M{num(cube_x)} {num(cube_y)}l6-6h26l-6 6M{num(cube_x + 26)} {num(cube_y + 26)}l6-6v-26" fill="none" stroke="{GOLD}" stroke-width="1.25" opacity=".7"/>'
        f'<path d="M398 322V306Q398 298 406 298H442Q450 298 450 306V322" fill="{pal.panel}" stroke="{pal.accent}" stroke-width="1.5"/>'
        f"{arm}</g>",
        f'<g class="fade" {delay(0.8)}><rect x="524" y="50" width="32" height="22" rx="2" fill="{pal.bg}" stroke="{pal.accent}" stroke-width="1.45"/>'
        f'<circle cx="540" cy="61" r="6" fill="none" stroke="{GOLD}" stroke-width="1.45"/><circle cx="540" cy="61" r="2" fill="{GOLD}"/>'
        f'<path d="M530 74L{num(cube_x - 6)} {num(cube_y)}M550 74L{num(cube_x + 30)} {num(cube_y)}" stroke="{pal.accent}" stroke-width="1.15" stroke-dasharray="2 5" opacity=".55"/></g>',
    )
    bars = "".join(
        f'<rect class="chunk" style="animation-delay:-{num(k * 0.19)}s" x="{336 + k * 8}" y="60" width="4" height="20" rx="1" fill="{GOLD}" opacity=".85"/>'
        for k in range(10)
    )
    svg.add(f'<g class="fade" {delay(0.9)}>' + svg.text(336, 50, "action chunk", "italic", 14, pal.dim) + bars + "</g>")
    svg.add(
        kicker(svg, 36, 64, "Robot learning · upstream", pal.accent, 17),
        _title(svg, 33, 126, "LeRobot", 56, pal.ink),
        f'<g class="rise" {delay(0.3)}>' + svg.text(36, 162, "merged into huggingface/lerobot", "italic", 21, "#b9cbc1") + "</g>",
        bullet_lines(svg, 36, 218, ["PR #2792, asynchronous inference", "actions moved to client_device", "ACT, π0 and π0.5 on a real arm"], pal.ink, GOLD, 18, 28, 0.55),
        _foot(svg, 36, 350, f"merged {long_date('2026-01-20T14:17:38Z')}", pal.dim),
    )
    plate.close(5, corner="tl")
    return svg.render()


def hball(data: dict) -> str:
    pal = HBALL
    brass = pal.accent
    svg = Svg(W, H, "H_ball and servo: electronics design contest builds, a MaixCAM eye feeding STM32 control")
    plate = Plate(svg, pal)
    plate.open()
    hatch = _hatch(svg, brass, 0.07, 5)
    svg.add(f'<rect x="300" y="0" width="300" height="{H}" fill="url(#{hatch})"/>')
    traces = [
        "M418 84H452L486 118V150",
        "M448 210H404L366 248V252",
        "M506 226V250L520 264V270",
        "M366 128V140L388 162H448",
        "M524 170H560V312H546",
    ]
    svg.style(
        "@keyframes glint{from{stroke-dashoffset:0}to{stroke-dashoffset:-130}}",
        ".glint{stroke-dasharray:5 125;animation:glint 5.5s linear infinite}",
        "@keyframes swing{0%,100%{transform:rotate(-28deg)}50%{transform:rotate(28deg)}}",
        ".swing{animation:swing 4.4s ease-in-out infinite;transform-box:view-box;transform-origin:366px 280px}",
        "@keyframes roll{0%,100%{transform:translateX(0)}50%{transform:translateX(72px)}}",
        ".rollball{animation:roll 4.4s ease-in-out infinite}",
    )
    pearl = svg.uid("pearl")
    svg.define(
        f'<radialGradient id="{pearl}" cx=".35" cy=".35" r=".7"><stop offset="0" stop-color="#fbf6ea"/>'
        '<stop offset=".6" stop-color="#cfc6b2"/><stop offset="1" stop-color="#7d7462"/></radialGradient>'
    )
    lens_ticks = "".join(
        f'<path d="M{num(366 + 27 * math.cos(math.radians(a)))} {num(84 + 27 * math.sin(math.radians(a)))}'
        f'L{num(366 + 31 * math.cos(math.radians(a)))} {num(84 + 31 * math.sin(math.radians(a)))}"/>'
        for a in range(0, 360, 15)
    )
    pins = "".join(
        f'<rect x="{num(452 + k * 7.6)}" y="142" width="2.4" height="7"/><rect x="{num(452 + k * 7.6)}" y="227" width="2.4" height="7"/>'
        f'<rect x="441" y="{num(154 + k * 7.6)}" width="7" height="2.4"/><rect x="524" y="{num(154 + k * 7.6)}" width="7" height="2.4"/>'
        for k in range(9)
    )
    svg.add(
        f'<g fill="none" stroke="{brass}" stroke-width="1.6" stroke-linejoin="round" opacity=".5">' + "".join(f'<path d="{d}"/>' for d in traces) + "</g>",
        f'<g fill="none" stroke="#f3dda0" stroke-width="1.9" stroke-linecap="round">'
        + "".join(f'<path class="glint" style="animation-delay:-{num(k * 1.1)}s" d="{d}"/>' for k, d in enumerate(traces))
        + "</g>",
        # The eye: a MaixCAM lens engraved like an instrument.
        f'<rect x="318" y="46" width="96" height="76" rx="3" fill="#0d0b08" stroke="{brass}" stroke-width="1.45"/>'
        f'<g stroke="{brass}" stroke-width="1.15" opacity=".7">{lens_ticks}</g>'
        f'<circle cx="366" cy="84" r="24" fill="none" stroke="{brass}" stroke-width="1.45"/>'
        f'<circle cx="366" cy="84" r="15" fill="#05060a" stroke="{brass}" stroke-width="1.1"/>'
        f'<circle cx="366" cy="84" r="6" fill="none" stroke="{brass}" stroke-width="1" opacity=".7"/>'
        f'<circle cx="361" cy="79" r="2.6" fill="#f3dda0" opacity=".75"/>'
        + svg.text(366, 140, "MaixCAM", "allsc", 14.5, pal.ink, "middle", tracking=1.6)
        # The chip.
        + f'<g fill="{brass}" opacity=".8">{pins}</g>'
        + f'<rect x="448" y="149" width="76" height="78" rx="2" fill="#0c0b08" stroke="{brass}" stroke-width="1.35"/>'
        + f'<rect x="454" y="155" width="64" height="66" rx="1" fill="none" stroke="{brass}" stroke-width="1" opacity=".5"/>'
        + f'<circle cx="460" cy="161" r="2" fill="{pal.dim}"/>'
        + svg.text(486, 193, "STM32", "allsc", 15, pal.ink, "middle", tracking=1.2)
        + svg.text(486, 211, "F103", "italic", 13, pal.dim, "middle")
        # The servo, swinging like a pendulum.
        + f'<rect x="324" y="252" width="84" height="56" rx="3" fill="#0d0b08" stroke="{brass}" stroke-width="1.45"/>'
        + f'<g class="swing"><path d="M366 280L366 254" stroke="{pal.ink}" stroke-width="3.5" stroke-linecap="round"/><circle cx="366" cy="254" r="3" fill="{pal.ink}"/></g>'
        + f'<circle cx="366" cy="280" r="7" fill="#0d0b08" stroke="{brass}" stroke-width="1.5"/>'
        + svg.text(366, 326, "Servo", "allsc", 14.5, pal.ink, "middle", tracking=1.6)
        # The IMU.
        + f'<rect x="500" y="270" width="40" height="30" rx="2" fill="#0c0b08" stroke="{brass}" stroke-width="1.35"/>'
        + svg.text(520, 290, "JY61", "allsc", 14.5, pal.ink, "middle", tracking=1)
        # The ball on its rail.
        + f'<path d="M444 336H566M444 342H566" stroke="{brass}" stroke-width="1.35" opacity=".7"/>'
        + f'<g class="rollball"><circle cx="460" cy="329" r="7" fill="url(#{pearl})"/></g>'
        + svg.text(436, 76, "uart", "allsc", 14.5, brass, "end", tracking=1.2),
        "".join(_screw(x, y, brass, 20 + 50 * k) for k, (x, y) in enumerate(((586, 22), (586, 358)))),
    )
    svg.add(
        f'<path d="M24 24H292V356H24Z" fill="none" stroke="{brass}" stroke-opacity=".28"/>'
        f'<path d="M29 29H287V351H29Z" fill="none" stroke="{brass}" stroke-opacity=".14"/>',
        kicker(svg, 42, 72, "Electronics design contest", brass, 15),
        _title(svg, 40, 132, "H_ball", 54, pal.ink),
        _title(svg, 42, 176, "+ servo", 38, "#cfc6aa", 0.25, "italic"),
        bullet_lines(svg, 42, 228, ["YOLO11n on a MaixCAM", "alpha–beta filter, UART link", "STM32 gimbal: PID and IMU"], pal.ink, brass, 18, 27, 0.55),
        f'<g class="fade" {delay(1.0)}>' + svg.text(42, 334, "Provincial 2nd, 2026 · 3rd, 2025", "allsc", 14.5, brass, tracking=1.4) + "</g>",
    )
    plate.close(6, corner="tr")
    return svg.render()


def nailong(data: dict) -> str:
    pal = NAILONG
    repo = data["repos"].get("naiLongRacing", {})
    amber = pal.accent
    svg = Svg(W, H, "naiLongRacing: a pseudo-3D racer in plain C on openvela, seen through a magic lantern")
    plate = Plate(svg, pal)
    plate.open()
    cx, cy, r = 440, 162, 112
    lens, sky, warm, edge = svg.uid("lens"), svg.uid("sky"), svg.uid("warm"), svg.uid("edge")
    svg.define(
        f'<clipPath id="{lens}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>',
        f'<linearGradient id="{sky}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2e1a07"/>'
        '<stop offset="1" stop-color="#160c04"/></linearGradient>',
        f'<radialGradient id="{warm}" cx=".5" cy=".45" r=".6"><stop offset="0" stop-color="#ffcf86" stop-opacity=".16"/>'
        '<stop offset="1" stop-color="#ffcf86" stop-opacity="0"/></radialGradient>',
        f'<radialGradient id="{edge}" cx=".5" cy=".5" r=".5"><stop offset=".72" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".75"/></radialGradient>',
    )
    horizon, bottom = 150, cy + r

    def road_x(y: float) -> tuple[float, float]:
        t = (y - horizon) / (bottom - horizon)
        half = 6 + t * 128
        return cx - half, cx + half

    bands_a, bands_b = [], []
    ys = [horizon + (bottom - horizon) / (1 + k * 0.55) for k in range(16)]
    for k in range(len(ys) - 1):
        y0, y1 = ys[k], ys[k + 1]
        l0, r0 = road_x(y0)
        l1, r1 = road_x(y1)
        kerb = 0.12
        shape = (
            f"M{num(l0)} {num(y0)}L{num(l0 + (r0 - l0) * kerb / 2)} {num(y0)}L{num(l1 + (r1 - l1) * kerb / 2)} {num(y1)}L{num(l1)} {num(y1)}Z"
            f"M{num(r0)} {num(y0)}L{num(r0 - (r0 - l0) * kerb / 2)} {num(y0)}L{num(r1 - (r1 - l1) * kerb / 2)} {num(y1)}L{num(r1)} {num(y1)}Z"
            f"M{num(cx - (r0 - l0) * 0.012)} {num(y0)}L{num(cx + (r0 - l0) * 0.012)} {num(y0)}L{num(cx + (r1 - l1) * 0.012)} {num(y1)}L{num(cx - (r1 - l1) * 0.012)} {num(y1)}Z"
        )
        (bands_a if k % 2 == 0 else bands_b).append(shape)
    tl, tr = road_x(horizon)
    bl, br = road_x(bottom)
    svg.style(
        FLICKER,
        "@keyframes flipa{0%,49.9%{opacity:1}50%,100%{opacity:.1}}",
        "@keyframes flipb{0%,49.9%{opacity:.1}50%,100%{opacity:1}}",
        ".flipa{animation:flipa .5s step-end infinite}.flipb{animation:flipb .5s step-end infinite}",
        "@keyframes sway{0%,100%{transform:translateX(-12px)}50%{transform:translateX(12px)}}",
        ".sway{animation:sway 4s ease-in-out infinite}",
    )
    mountains = (
        f"M{cx - r} 150L{cx - 92} 128L{cx - 74} 138L{cx - 48} 114L{cx - 22} 134L{cx - 4} 124L{cx + 22} 140"
        f"L{cx + 46} 118L{cx + 70} 134L{cx + 92} 122L{cx + r} 138V150Z"
    )
    car_y = bottom - 34
    car = (
        f'<g class="sway"><rect x="{cx - 20}" y="{car_y}" width="40" height="12" rx="3" fill="{amber}"/>'
        f'<rect x="{cx - 13}" y="{car_y - 9}" width="26" height="11" rx="3" fill="#7a4a12"/>'
        f'<rect x="{cx - 10}" y="{car_y - 7}" width="20" height="6" rx="2" fill="#2a1806"/>'
        f'<rect x="{cx - 24}" y="{car_y + 7}" width="8" height="9" rx="2" fill="#2a1806"/>'
        f'<rect x="{cx + 16}" y="{car_y + 7}" width="8" height="9" rx="2" fill="#2a1806"/>'
        f'<rect x="{cx - 16}" y="{car_y + 3}" width="5" height="2.6" fill="#fff3d6"/><rect x="{cx + 11}" y="{car_y + 3}" width="5" height="2.6" fill="#fff3d6"/></g>'
    )

    def polar(radius: float, degrees: float) -> tuple[float, float]:
        a = math.radians(degrees)
        return cx + radius * math.cos(a), cy + radius * math.sin(a)

    ring_ticks = "".join(
        f'<path d="M{num(polar(r + 6, a)[0])} {num(polar(r + 6, a)[1])}L{num(polar(r + (11 if a % 30 == 0 else 8), a)[0])} {num(polar(r + (11 if a % 30 == 0 else 8), a)[1])}"/>'
        for a in range(0, 360, 6)
    )
    svg.add(
        f'<circle cx="{cx}" cy="{cy}" r="{r + 18}" fill="#1a1209" stroke="{pal.line}" stroke-width="1.45"/>',
        f'<g stroke="{amber}" stroke-width="1.15" opacity=".55">{ring_ticks}</g>',
        f'<circle cx="{cx}" cy="{cy}" r="{r + 4}" fill="none" stroke="{amber}" stroke-width="1.45" opacity=".6"/>',
        f'<g clip-path="url(#{lens})"><rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" fill="url(#{sky})"/>'
        f'<circle cx="{cx + 50}" cy="140" r="22" fill="{amber}" opacity=".24"/>'
        f'<path d="M{cx + 28} 132H{cx + 72}M{cx + 30} 138H{cx + 70}M{cx + 34} 144H{cx + 66}" stroke="#1f1307" stroke-width="2.2"/>'
        f'<path d="{mountains}" fill="{pal.accent2}" opacity=".3"/>'
        f'<path d="M{num(tl)} {horizon}L{num(tr)} {horizon}L{num(br)} {bottom}L{num(bl)} {bottom}Z" fill="#1c1107"/>'
        f'<path d="M{num(tl)} {horizon}L{num(bl)} {bottom}M{num(tr)} {horizon}L{num(br)} {bottom}" stroke="{amber}" stroke-width="1.45" opacity=".7"/>'
        f'<path class="flipa" d="{"".join(bands_a)}" fill="{amber}"/>'
        f'<path class="flipb" d="{"".join(bands_b)}" fill="{amber}" opacity=".1"/>'
        f"{car}"
        + grain(svg, cx - r, cy - r, 2 * r, 2 * r, 0.9)
        + f'<circle class="flicker" cx="{cx}" cy="{cy}" r="{r}" fill="url(#{warm})"/>'
        + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{edge})"/></g>',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#000" stroke-opacity=".6" stroke-width="1.8"/>',
        "".join(_screw(*polar(r + 26, a), amber, a) for a in (-135, -45, 45, 135)),
        f'<g class="fade" {delay(0.8)}>' + svg.text(cx, 330, "R528 · NuttX · SPI LCD", "allsc", 14.5, pal.dim, "middle", tracking=2) + "</g>",
    )
    svg.add(
        kicker(svg, 36, 64, "openvela · embedded game", amber, 17),
        _title(svg, 33, 126, "naiLong", 54, pal.ink),
        _title(svg, 33, 176, "Racing", 54, pal.ink, 0.25),
        bullet_lines(svg, 36, 230, ["a pseudo-3D racer in plain C", "framebuffer straight to SPI LCD", "an SDL twin for the desktop"], pal.ink, amber, 18, 27, 0.55),
        _foot(svg, 36, 350, f"updated {month_year(repo.get('pushed_at'))}", pal.dim, int(repo.get("stars", 0))),
    )
    plate.close(7, corner="br")
    return svg.render()


def fpga(data: dict) -> str:
    pal = FPGA
    repo = data["repos"].get("fpga_cpu", {})
    ink = "#5b2a1a"
    svg = Svg(W, H, "FPGA RISC-V CPU: RV32IM, five-stage pipeline, 50 MHz on a Spartan-6 board, traced by a chart recorder")
    plate = Plate(svg, pal)
    plate.open()
    tx, ty, tw, th = 36, 34, 528, 142
    pen_x = 420
    tape, drawn, sheet = svg.uid("tape"), svg.uid("drawn"), svg.uid("sheet")
    svg.define(
        f'<clipPath id="{tape}"><rect x="{tx}" y="{ty}" width="{tw}" height="{th}"/></clipPath>',
        f'<clipPath id="{drawn}"><rect x="{tx}" y="{ty}" width="{pen_x - tx}" height="{th}"/></clipPath>',
        f'<linearGradient id="{sheet}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e4d7bd"/>'
        '<stop offset="1" stop-color="#cbb995"/></linearGradient>',
    )
    # Chart paper and trace scroll together; one loop moves 704 px, a whole number of clock periods.
    period, travel, loop = 44, 704, 19.2
    high, low = 62, 92
    x0, x1 = tx - period, tx + tw + travel
    minor = "".join(f"M{x} {ty}V{ty + th}" for x in range(tx, x1, 11)) + "".join(f"M{tx} {y}H{x1}" for y in range(ty, ty + th + 1, 11))
    major = "".join(f"M{x} {ty}V{ty + th}" for x in range(tx, x1, 44))
    clock = [f"M{x0} {low}"]
    x = x0
    while x < x1:
        clock.append(f"H{x + period / 2}V{high}H{x + period}V{low}")
        x += period
    mnemonics = ["addi", "lw", "beq", "mul", "sw", "jal", "xor", "lui"]
    bus, labels = [], []
    seg, k = 88, 0
    x = tx - seg
    while x < x1:
        b0, b1 = 124, 146
        bus.append(f"M{x + 6} {b0}L{x + seg - 6} {b0}L{x + seg} {(b0 + b1) / 2}L{x + seg - 6} {b1}L{x + 6} {b1}L{x} {(b0 + b1) / 2}Z")
        labels.append(svg.text(x + seg / 2, 140, mnemonics[k % len(mnemonics)], "italic", 15, ink, "middle"))
        x += seg
        k += 1
    # Keep the nib on the trace: each period is low for its first half, and the
    # tape moves left, so the phase under the pen grows with time.
    speed = travel / loop
    half = period / 2 / speed
    phase = (pen_x - x0) % period
    elapsed = half - (period / 2 - phase) / speed if phase < period / 2 else 2 * half - (period - phase) / speed
    svg.style(
        f"@keyframes scroll{{to{{transform:translateX(-{travel}px)}}}}",
        f".scroll{{animation:scroll {num(loop)}s linear infinite}}",
        f"@keyframes nib{{0%,49.99%{{transform:translateY(0)}}50%,100%{{transform:translateY({high - low}px)}}}}",
        f".nib{{animation:nib {num(2 * half, 3)}s linear -{num(elapsed, 3)}s infinite}}",
        "@keyframes token{0%{transform:translateX(0)}20%{transform:translateX(53px)}40%{transform:translateX(106px)}"
        "60%{transform:translateX(159px)}80%,100%{transform:translateX(212px)}}",
        ".token{animation:token 3.5s step-end infinite}",
    )
    svg.add(
        f'<rect x="{tx}" y="{ty + 4}" width="{tw}" height="{th}" fill="#000" opacity=".4"/>',
        f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" fill="url(#{sheet})"/>',
        f'<g clip-path="url(#{tape})"><g class="scroll">'
        f'<path d="{minor}" stroke="#a0533a" stroke-width="0.9" opacity=".2"/>'
        f'<path d="{major}" stroke="#a0533a" stroke-width="1.1" opacity=".38"/></g>'
        + grain(svg, tx, ty, tw, th, 0.8)
        + f'<g clip-path="url(#{drawn})"><g class="scroll"><path d="{"".join(clock)}" fill="none" stroke="{ink}" stroke-width="1.8" stroke-linejoin="round"/>'
        f'<path d="{"".join(bus)}" fill="none" stroke="{ink}" stroke-width="1.45" opacity=".85"/>{"".join(labels)}</g></g></g>',
        "".join(
            f'<rect x="{rx}" y="{ty - 6}" width="12" height="{th + 12}" rx="4" fill="#3a2a20" stroke="{GOLD}" stroke-width="1.25" stroke-opacity=".6"/>'
            f'<path d="M{rx + 4} {ty - 2}V{ty + th + 2}" stroke="{GOLD}" stroke-width="1.25" opacity=".35"/>'
            for rx in (tx - 12, tx + tw)
        ),
        f'<g class="nib"><path d="M{pen_x} 14V{low - 4}" stroke="{GOLD}" stroke-width="1.9"/>'
        f'<path d="M{pen_x - 4} {low - 12}L{pen_x} {low}L{pen_x + 4} {low - 12}Z" fill="{GOLD}"/></g>',
        svg.text(tx + 8, ty + 18, "clock · 50 MHz", "allsc", 14.5, "#8a3e28", tracking=1.4),
        svg.text(tx + tw - 8, ty + 18, "timing met at 51.68 MHz", "italic", 14, "#8a3e28", "end"),
    )
    stages = ["IF", "ID", "EX", "MEM", "WB"]
    px0, py0, bw, gap = 320, 258, 44, 9
    boxes = "".join(
        f'<rect x="{px0 + k * (bw + gap)}" y="{py0}" width="{bw}" height="30" rx="2" fill="{pal.panel}" stroke="{pal.line}" stroke-width="1.45"/>'
        f'<rect x="{px0 + k * (bw + gap) + 3}" y="{py0 + 3}" width="{bw - 6}" height="24" rx="1" fill="none" stroke="{GOLD}" stroke-width="1" stroke-opacity=".35"/>'
        + svg.text(px0 + k * (bw + gap) + bw / 2, py0 + 20, name, "allsc", 14, pal.ink, "middle", tracking=0.8)
        for k, name in enumerate(stages)
    )
    ex, mem = px0 + 2 * (bw + gap) + bw / 2, px0 + 3 * (bw + gap) + bw / 2
    svg.add(
        f'<g class="fade" {delay(0.6)}>'
        + svg.text(px0, 242, "Five-stage pipeline", "allsc", 14.5, pal.dim, tracking=1.6)
        + boxes
        + f'<path class="token" d="M{px0 + bw / 2} {py0 + 31}l4 4-4 4-4-4z" fill="{GOLD}"/>'
        + f'<path d="M{mem} {py0 + 32}V{py0 + 46}H{ex}V{py0 + 34}" fill="none" stroke="{pal.accent}" stroke-width="1.35" stroke-dasharray="3 3"/>'
        + f'<path d="M{ex - 4} {py0 + 39}L{ex} {py0 + 34}L{ex + 4} {py0 + 39}" fill="none" stroke="{pal.accent}" stroke-width="1.35"/>'
        + svg.text(px0 + 256, py0 + 56, "forwarding", "italic", 14, pal.dim, "end")
        + svg.text(px0, 342, f"17 RTL regressions · {month_year(repo.get('pushed_at'))}", "italic", 16, pal.dim)
        + "</g>"
    )
    svg.add(
        kicker(svg, 36, 238, "RISC-V · Spartan-6", pal.accent, 17),
        _title(svg, 33, 292, "FPGA CPU", 50, pal.ink),
        f'<g class="fade" {delay(0.6)}>'
        + svg.text(36, 322, "RV32IM, 2-bit BHT, I-cache", "italic", 18, "#d9c4b6")
        + svg.text(36, 346, "SDRAM, a UART shell, an MLP demo", "italic", 18, "#d9c4b6")
        + "</g>",
    )
    plate.close(8, corner="br")
    return svg.render()


PRIZE_ROWS = [
    ("2026", "RoboMaster University League", "National 2nd"),
    ("2026", "CUMCM · Math Modeling", "National 2nd"),
    ("2026", "Electronics Design Contest · H", "Provincial 2nd"),
    ("2025", "Electronics Design Contest · E", "Provincial 3rd"),
]


def prizes(data: dict) -> str:
    pal = PRIZES
    ink, rose, paper = "#2a2124", "#9c4f63", pal.accent3
    svg = Svg(W, H, "Prizes: national second prizes in the RoboMaster University League and CUMCM; electronics design contest provincial prizes")
    plate = Plate(svg, pal)
    plate.open()
    rosette = "".join(f'<ellipse cx="300" cy="190" rx="300" ry="96" transform="rotate({k * 7.5} 300 190)"/>' for k in range(24))
    rosette2 = "".join(f'<ellipse cx="300" cy="190" rx="220" ry="60" transform="rotate({k * 10 + 5} 300 190)"/>' for k in range(18))
    svg.add(f'<g fill="none" stroke="{pal.accent}" stroke-width="1.1" opacity=".09">{rosette}{rosette2}</g>')
    sheet = torn_rect(44, 40, 512, 296, 2.4, seed=2026, edges="lrtb")
    rng = random.Random(1925)
    foxing = "".join(
        f'<circle cx="{num(rng.uniform(60, 540))}" cy="{num(rng.uniform(56, 320))}" r="{num(rng.uniform(3, 14))}" fill="#8a6234" opacity="{num(rng.uniform(.04, .09))}"/>'
        for _ in range(9)
    )
    svg.add(
        f'<g transform="rotate(-1.2 300 190)">'
        f'<path d="{sheet}" transform="translate(4 6)" fill="#000" opacity=".45"/>'
        f'<path d="{sheet}" fill="{paper}"/>{foxing}'
        + grain(svg, 40, 36, 520, 304, 0.9)
        + f'<rect x="58" y="54" width="484" height="268" fill="none" stroke="{rose}" stroke-width="1.35" opacity=".55"/>'
        f'<rect x="62" y="58" width="476" height="260" fill="none" stroke="{rose}" stroke-width="1" opacity=".45"/>'
        + f'<g class="rise" {delay(0.2)}>'
        + svg.text(80, 104, "Prizes", "serif", 38, ink)
        + svg.text(520, 100, "2025 – 2026", "allsc", 14, rose, "end", tracking=1.8)
        + "</g>"
        + f'<path class="draw" {delay(0.4)} d="M80 118H520" pathLength="1" stroke="{rose}" stroke-width="1.45"/>'
        + f'<path class="draw" {delay(0.5)} d="M80 121.5H520" pathLength="1" stroke="{rose}" stroke-width="1" opacity=".7"/>'
    )
    for i, (year, name, level) in enumerate(PRIZE_ROWS):
        y = 160 + i * 42
        name_end = 128 + measure(name, "serif-m", 21)
        level_start = 520 - measure(level, "italic", 20)
        leader = ""
        if level_start - name_end > 40:
            leader = f'<path d="M{num(name_end + 10)} {y - 4}H{num(level_start - 10)}" stroke="{rose}" stroke-width="1.5" stroke-dasharray="1 5" stroke-linecap="round" opacity=".55"/>'
        svg.add(
            f'<g class="rise" {delay(0.45 + i * 0.12)}>'
            + svg.text(80, y, year, "italic", 18, "#8a6a71")
            + svg.text(128, y, name, "serif-m", 21, ink)
            + leader
            + svg.text(520, y, level, "italic", 20, rose, "end")
            + "</g>"
        )
    svg.add("</g>")
    svg.style("@keyframes sheen{0%,100%{opacity:.12}50%{opacity:.42}}", ".sheen{animation:sheen 6s ease-in-out infinite}")
    sx, sy = 526, 316
    svg.add(
        f'<g class="fade" {delay(1.0)}>'
        f'<circle cx="{sx + 3}" cy="{sy + 4}" r="31" fill="#000" opacity=".4"/>'
        f'<path d="M{sx - 31} {sy}Q{sx - 33} {sy - 20} {sx - 18} {sy - 28}Q{sx} {sy - 36} {sx + 18} {sy - 28}Q{sx + 33} {sy - 18} {sx + 31} {sy}'
        f'Q{sx + 33} {sy + 20} {sx + 18} {sy + 28}Q{sx} {sy + 36} {sx - 18} {sy + 28}Q{sx - 33} {sy + 18} {sx - 31} {sy}Z" fill="#7f3343"/>'
        f'<circle cx="{sx}" cy="{sy}" r="22" fill="#94404f" stroke="#6c2635" stroke-width="2"/>'
        f'<g opacity=".7">{seal(sx, sy, 18, "#d68a99", 0.7)}</g>'
        f'<ellipse class="sheen" cx="{sx - 8}" cy="{sy - 12}" rx="12" ry="5" fill="#fff" transform="rotate(-30 {sx - 8} {sy - 12})"/>'
        "</g>"
    )
    plate.close(9, corner="bl")
    return svg.render()
