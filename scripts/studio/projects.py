"""Six half-width plates, each in its own material and layout."""

from __future__ import annotations

import math
import random

from .data import month_year, short_date
from .featured import crossfade, meta_stars
from .svg import Svg, delay, fit, measure, num
from .theme import (
    FPGA,
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


def _foot(svg: Svg, x: float, y: float, parts: list[str], color: str, stars: int | None = None, at: float = 1.0) -> str:
    out, cx = [f'<g class="fade" {delay(at)}>'], x
    if stars is not None:
        markup, cx = meta_stars(svg, cx, y, stars, color, 13)
        out.append(markup)
        cx += 16
    out.append(svg.text(cx, y, "  ·  ".join(parts), "mono", 13, color))
    return "".join(out) + "</g>"


def seiyuumatch(data: dict) -> str:
    pal = SEIYUU
    repo = data["repos"].get("SeiyuuMatch", {})
    svg = Svg(W, H, "SeiyuuMatch: face retrieval over 119 voice actors, live at seiyuumatch.org")
    plate = Plate(svg, pal, rx=16)
    plate.open()
    px, py, pw, ph = 22, 22, 556, 198
    panel, nebula = svg.uid("panel"), svg.uid("nebula")
    svg.define(
        f'<clipPath id="{panel}"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12"/></clipPath>',
        f'<radialGradient id="{nebula}" cx=".5" cy=".55" r=".6"><stop offset="0" stop-color="#3a2d52" stop-opacity=".75"/>'
        f'<stop offset="1" stop-color="{pal.panel}" stop-opacity="0"/></radialGradient>',
    )
    svg.add(
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12" fill="{pal.panel}" stroke="{pal.line}"/>',
        f'<g clip-path="url(#{panel})"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="url(#{nebula})"/>',
    )
    rng = random.Random(119)
    dots = []
    for i in range(119):
        if i < 64:
            cx, cy, color = rng.gauss(208, 64), rng.gauss(128, 30), pal.accent2
        else:
            cx, cy, color = rng.gauss(398, 58), rng.gauss(116, 30), pal.accent3
        cx = min(max(cx, px + 16), px + pw - 16)
        cy = min(max(cy, py + 44), py + ph - 14)
        dots.append((cx, cy, rng.uniform(1.7, 3.1), color, rng.uniform(0, 4)))
    svg.add(
        '<g class="fade" style="animation-delay:.2s;animation-duration:2s">'
        + "".join(
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r)}" fill="{c}" opacity=".78"'
            + (f' class="breathe" style="animation-delay:-{num(d)}s"' if k % 7 == 0 else "")
            + "/>"
            for k, (x, y, r, c, d) in enumerate(dots)
        )
        + "</g>"
    )
    queries = [(150, 162), (306, 96), (452, 150)]
    svg.style(*(crossfade(f"sq{k}", 3, k, fade=3) for k in range(3)))
    for k, (qx, qy) in enumerate(queries):
        nearest = sorted(dots, key=lambda d: (d[0] - qx) ** 2 + (d[1] - qy) ** 2)[:5]
        svg.style(f".sq{k}{{animation:sq{k} 12s ease-in-out 1s infinite both}}")
        lines = "".join(
            f'<path d="M{qx} {qy}L{num(x)} {num(y)}" stroke="{pal.ink}" stroke-width="{1.6 if rank == 0 else 0.9}" opacity="{0.95 if rank == 0 else 0.55}"/>'
            f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r + 3.5)}" fill="none" stroke="{pal.ink}" stroke-width="1"/>'
            for rank, (x, y, r, _, _) in enumerate(nearest)
        )
        top = nearest[0]
        hidden = ' opacity="0"' if k else ""
        svg.add(
            f'<g class="sq{k}"{hidden}>{lines}'
            f'<circle cx="{qx}" cy="{qy}" r="9" fill="none" stroke="{pal.ink}" stroke-width="1.6"/>'
            f'<circle cx="{qx}" cy="{qy}" r="2.6" fill="{pal.ink}"/>'
            f'<path d="M{qx - 16} {qy}h6M{qx + 10} {qy}h6M{qx} {qy - 16}v6M{qx} {qy + 10}v6" stroke="{pal.ink}" stroke-width="1.2"/>'
            + svg.text(top[0] + 8, top[1] - 8, "1", "mono-b", 11, pal.ink)
            + "</g>"
        )
    svg.add(
        "</g>",
        f'<g class="fade" {delay(0.5)}>' + svg.text(px + 18, py + 28, "119 VOICE ACTORS  ·  TOP-5 NEAREST FACES", "mono-b", 11, pal.dim, tracking=2) + "</g>",
    )
    svg.add(
        kicker(svg, 36, 258, "FACE RETRIEVAL  ·  LIVE SITE", pal.accent, size=12),
        _title(svg, 33, 312, "SeiyuuMatch", fit("SeiyuuMatch", "serif", 50, 262), pal.ink),
        bullet_lines(svg, 334, 282, ["InsightFace, top-5 matches", "group photos, face swap", "11,000+ recognitions"], pal.ink, pal.accent, 13.5, 24, 0.6),
        _foot(svg, 36, 352, ["v2.0.0", "seiyuumatch.org"], pal.dim, int(repo.get("stars", 0))),
    )
    plate.close("04 / 09", corner="br")
    return svg.render()


def _rotate(point: tuple[float, float], center: tuple[float, float], degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    x, y = point[0] - center[0], point[1] - center[1]
    return (center[0] + x * math.cos(a) - y * math.sin(a), center[1] + x * math.sin(a) + y * math.cos(a))


def lerobot(data: dict) -> str:
    pal = LEROBOT
    svg = Svg(W, H, "LeRobot: merged upstream fix for asynchronous inference; ACT, pi0 and pi0.5 on a real arm")
    plate = Plate(svg, pal, rx=16)
    plate.open()
    vx, vy, vw, vh = 316, 22, 262, 336
    patina = svg.uid("patina")
    svg.define(
        f'<radialGradient id="{patina}" cx=".6" cy=".35" r=".8"><stop offset="0" stop-color="#1d3a33"/>'
        f'<stop offset="1" stop-color="{pal.panel}"/></radialGradient>'
    )
    svg.add(
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="12" fill="url(#{patina})" stroke="{pal.line}"/>',
        "".join(
            f'<circle cx="{cx}" cy="{cy}" r="3" fill="none" stroke="{pal.accent2}" opacity=".6"/>'
            for cx in (vx + 12, vx + vw - 12)
            for cy in (vy + 12, vy + vh - 12)
        ),
        f'<path d="M{vx + 20} 322H{vx + vw - 20}" stroke="{pal.accent}" stroke-width="1" stroke-dasharray="3 5" opacity=".5"/>',
    )
    shoulder, elbow, wrist, tip = (424, 292), (378, 204), (462, 152), (488, 186)
    reach = (6, 50, -20)
    # Where the fingertips land at full reach; the cube waits there.
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
        ".j1,.j2,.j3,.g1,.g2{transform-box:view-box;animation-duration:8s;animation-iteration-count:infinite;"
        "animation-timing-function:cubic-bezier(.45,0,.3,1);animation-delay:1.5s;animation-fill-mode:both}",
        ".j1{animation-name:j1}.j2{animation-name:j2}.j3{animation-name:j3}.g1{animation-name:grip}.g2{animation-name:grip2}",
        "@keyframes chunk{0%,100%{transform:scaleY(.35)}50%{transform:scaleY(1)}}",
        ".chunk{animation:chunk 1.8s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 100%}",
    )

    def link(a: tuple[float, float], b: tuple[float, float]) -> str:
        d = f"M{num(a[0])} {num(a[1])}L{num(b[0])} {num(b[1])}"
        return (
            f'<path d="{d}" stroke="{pal.accent}" stroke-width="26" stroke-linecap="round"/>'
            f'<path d="{d}" stroke="#163029" stroke-width="22.5" stroke-linecap="round"/>'
            f'<path d="{d}" stroke="{pal.accent}" stroke-width="1.2" stroke-dasharray="2 6" stroke-linecap="round" opacity=".75"/>'
        )

    def joint(c: tuple[float, float]) -> str:
        return (
            f'<circle cx="{num(c[0])}" cy="{num(c[1])}" r="12" fill="{pal.bg}" stroke="{pal.accent2}" stroke-width="2"/>'
            f'<circle cx="{num(c[0])}" cy="{num(c[1])}" r="3.5" fill="{pal.accent2}"/>'
        )

    fx, fy = tip
    fingers = (
        f'<g class="g1" style="transform-origin:{fx}px {fy}px"><path d="M{fx} {fy}l-11 6v16" fill="none" stroke="{pal.accent}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
        f'<g class="g2" style="transform-origin:{fx}px {fy}px"><path d="M{fx} {fy}l11 6v16" fill="none" stroke="{pal.accent}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/></g>'
    )
    arm = (
        f'<g class="j1" style="transform-origin:{shoulder[0]}px {shoulder[1]}px">{link(shoulder, elbow)}'
        f'<g class="j2" style="transform-origin:{elbow[0]}px {elbow[1]}px">{link(elbow, wrist)}'
        f'<g class="j3" style="transform-origin:{wrist[0]}px {wrist[1]}px">{link(wrist, tip)}{fingers}{joint(wrist)}</g>'
        f"{joint(elbow)}</g>{joint(shoulder)}</g>"
    )
    svg.add(
        f'<g class="fade" {delay(0.4)}>'
        f'<rect x="{num(cube_x)}" y="{num(cube_y)}" width="26" height="26" rx="2" fill="{pal.accent2}" fill-opacity=".14" stroke="{pal.accent2}" stroke-width="1.8"/>'
        f'<path d="M398 322V306Q398 298 406 298H442Q450 298 450 306V322" fill="{pal.panel}" stroke="{pal.accent}" stroke-width="1.6"/>'
        f"{arm}</g>",
        # Camera and its view of the cube.
        f'<g class="fade" {delay(0.8)}><rect x="526" y="52" width="30" height="20" rx="3" fill="{pal.bg}" stroke="{pal.accent}" stroke-width="1.4"/>'
        f'<circle cx="541" cy="62" r="5" fill="none" stroke="{pal.accent2}" stroke-width="1.4"/>'
        f'<path d="M532 74L{num(cube_x - 6)} {num(cube_y)}M550 74L{num(cube_x + 28)} {num(cube_y)}" stroke="{pal.accent}" stroke-width="1" stroke-dasharray="3 5" opacity=".55"/></g>',
    )
    bars = "".join(
        f'<rect class="chunk" style="animation-delay:-{num(k * 0.17)}s" x="{334 + k * 9}" y="58" width="5" height="22" rx="1.5" fill="{pal.accent}" opacity=".85"/>'
        for k in range(10)
    )
    svg.add(f'<g class="fade" {delay(0.9)}>' + svg.text(334, 48, "ACTION CHUNK", "mono-b", 10, pal.dim, tracking=1.8) + bars + "</g>")
    svg.add(
        kicker(svg, 36, 58, "ROBOT LEARNING  ·  UPSTREAM", pal.accent, size=12),
        _title(svg, 33, 122, "LeRobot", 56, pal.ink),
        f'<g class="rise" {delay(0.3)}>' + svg.text(36, 158, "merged into huggingface/lerobot", "italic", 21, "#bcd3ca") + "</g>",
        bullet_lines(svg, 36, 214, ["PR #2792, async inference", "actions to client_device", "ACT, π0, π0.5 on a real arm"], pal.ink, pal.accent2, 13, 27, 0.55),
        _foot(svg, 36, 350, [f"merged {short_date('2026-01-20T14:17:38Z')}"], pal.dim),
    )
    plate.close("05 / 09", corner="tl")
    return svg.render()


def hball(data: dict) -> str:
    pal = HBALL
    svg = Svg(W, H, "H_ball and servo: electronics design contest builds, MaixCAM vision feeding STM32 control")
    plate = Plate(svg, pal, rx=16)
    plate.open()
    hatch = svg.uid("hatch")
    svg.define(
        f'<pattern id="{hatch}" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<path d="M0 0V7" stroke="#183026" stroke-width="2.2"/></pattern>'
    )
    svg.add(f'<rect x="300" y="0" width="300" height="{H}" fill="url(#{hatch})" opacity=".55"/>')
    rng = random.Random(25)
    svg.add(
        "".join(
            f'<circle cx="{num(rng.uniform(310, 590))}" cy="{num(rng.uniform(14, 366))}" r="2.6" fill="{pal.bg}" stroke="{pal.accent}" stroke-opacity=".35"/>'
            for _ in range(26)
        )
    )
    traces = [
        "M416 84H452L486 118V150",  # camera → MCU (UART)
        "M448 210H404L366 248V252",  # MCU → servo
        "M506 226V250L520 264V270",  # MCU → IMU
        "M366 124V140L388 162H448",  # camera power / sync
        "M524 170H560V312H540",  # MCU → track sensor
    ]
    svg.style(
        "@keyframes packet{from{stroke-dashoffset:0}to{stroke-dashoffset:-112}}",
        ".packet{stroke-dasharray:7 105;animation:packet 2.6s linear infinite}",
        "@keyframes swing{0%,100%{transform:rotate(-32deg)}50%{transform:rotate(32deg)}}",
        ".swing{animation:swing 3.2s ease-in-out infinite;transform-box:view-box;transform-origin:366px 280px}",
        "@keyframes roll{0%,100%{transform:translateX(0)}50%{transform:translateX(74px)}}",
        ".rollball{animation:roll 3.2s ease-in-out infinite}",
    )
    svg.add(
        f'<g fill="none" stroke="{pal.accent}" stroke-width="2.4" stroke-linejoin="round" opacity=".55">'
        + "".join(f'<path d="{d}"/>' for d in traces)
        + "</g>",
        f'<g fill="none" stroke="#f6dc98" stroke-width="2.6" stroke-linecap="round">'
        + "".join(f'<path class="packet" style="animation-delay:-{num(k * 0.7)}s" d="{d}"/>' for k, d in enumerate(traces))
        + "</g>",
    )
    svg.add(
        # MaixCAM module.
        f'<rect x="316" y="44" width="100" height="80" rx="6" fill="#0d1612" stroke="{pal.accent}" stroke-width="1.4"/>'
        f'<circle cx="366" cy="82" r="23" fill="none" stroke="{pal.accent}" stroke-width="1.4"/>'
        '<circle cx="366" cy="82" r="14" fill="#04070a"/><circle cx="361" cy="77" r="3.5" fill="#f6dc98" opacity=".7"/>'
        + svg.text(366, 140, "MAIXCAM", "mono-b", 10.5, pal.ink, "middle", tracking=1.6)
        # MCU.
        + f'<g transform="translate(0 -1)" fill="{pal.accent}" opacity=".85">' + "".join(
            f'<rect x="{num(452 + k * 7.6)}" y="143" width="3" height="7"/><rect x="{num(452 + k * 7.6)}" y="227" width="3" height="7"/>'
            f'<rect x="441" y="{num(154 + k * 7.6)}" width="7" height="3"/><rect x="524" y="{num(154 + k * 7.6)}" width="7" height="3"/>'
            for k in range(9)
        ) + "</g>"
        + f'<rect x="448" y="150" width="76" height="76" rx="3" fill="#0a0f0c" stroke="#33463b"/>'
        + f'<circle cx="458" cy="160" r="2.5" fill="{pal.dim}"/>'
        + svg.text(486, 192, "STM32", "mono-b", 13, pal.ink, "middle", tracking=1)
        + svg.text(486, 210, "F103", "mono", 10.5, pal.dim, "middle")
        # Servo with a sweeping horn.
        + f'<rect x="324" y="252" width="84" height="56" rx="6" fill="#0d1612" stroke="{pal.accent}" stroke-width="1.4"/>'
        + f'<g class="swing"><path d="M366 280L366 254" stroke="{pal.ink}" stroke-width="5" stroke-linecap="round"/></g>'
        + f'<circle cx="366" cy="280" r="8" fill="#0d1612" stroke="{pal.ink}" stroke-width="1.6"/>'
        + svg.text(366, 326, "SERVO", "mono-b", 10.5, pal.ink, "middle", tracking=1.6)
        # IMU.
        + f'<rect x="500" y="270" width="40" height="30" rx="3" fill="#0a0f0c" stroke="#33463b"/>'
        + svg.text(520, 290, "JY61", "mono-b", 10, pal.ink, "middle")
        # The ball on its track.
        + f'<path d="M444 338H566" stroke="{pal.dim}" stroke-width="5" stroke-linecap="round" opacity=".5"/>'
        + f'<g class="rollball"><circle cx="460" cy="330" r="7" fill="#e9eef2" opacity=".9"/><circle cx="458" cy="328" r="2" fill="#fff"/></g>'
        + svg.text(426, 76, "UART", "mono-b", 9.5, pal.accent, tracking=1.4)
    )
    svg.add(
        f'<path d="M24 24H292V356H24Z" fill="none" stroke="{pal.ink}" stroke-opacity=".18" stroke-dasharray="2 5"/>',
        svg.text(36, 44, "U1", "mono-b", 10, pal.dim, tracking=1),
        kicker(svg, 40, 76, "NUEDC  ·  2026 H  /  2025 E", pal.accent, size=12),
        _title(svg, 38, 136, "H_ball", 54, pal.ink),
        _title(svg, 40, 180, "+ servo", 38, "#cfc9b3", 0.25, "italic"),
        bullet_lines(svg, 40, 230, ["MaixCAM: YOLO11n, α-β filter", "latency-compensated UART", "STM32 gimbal: PID, IMU"], pal.ink, pal.accent, 13, 26, 0.55),
        f'<g class="fade" {delay(1.0)}>' + svg.text(40, 334, "PROVINCIAL 2ND  ·  3RD PRIZE", "mono-b", 11.5, pal.accent, tracking=1.6) + "</g>",
    )
    plate.close("06 / 09", corner="tr")
    return svg.render()


def nailong(data: dict) -> str:
    pal = NAILONG
    repo = data["repos"].get("naiLongRacing", {})
    amber = pal.accent
    svg = Svg(W, H, "naiLongRacing: a pseudo-3D racer in plain C on openvela, drawn straight to the framebuffer")
    plate = Plate(svg, pal, rx=16)
    plate.open()
    bx, by, bw, bh = 300, 28, 278, 258
    sx, sy, sw, sh = 312, 40, 254, 234
    screen, sky, glare, lines = svg.uid("screen"), svg.uid("sky"), svg.uid("glare"), svg.uid("lines")
    svg.define(
        f'<clipPath id="{screen}"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="14"/></clipPath>',
        f'<linearGradient id="{sky}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2b1806"/>'
        '<stop offset="1" stop-color="#140b04"/></linearGradient>',
        f'<radialGradient id="{glare}" cx=".3" cy=".2" r=".9"><stop offset="0" stop-color="#ffcf8a" stop-opacity=".1"/>'
        '<stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>',
        f'<pattern id="{lines}" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1.2" fill="#000" opacity=".5"/></pattern>',
    )
    horizon, bottom, cx = 136, sy + sh, sx + sw / 2

    def road_x(y: float) -> tuple[float, float]:
        t = (y - horizon) / (bottom - horizon)
        half = 7 + t * (sw * 0.58)
        return cx - half, cx + half

    bands_a, bands_b = [], []
    zs = [1 + k * 0.55 for k in range(16)]
    ys = [horizon + (bottom - horizon) / z for z in zs]
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
        "@keyframes flipa{0%,49.9%{opacity:1}50%,100%{opacity:.08}}",
        "@keyframes flipb{0%,49.9%{opacity:.08}50%,100%{opacity:1}}",
        ".flipa{animation:flipa .34s step-end infinite}.flipb{animation:flipb .34s step-end infinite}",
        "@keyframes sway{0%,100%{transform:translateX(-14px)}50%{transform:translateX(14px)}}",
        ".sway{animation:sway 3.4s ease-in-out infinite}",
        "@keyframes gauge{0%,100%{transform:scaleX(.62)}50%{transform:scaleX(.94)}}",
        ".gauge{animation:gauge 2.6s ease-in-out infinite;transform-box:fill-box;transform-origin:0 50%}",
    )
    mountains = "M312 136L336 116L352 126L378 102L404 124L420 114L446 130L472 108L500 124L520 112L546 128L566 120V136Z"
    car_x, car_y = cx, bottom - 30
    car = (
        f'<g class="sway"><rect x="{num(car_x - 22)}" y="{num(car_y)}" width="44" height="14" rx="3" fill="{amber}"/>'
        f'<rect x="{num(car_x - 14)}" y="{num(car_y - 10)}" width="28" height="12" rx="3" fill="#7a4a12"/>'
        f'<rect x="{num(car_x - 11)}" y="{num(car_y - 8)}" width="22" height="7" rx="2" fill="#2a1806"/>'
        f'<rect x="{num(car_x - 26)}" y="{num(car_y + 8)}" width="9" height="10" rx="2" fill="#2a1806"/>'
        f'<rect x="{num(car_x + 17)}" y="{num(car_y + 8)}" width="9" height="10" rx="2" fill="#2a1806"/>'
        f'<rect x="{num(car_x - 18)}" y="{num(car_y + 3)}" width="6" height="3" fill="#fff3d6"/>'
        f'<rect x="{num(car_x + 12)}" y="{num(car_y + 3)}" width="6" height="3" fill="#fff3d6"/></g>'
    )
    svg.add(
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="22" fill="#1e150b" stroke="{pal.line}" stroke-width="1.5"/>',
        f'<g clip-path="url(#{screen})"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#{sky})"/>'
        f'<circle cx="500" cy="128" r="24" fill="{amber}" opacity=".22"/>'
        f'<path d="M476 120H524M478 126H522M482 132H518" stroke="#1d1207" stroke-width="2.4"/>'
        f'<path d="{mountains}" fill="{pal.accent2}" opacity=".32"/>'
        f'<path d="M{num(tl)} {horizon}L{num(tr)} {horizon}L{num(br)} {bottom}L{num(bl)} {bottom}Z" fill="#1c1107"/>'
        f'<path d="M{num(tl)} {horizon}L{num(bl)} {bottom}M{num(tr)} {horizon}L{num(br)} {bottom}" stroke="{amber}" stroke-width="1.2" opacity=".7"/>'
        f'<path class="flipa" d="{"".join(bands_a)}" fill="{amber}"/>'
        f'<path class="flipb" d="{"".join(bands_b)}" fill="{amber}" opacity=".08"/>'
        f"{car}"
        + svg.text(326, 64, "LAP 1/3", "mono-b", 11, amber, tracking=1.4)
        + f'<rect x="488" y="55" width="62" height="7" rx="2" fill="none" stroke="{amber}" stroke-width="1" opacity=".7"/>'
        + f'<rect class="gauge" x="490" y="57" width="58" height="3" fill="{amber}"/>'
        + f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#{lines})" opacity=".55"/>'
        + f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#{glare})"/></g>',
        f'<g class="fade" {delay(0.8)}>'
        + svg.text(bx + bw / 2, 312, "R528  ·  NUTTX  ·  SPI LCD", "mono-b", 11, pal.dim, "middle", tracking=2)
        + "</g>",
    )
    svg.add(
        kicker(svg, 36, 58, "OPENVELA  ·  EMBEDDED GAME", amber, size=12),
        _title(svg, 33, 120, "naiLong", 54, pal.ink),
        _title(svg, 33, 170, "Racing", 54, pal.ink, 0.25),
        bullet_lines(svg, 36, 222, ["pseudo-3D racer in plain C", "framebuffer → SPI LCD", "SDL twin for the desktop"], pal.ink, pal.accent2, 13, 27, 0.55),
        _foot(svg, 36, 350, [f"updated {month_year(repo.get('pushed_at'))}"], pal.dim, int(repo.get("stars", 0))),
    )
    plate.close("07 / 09", corner="br")
    return svg.render()


def fpga(data: dict) -> str:
    pal = FPGA
    repo = data["repos"].get("fpga_cpu", {})
    svg = Svg(W, H, "FPGA RISC-V CPU: RV32IM, five-stage pipeline, 50 MHz on a Spartan-6 board")
    plate = Plate(svg, pal, rx=16)
    plate.open()
    sx, sy, sw, sh = 22, 22, 556, 182
    scope, phosphor = svg.uid("scope"), svg.uid("phosphor")
    svg.define(
        f'<clipPath id="{scope}"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="12"/></clipPath>',
        f'<radialGradient id="{phosphor}" cx=".5" cy=".5" r=".7"><stop offset="0" stop-color="#2a1610"/>'
        '<stop offset="1" stop-color="#0c0706"/></radialGradient>',
    )
    grid = "".join(f"M{num(sx + k * sw / 10)} {sy}V{sy + sh}" for k in range(1, 10))
    grid += "".join(f"M{sx} {num(sy + k * sh / 6)}H{sx + sw}" for k in range(1, 6))
    ticks = "".join(f"M{num(sx + k * sw / 50)} {num(sy + sh / 2 - 3)}v6" for k in range(1, 50))
    period, travel = 44, 704
    x0, x1 = sx - period, sx + sw + travel
    high, low = 62, 92
    clock = [f"M{x0} {low}"]
    x = x0
    while x < x1:
        clock.append(f"H{x + period / 2}V{high}H{x + period}V{low}")
        x += period
    mnemonics = ["ADDI", "LW", "BEQ", "MUL", "SW", "JAL", "XOR", "LUI"]
    bus, labels = [], []
    seg = 88
    x = sx - seg
    k = 0
    while x < x1:
        y0, y1 = 140, 162
        bus.append(f"M{x + 6} {y0}L{x + seg - 6} {y0}L{x + seg} {(y0 + y1) / 2}L{x + seg - 6} {y1}L{x + 6} {y1}L{x} {(y0 + y1) / 2}Z")
        labels.append(svg.text(x + seg / 2, 155.5, mnemonics[k % len(mnemonics)], "mono-b", 11, pal.accent2, "middle", tracking=1))
        x += seg
        k += 1
    svg.style(
        f"@keyframes scroll{{to{{transform:translateX(-{travel}px)}}}}",
        ".scroll{animation:scroll 19.2s linear infinite}",
        "@keyframes stage{0%{transform:translateX(0)}20%{transform:translateX(53px)}40%{transform:translateX(106px)}"
        "60%{transform:translateX(159px)}80%,100%{transform:translateX(212px)}}",
        ".stage{animation:stage 3s step-end infinite}",
    )
    svg.add(
        f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="12" fill="url(#{phosphor})" stroke="{pal.line}"/>',
        f'<g clip-path="url(#{scope})"><path d="{grid}" stroke="{pal.line}" stroke-dasharray="1 4"/>'
        f'<path d="{ticks}" stroke="{pal.line}"/>'
        f'<g class="scroll"><path d="{"".join(clock)}" fill="none" stroke="{pal.accent}" stroke-width="5" opacity=".18"/>'
        f'<path d="{"".join(clock)}" fill="none" stroke="#ffb48c" stroke-width="1.6"/>'
        f'<path d="{"".join(bus)}" fill="none" stroke="{pal.accent2}" stroke-width="1.3" opacity=".8"/>{"".join(labels)}</g>'
        + "</g>",
        svg.text(sx + 14, sy + 22, "CH1  CLK  50 MHz", "mono-b", 11, pal.accent, tracking=1.2),
        svg.text(sx + sw - 14, sy + 22, "FMAX 51.68 MHz", "mono-b", 11, pal.accent2, "end", tracking=1.2),
        svg.text(sx + 14, sy + sh - 12, "CH2  INSTR", "mono-b", 11, pal.accent2, tracking=1.2),
    )
    stages = ["IF", "ID", "EX", "MEM", "WB"]
    px0, py0, bw, gap = 320, 262, 44, 9
    boxes = "".join(
        f'<rect x="{px0 + k * (bw + gap)}" y="{py0}" width="{bw}" height="30" rx="4" fill="{pal.panel}" stroke="{pal.line}" stroke-width="1.3"/>'
        + svg.text(px0 + k * (bw + gap) + bw / 2, py0 + 20, name, "mono-b", 11.5, pal.ink, "middle", tracking=0.6)
        for k, name in enumerate(stages)
    )
    ex, mem = px0 + 2 * (bw + gap) + bw / 2, px0 + 3 * (bw + gap) + bw / 2
    svg.add(
        f'<g class="fade" {delay(0.6)}>'
        + svg.text(px0, 248, "5-STAGE PIPELINE", "mono-b", 10.5, pal.dim, tracking=1.8)
        + boxes
        + f'<rect class="stage" x="{px0 + 4}" y="{py0 + 25}" width="{bw - 8}" height="3" rx="1.5" fill="{pal.accent}"/>'
        + f'<path d="M{mem} {py0 + 32}V{py0 + 44}H{ex}V{py0 + 34}" fill="none" stroke="{pal.accent2}" stroke-width="1.2" stroke-dasharray="3 3"/>'
        + f'<path d="M{ex - 4} {py0 + 38}L{ex} {py0 + 33}L{ex + 4} {py0 + 38}" fill="none" stroke="{pal.accent2}" stroke-width="1.2"/>'
        + svg.text(px0 + 256, py0 + 52, "FORWARD", "mono-b", 9.5, pal.dim, "end", tracking=1.4)
        + svg.text(px0, 336, f"17 RTL regressions  ·  {month_year(repo.get('pushed_at'))}", "mono", 12.5, pal.dim)
        + "</g>"
    )
    svg.add(
        kicker(svg, 36, 244, "RISC-V  ·  SPARTAN-6", pal.accent, size=12),
        _title(svg, 33, 298, "FPGA CPU", 50, pal.ink),
        f'<g class="fade" {delay(0.6)}>'
        + svg.text(36, 328, "RV32IM · 2-bit BHT · I-cache", "mono", 12.5, "#d9c4b6")
        + svg.text(36, 350, "SDRAM · UART shell · MLP demo", "mono", 12.5, "#d9c4b6")
        + "</g>",
    )
    plate.close("08 / 09", corner="br")
    return svg.render()


PRIZE_ROWS = [
    ("2026", "RoboMaster University League", "National 2nd"),
    ("2026", "Mathematical Modeling Contest", "National 2nd"),
    ("2026", "Electronics Design Contest · H", "Provincial 2nd"),
    ("2025", "Electronics Design Contest · E", "Provincial 3rd"),
]


def prizes(data: dict) -> str:
    pal = PRIZES
    ink, rose, paper = "#2a2124", "#a3566a", pal.accent3
    svg = Svg(W, H, "Prizes: RoboMaster University League and mathematical modeling national second prizes; electronics design contest provincial prizes")
    plate = Plate(svg, pal, rx=16)
    plate.open()
    rosette = "".join(
        f'<ellipse cx="300" cy="190" rx="300" ry="96" transform="rotate({k * 7.5} 300 190)"/>' for k in range(24)
    )
    svg.add(f'<g fill="none" stroke="{pal.accent}" stroke-width=".8" opacity=".09">{rosette}</g>')
    sheet = torn_rect(44, 40, 512, 296, 2.4, seed=2026, edges="lrtb")
    svg.add(
        f'<g transform="rotate(-1.2 300 190)">'
        f'<path d="{sheet}" transform="translate(4 6)" fill="#000" opacity=".45"/>'
        f'<path d="{sheet}" fill="{paper}"/>'
        + grain(svg, 40, 36, 520, 304, 0.9)
        + f'<rect x="58" y="54" width="484" height="268" fill="none" stroke="{rose}" stroke-width="1" opacity=".55"/>'
        f'<rect x="62" y="58" width="476" height="260" fill="none" stroke="{rose}" stroke-width=".6" opacity=".45"/>'
        + f'<g class="rise" {delay(0.2)}>'
        + svg.text(80, 104, "Prizes", "serif", 38, ink)
        + svg.text(520, 100, "BUPT  ·  2025 – 2026", "mono-b", 11, rose, "end", tracking=1.8)
        + "</g>"
        + f'<path class="draw" {delay(0.4)} d="M80 118H520" pathLength="1" stroke="{rose}" stroke-width="1.2"/>'
    )
    for i, (year, name, level) in enumerate(PRIZE_ROWS):
        y = 160 + i * 42
        name_end = 128 + measure(name, "serif-m", 21)
        level_start = 520 - measure(level, "italic", 20)
        leader = f'<path d="M{num(name_end + 10)} {y - 4}H{num(level_start - 10)}" stroke="{rose}" stroke-width="1.4" stroke-dasharray="1 5" stroke-linecap="round" opacity=".55"/>'
        svg.add(
            f'<g class="rise" {delay(0.45 + i * 0.12)}>'
            + svg.text(80, y, year, "mono-b", 12, "#8a6a71", tracking=1)
            + svg.text(128, y, name, "serif-m", 21, ink)
            + leader
            + svg.text(520, y, level, "italic", 20, rose, "end")
            + "</g>"
        )
    svg.add("</g>")
    svg.style(
        "@keyframes sheen{0%,100%{opacity:.15}50%{opacity:.45}}",
        ".sheen{animation:sheen 5s ease-in-out infinite}",
    )
    sx, sy = 526, 316
    svg.add(
        f'<g class="fade" {delay(1.0)}>'
        f'<circle cx="{sx + 3}" cy="{sy + 4}" r="31" fill="#000" opacity=".4"/>'
        f'<path d="M{sx - 31} {sy}Q{sx - 33} {sy - 20} {sx - 18} {sy - 28}Q{sx} {sy - 36} {sx + 18} {sy - 28}Q{sx + 33} {sy - 18} {sx + 31} {sy}'
        f'Q{sx + 33} {sy + 20} {sx + 18} {sy + 28}Q{sx} {sy + 36} {sx - 18} {sy + 28}Q{sx - 33} {sy + 18} {sx - 31} {sy}Z" fill="#8f3a4c"/>'
        f'<circle cx="{sx}" cy="{sy}" r="22" fill="#a24658" stroke="#7a2c3c" stroke-width="2"/>'
        f'<g opacity=".75">{seal(sx, sy, 18, "#d68a99", 0.8)}</g>'
        f'<ellipse class="sheen" cx="{sx - 8}" cy="{sy - 12}" rx="12" ry="5" fill="#fff" transform="rotate(-30 {sx - 8} {sy - 12})"/>'
        "</g>"
    )
    plate.close("09 / 09", corner="bl")
    return svg.render()
