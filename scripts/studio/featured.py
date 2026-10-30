"""The three full-width plates: AutoKeeper, CompSkill and the deep learning course."""

from __future__ import annotations

import random

from .data import short_date
from .svg import SRC, Svg, cap_height, data_uri, delay, fit, measure, num, wrap
from .theme import (
    AUTOKEEPER,
    COMPSKILL,
    DEEP,
    Plate,
    arrow,
    bullet_lines,
    grain,
    kicker,
    seal,
    sketch_line,
    sketch_loop,
    star,
    torn_rect,
)

AK_FRAMES = [
    ("title", "TITLE SCREEN"),
    ("library", "INVESTIGATION"),
    ("map", "TOWN MAP"),
    ("combat", "COMBAT"),
    ("styles", "PICTURE STYLES"),
]
AK_LOOP = 25  # seconds; five frames of five seconds


def crossfade(name: str, count: int, index: int, fade: float = 1.6) -> str:
    """Keyframes that show frame `index` of `count` and cross-fade at the seams."""
    seg = 100 / count
    s, e = index * seg, (index + 1) * seg
    if index == 0:
        stops = [(0, 1), (e - fade, 1), (e + fade, 0), (100 - fade, 0), (100, 1)]
    elif index == count - 1:
        stops = [(0, 0), (s - fade, 0), (s + fade, 1), (100 - fade, 1), (100, 0)]
    else:
        stops = [(0, 0), (s - fade, 0), (s + fade, 1), (e - fade, 1), (e + fade, 0), (100, 0)]
    return f"@keyframes {name}{{" + "".join(f"{num(p)}%{{opacity:{o}}}" for p, o in stops) + "}"


def meta_stars(svg: Svg, x: float, y: float, stars: int, color: str, size: float = 14) -> tuple[str, float]:
    """A drawn star and a count; returns the markup and the x after it."""
    r = size * 0.48
    out = star(x + r, y - cap_height("mono-b", size) / 2, r, color) + svg.text(x + 2 * r + 7, y, str(stars), "mono-b", size, color)
    return out, x + 2 * r + 7 + measure(str(stars), "mono-b", size)


def autokeeper(data: dict) -> str:
    pal = AUTOKEEPER
    w, h = 1200, 600
    svg = Svg(w, h, "AutoKeeper: play Call of Cthulhu 7th edition with an AI keeper, in the terminal or the browser")
    plate = Plate(svg, pal)
    plate.open()
    glow = svg.uid("glow")
    svg.define(
        f'<radialGradient id="{glow}" cx=".7" cy=".45" r=".65">'
        '<stop offset="0" stop-color="#3b1612" stop-opacity=".7"/>'
        f'<stop offset="1" stop-color="{pal.bg}" stop-opacity="0"/></radialGradient>'
    )
    svg.add(f'<rect width="{w}" height="{h}" fill="url(#{glow})"/>')
    svg.add(f'<g opacity=".17"><g class="spin" style="animation-duration:180s">{seal(386, 132, 104, pal.accent2)}</g></g>')

    x = 56
    svg.add(kicker(svg, x, 88, "CALL OF CTHULHU 7E  ·  OPEN SOURCE", pal.accent))
    size = fit("AutoKeeper", "serif", 94, 392)
    svg.add(f'<g class="rise" {delay(0.15)}>' + svg.text(x - 4, 172, "AutoKeeper", "serif", size, pal.ink) + "</g>")
    tagline = wrap("Play Call of Cthulhu with an AI keeper, in the terminal or the browser.", "italic", 27, 392)
    svg.add(f'<g class="rise" {delay(0.3)}>' + svg.lines(x, 218, tagline, 33, face="italic", size=27, fill="#cbbda4") + "</g>")
    bullets = [
        "LangGraph agents: keeper, NPCs, arbiter",
        "7e rules by the book, physics dice",
        "true-colour ASCII art, procedural music",
        "solo or online, terminal or browser",
    ]
    svg.add(bullet_lines(svg, x, 320, bullets, "#dccfb7", pal.accent2, size=15, leading=31, at=0.55))
    svg.add(
        f'<g class="fade" {delay(1.1)}>'
        + svg.text(x, 470, "DEEPSEEK · CLAUDE · CODEX · OLLAMA", "mono-b", 12, pal.dim, tracking=2.2)
        + "</g>"
    )

    release = data.get("release") or {}
    tag = release.get("tag", "")
    repo = data["repos"].get("autokeeper", {})
    meta = [f'<g class="fade" {delay(1.25)}>']
    cx = x
    if tag:
        pill = measure(tag, "mono-b", 14, 1) + 30
        meta.append(
            f'<rect x="{cx}" y="514" width="{num(pill)}" height="34" rx="17" fill="none" stroke="{pal.accent2}" stroke-opacity=".8"/>'
            + svg.text(cx + 15, 536, tag, "mono-b", 14, pal.accent2, tracking=1)
        )
        cx += pill + 16
        meta.append(svg.text(cx, 536, f"released {short_date(release.get('published_at'))}", "mono", 13, pal.dim))
        cx += measure(f"released {short_date(release.get('published_at'))}", "mono", 13) + 22
    stars_markup, _ = meta_stars(svg, cx, 536, int(repo.get("stars", 0)), pal.dim, 13)
    meta.append(stars_markup + "</g>")
    svg.add("".join(meta))

    # Film strip and projected screenshots.
    sx, sy, sw, sh = 476, 40, 690, 470
    ix, iy, iw, ih = 492, 90, 658, 370
    strip = svg.uid("strip")
    picture = svg.uid("picture")
    svg.define(
        f'<clipPath id="{strip}"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="8"/></clipPath>',
        f'<clipPath id="{picture}"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="3"/></clipPath>',
    )
    pitch = 26
    holes = "".join(
        f'<rect x="{hx}" y="{hy}" width="14" height="10" rx="2.5"/>'
        for hx in range(sx + 6, sx + sw + pitch * 6, pitch)
        for hy in (sy + 18, sy + sh - 28)
    )
    feed = "".join(
        f"{num(k * 20 + 18.6)}%{{transform:translateX({-k * pitch}px)}}{num(k * 20 + 20)}%{{transform:translateX({-(k + 1) * pitch}px)}}"
        for k in range(5)
    )
    svg.style(
        f"@keyframes feed{{0%{{transform:translateX(0)}}{feed}}}",
        f".feed{{animation:feed {AK_LOOP}s linear infinite}}",
        "@keyframes drift{0%,100%{transform:scale(1)}50%{transform:scale(1.045)}}",
        f".drift{{animation:drift {AK_LOOP}s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 50%}}",
        f"@keyframes roll{{from{{transform:translateY(0)}}to{{transform:translateY({ih + 90}px)}}}}",
        ".roll{animation:roll 7s linear infinite}",
    )
    svg.add(
        f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="8" fill="#070504" stroke="#2a1d19"/>',
        f'<g clip-path="url(#{strip})"><g class="feed" fill="#24191a">{holes}</g></g>',
    )
    frames = []
    for i, (name, _) in enumerate(AK_FRAMES):
        svg.style(crossfade(f"ak{i}", len(AK_FRAMES), i), f".ak{i}{{animation:ak{i} {AK_LOOP}s linear infinite}}")
        hidden = ' opacity="0"' if i else ""
        frames.append(
            f'<image class="ak{i}" href="{data_uri(SRC / "autokeeper" / f"{name}.jpg")}" x="{ix}" y="{iy}" '
            f'width="{iw}" height="{ih}" preserveAspectRatio="xMidYMid slice"{hidden}/>'
        )
    scan, band, vignette = svg.uid("scan"), svg.uid("band"), svg.uid("vignette")
    svg.define(
        f'<pattern id="{scan}" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1.5" fill="#000" opacity=".55"/></pattern>',
        f'<linearGradient id="{band}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#ffe9d0" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
        f'<radialGradient id="{vignette}" cx=".5" cy=".5" r=".72"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".62"/></radialGradient>',
    )
    svg.add(
        f'<g clip-path="url(#{picture})"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#000"/>'
        f'<g class="drift">{"".join(frames)}</g>'
        f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="url(#{scan})" opacity=".4"/>'
        f'<rect class="roll" x="{ix}" y="{iy - 90}" width="{iw}" height="90" fill="url(#{band})"/>'
        f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="url(#{vignette})"/></g>',
        f'<rect x="{ix + .5}" y="{iy + .5}" width="{iw - 1}" height="{ih - 1}" rx="3" fill="none" stroke="#000" stroke-opacity=".6"/>',
    )
    # Caption and progress, in step with the frames.
    for i, (_, label) in enumerate(AK_FRAMES):
        hidden = ' opacity="0"' if i else ""
        svg.add(
            f'<g class="ak{i}"{hidden}>'
            + svg.text(sx + 2, 553, f"{i + 1:02d} / {len(AK_FRAMES):02d}", "mono-b", 13, pal.accent, tracking=2)
            + svg.text(sx + 108, 553, label, "mono-b", 13, pal.ink, tracking=2.6)
            + "</g>"
        )
    bar_w, gap = 50, 8
    bx0 = sx + sw - len(AK_FRAMES) * bar_w - (len(AK_FRAMES) - 1) * gap
    for i in range(len(AK_FRAMES)):
        s, e = i * 20, (i + 1) * 20
        stops = f"0%,{s}%{{transform:scaleX(0)}}" + (
            "100%{transform:scaleX(1)}" if e >= 100 else f"{e}%,99.6%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}"
        )
        svg.style(
            f"@keyframes akp{i}{{{stops}}}",
            f".akp{i}{{animation:akp{i} {AK_LOOP}s linear infinite;transform-box:fill-box;transform-origin:0 50%}}",
        )
        bx = bx0 + i * (bar_w + gap)
        svg.add(
            f'<rect x="{bx}" y="547" width="{bar_w}" height="3" rx="1.5" fill="{pal.line}"/>'
            f'<rect class="akp{i}" x="{bx}" y="547" width="{bar_w}" height="3" rx="1.5" fill="{pal.accent}"/>'
        )
    plate.close("01 / 09", corner="tl")
    return svg.render()


def compskill(data: dict) -> str:
    pal = COMPSKILL
    ink, blue, red, lead = pal.ink, pal.accent2, pal.accent, "#6c665d"
    w, h = 1200, 640
    svg = Svg(w, h, "CompSkill: compiling execution experience for skill retrieval")
    sheet = torn_rect(10, 18, 1180, 604, 5.5, seed=29, edges="tb")
    clip, paper, dots = svg.uid("sheet"), svg.uid("paper"), svg.uid("dots")
    svg.define(
        f'<clipPath id="{clip}"><path d="{sheet}"/></clipPath>',
        f'<linearGradient id="{paper}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f1ebdf"/>'
        '<stop offset=".6" stop-color="#e8e0cf"/><stop offset="1" stop-color="#ddd3bf"/></linearGradient>',
        f'<pattern id="{dots}" width="24" height="24" patternUnits="userSpaceOnUse">'
        '<circle cx="12" cy="12" r="1" fill="#6f7f93" opacity=".3"/></pattern>',
    )
    svg.add(
        f'<path d="{sheet}" transform="translate(5 8)" fill="#000" opacity=".3"/>',
        f'<path d="{sheet}" fill="url(#{paper})"/>',
        f'<g clip-path="url(#{clip})">',
        f'<rect x="452" y="40" width="720" height="570" fill="url(#{dots})"/>',
        grain(svg, 0, 0, w, h, 0.85),
    )

    # Left column: title and results.
    x = 64
    svg.add(kicker(svg, x, 88, "PAPER  ·  CODE  ·  WEIGHTS", red))
    size = fit("CompSkill", "serif", 92, 356)
    svg.add(f'<g class="rise" {delay(0.15)}>' + svg.text(x - 4, 176, "CompSkill", "serif", size, ink) + "</g>")
    svg.add(
        f'<g class="rise" {delay(0.3)}>'
        + svg.lines(x, 222, ["Compiling execution experience", "for skill retrieval"], 34, face="italic", size=28, fill="#3a352e")
        + "</g>"
    )
    results = [
        ("79.8%", "TOOLQA HIT@1 · BASELINE 63.0", "GPT-5.5 executor"),
        ("70.9", "SKILLRET NDCG@10 · BASELINE 64.0", ""),
        ("8×", "SMALLER KEYS · 4096 → 512-D", ""),
    ]
    for i, (value, caption, _) in enumerate(results):
        y = 344 + i * 92
        width = measure(value, "serif", 54)
        svg.add(
            f'<g class="rise" {delay(0.7 + i * 0.18)}>'
            + svg.text(x - 2, y, value, "serif", 54, ink)
            + svg.text(x, y + 30, caption, "mono-b", 12, lead, tracking=1.6)
            + "</g>",
            f'<path class="draw" {delay(1.3 + i * 0.2)} d="{sketch_line(x - 4, y + 9, x + width + 10, y + 7, seed=i + 3, amp=1.6)}" '
            f'pathLength="1" fill="none" stroke="{red}" stroke-width="2.2" stroke-linecap="round" opacity=".85"/>',
        )
    svg.add(
        f'<path class="draw" {delay(0.4)} d="M430 64V588" pathLength="1" stroke="{blue}" stroke-width="1" '
        'stroke-dasharray="6 5" opacity=".45" fill="none"/>'
    )

    # Test-time path along the top: task → ① → ② → ③ → ④.
    flow = [("task", ""), ("top-10", "1"), ("score S", "2"), ("6 + ≤4", "3"), ("actor", "4")]
    widths = [measure(label, "serif-m", 22) + (32 if number else 30) for label, number in flow]
    left, right, y = 476, 1150, 108
    gap = (right - left - sum(widths)) / (len(flow) - 1)
    fx = left
    stations = []
    for i, ((label, number), width) in enumerate(zip(flow, widths)):
        parts = []
        if number:
            parts.append(
                f'<circle cx="{num(fx + 11)}" cy="{y - 7}" r="11" fill="none" stroke="{ink}" stroke-width="1.3"/>'
                + svg.text(fx + 11, y - 2.5, number, "mono-b", 12, ink, "middle")
            )
            parts.append(svg.text(fx + 30, y, label, "serif-m", 22, ink))
        else:
            parts.append(
                f'<path d="M{num(fx)} {y - 26}h{num(width)}v32h-{num(width - 22)}l-9 9v-9h-{num(13)}z" fill="#f6f1e6" '
                f'stroke="{ink}" stroke-width="1.3" stroke-linejoin="round"/>'
                + svg.text(fx + 14, y - 3, label, "italic", 22, ink)
            )
        stations.append(f'<g class="fade" {delay(0.5 + i * 0.15)}>' + "".join(parts) + "</g>")
        if i < len(flow) - 1:
            ax = fx + width + 8
            stations.append(arrow(ax, y - 7, ax + gap - 16, y - 7, ink, 1.3, 7, f'class="fade" {delay(0.6 + i * 0.15)}'))
        fx += width + gap
    svg.add(*stations)
    svg.style(
        "@keyframes probe{0%{transform:translateX(0);opacity:0}6%{opacity:1}70%{transform:translateX(650px);opacity:1}"
        "76%,100%{transform:translateX(650px);opacity:0}}",
        ".probe{animation:probe 8s cubic-bezier(.45,0,.55,1) 2.5s infinite both}",
    )
    svg.add(
        f'<path d="M482 130H1146" stroke="{blue}" stroke-width="1" stroke-dasharray="2 5" opacity=".55"/>',
        f'<circle class="probe" cx="484" cy="130" r="5" fill="{red}"/>',
    )

    # ① compact keys.
    def heading(xx: float, yy: float, number: str, text: str, at: float) -> str:
        return (
            f'<g class="fade" {delay(at)}><circle cx="{num(xx + 10)}" cy="{num(yy - 7)}" r="10" fill="none" stroke="{ink}" stroke-width="1.2"/>'
            + svg.text(xx + 10, yy - 2.6, number, "mono-b", 11, ink, "middle")
            + svg.text(xx + 28, yy, text, "serif-m", 21, ink)
            + "</g>"
        )

    svg.add(heading(476, 184, "1", "compact keys", 1.0))
    cells = "".join(
        f'<rect x="{476 + c * 9}" y="204" width="9" height="15" fill="#c9d5e8" stroke="{blue}" stroke-width=".9"/>' for c in range(16)
    )
    short = "".join(
        f'<rect x="{538 + c * 9}" y="290" width="9" height="15" fill="#c9d5e8" stroke="{blue}" stroke-width=".9"/>' for c in range(2)
    )
    svg.add(
        f'<g class="fade" {delay(1.1)}>{cells}'
        + svg.text(476, 240, "4096-d", "mono-b", 12, lead, tracking=0.6)
        + f'<path d="M524 248H572L560 270H536Z" fill="none" stroke="{ink}" stroke-width="1.3" stroke-linejoin="round"/>'
        + arrow(548, 222, 548, 244, ink, 1.2, 5)
        + arrow(548, 272, 547, 287, ink, 1.2, 5)
        + short
        + svg.text(562, 302, "512-d", "mono-b", 12, lead, tracking=0.6)
        + "</g>",
        f'<g class="fade" {delay(1.9)}>'
        + svg.text(476, 352, "×8 fewer", "italic", 21, red)
        + svg.text(476, 376, "coordinates", "italic", 21, red)
        + f'<path d="M560 340C590 336 600 322 590 310" fill="none" stroke="{red}" stroke-width="1.4"/>'
        + "</g>",
    )

    # ② KeyOpt calibration and the skill key.
    svg.add(heading(664, 184, "2", "KeyOpt calibration", 1.2))
    ox, oy = 690, 322
    svg.add(
        f'<g class="fade" {delay(1.4)}>'
        f'<circle cx="842" cy="240" r="28" fill="none" stroke="{blue}" stroke-width="1.1" stroke-dasharray="4 4"/>'
        + arrow(ox, oy, 772, 210, ink, 1.6, 9)
        + arrow(ox, oy, 840, 240, blue, 1.6, 9)
        + arrow(ox, oy, 826, 220, red, 1.6, 9)
        + svg.text(752, 206, "q", "italic", 22, ink)
        + svg.text(852, 268, "k⁰", "italic", 22, blue)
        + svg.text(818, 210, "k′", "italic", 22, red)
        + f'<circle cx="{ox}" cy="{oy}" r="3" fill="{ink}"/>'
        + svg.text(800, 298, "score change ≤ c", "italic", 19, lead)
        + "</g>"
    )
    key_cells = []
    for c in range(20):
        key_cells.append(
            f'<rect x="{664 + c * 13}" y="352" width="13" height="18" fill="#c9d5e8" stroke="{blue}" stroke-width=".9"/>'
        )
    svg.style(
        "@keyframes edit{0%,30%{opacity:.25}38%,62%{opacity:1}75%,100%{opacity:.25}}",
        ".edit{animation:edit 8s ease-in-out 2.5s infinite both}",
    )
    svg.add(
        f'<g class="fade" {delay(1.6)}>{"".join(key_cells)}'
        f'<rect class="edit" x="664" y="373" width="260" height="6" fill="{red}" opacity=".7"/>'
        f'<rect x="930" y="352" width="18" height="18" fill="#f3ddd5" stroke="{red}" stroke-width="1.1"/>'
        + svg.text(939, 366, "b", "italic", 17, red, "middle")
        + svg.text(664, 408, "key = [k⁰ + Δk ; b]", "serif-m", 22, ink)
        + "</g>",
        f'<g class="fade" {delay(2.1)}>' + svg.text(664, 436, "read with one inner product and a clip", "italic", 19, red) + "</g>",
    )

    # ③ experience hypergraph.
    svg.add(heading(978, 184, "3", "hypergraph", 1.4))
    nodes = [(996, 236), (1032, 214), (1050, 262), (1006, 290), (1092, 224), (1118, 270), (1080, 302)]
    blob_a = "M984 230C990 200 1040 196 1062 222C1080 246 1060 300 1022 302C990 304 978 262 984 230Z"
    blob_b = "M1040 252C1046 214 1100 198 1126 230C1140 262 1118 318 1080 314C1050 310 1036 284 1040 252Z"
    svg.add(
        f'<g class="fade" {delay(1.7)}>'
        f'<path d="{blob_a}" fill="{blue}" fill-opacity=".13" stroke="{blue}" stroke-width="1.1"/>'
        f'<path d="{blob_b}" fill="{red}" fill-opacity=".1" stroke="{red}" stroke-width="1.1"/>'
        f'<path d="M996 236L1032 214L1050 262L1006 290ZM1050 262L1092 224L1118 270L1080 302Z" fill="none" stroke="{ink}" stroke-width="1.1" opacity=".7"/>'
        + "".join(f'<circle cx="{nx}" cy="{ny}" r="4.5" fill="{ink}"/>' for nx, ny in nodes)
        + svg.text(978, 344, "attributed events", "mono-b", 12, lead, tracking=0.6)
        + svg.text(978, 364, "task · executor · version", "mono", 12, lead)
        + "</g>"
    )

    # Between rounds: publish ← fit ← filter ← record ← outcomes, fed by ④.
    svg.add(f'<g class="fade" {delay(2.0)}>' + svg.text(476, 486, "between rounds · support tasks only", "italic", 20, blue) + "</g>")
    steps = ["PUBLISH", "FIT", "FILTER", "RECORD", "OUTCOMES"]
    bw, bgap, by = 84, 13, 504
    svg.style(
        "@keyframes back{to{stroke-dashoffset:22}}",
        ".back{animation:back 1.6s linear infinite}",
    )
    for i, step in enumerate(steps):
        bx = 476 + i * (bw + bgap)
        svg.add(
            f'<g class="fade" {delay(2.1 + i * 0.08)}><rect x="{bx}" y="{by}" width="{bw}" height="32" rx="4" fill="#f6f1e6" stroke="{ink}" stroke-width="1.2"/>'
            + svg.text(bx + bw / 2, by + 21, step, "mono-b", 11.5, ink, "middle", tracking=1)
            + "</g>"
        )
        if i:
            svg.add(arrow(bx - 2, by + 16, bx - bgap + 3, by + 16, blue, 1.3, 5, f'class="fade" {delay(2.2 + i * 0.08)}'))
    svg.add(
        f'<path class="back" d="M{476 + 5 * (bw + bgap) + 30} {by + 16}H{476 + 5 * (bw + bgap) - bgap + 2}" stroke="{blue}" stroke-width="1.3" stroke-dasharray="5 6" fill="none"/>'
    )
    svg.add(heading(1000, 474, "4", "frozen actor", 1.8))
    for i, name in enumerate(["ToolQA", "AppWorld", "ALFWorld"]):
        wx, wy = 1004 + i * 12, 488 + i * 31
        svg.add(
            f'<g class="fade" {delay(1.9 + i * 0.1)}><rect x="{wx}" y="{wy}" width="124" height="38" rx="4" fill="#f6f1e6" stroke="{ink}" stroke-width="1.2"/>'
            f'<path d="M{wx} {wy + 10}H{wx + 124}" stroke="{ink}" stroke-width=".9"/>'
            + "".join(f'<circle cx="{wx + 8 + d * 7}" cy="{wy + 5}" r="1.7" fill="{ink}"/>' for d in range(3))
            + svg.text(wx + 10, wy + 26, name, "mono-b", 12, ink, tracking=0.4)
            + "</g>"
        )
    svg.add(f'<g class="fade" {delay(2.3)}>' + svg.text(476, 586, "the actor reads the original skill document only", "italic", 19, red) + "</g>")
    svg.add("</g>", f'<path d="{sheet}" fill="none" stroke="#c9bea8" stroke-width="1"/>')
    svg.add(svg.text(1150, 62, "02 / 09", "mono", 12, lead, "end", tracking=2.2))
    return svg.render()


def deep_learning(data: dict) -> str:
    pal = DEEP
    chalk, yellow, pink, blue = pal.ink, pal.accent, pal.accent2, pal.accent3
    w, h = 1200, 600
    svg = Svg(w, h, "From y = ax + b to MiniMind: an open deep learning textbook, implementation first")
    plate = Plate(svg, pal)
    plate.open()
    glow, grid, dust = svg.uid("glow"), svg.uid("grid"), svg.uid("dust")
    svg.define(
        f'<radialGradient id="{glow}" cx=".45" cy=".4" r=".7"><stop offset="0" stop-color="#21302a"/>'
        f'<stop offset="1" stop-color="{pal.bg}"/></radialGradient>',
        f'<pattern id="{grid}" width="30" height="30" patternUnits="userSpaceOnUse">'
        '<path d="M30 0H0V30" fill="none" stroke="#e9f2ec" stroke-opacity=".045"/></pattern>',
        f'<radialGradient id="{dust}"><stop offset="0" stop-color="#f4f1e8" stop-opacity=".07"/>'
        '<stop offset="1" stop-color="#f4f1e8" stop-opacity="0"/></radialGradient>',
    )
    svg.add(
        f'<rect width="{w}" height="{h}" fill="url(#{glow})"/>',
        f'<rect width="{w}" height="{h}" fill="url(#{grid})"/>',
        f'<ellipse cx="860" cy="140" rx="300" ry="90" fill="url(#{dust})" transform="rotate(-8 860 140)"/>',
        f'<ellipse cx="300" cy="470" rx="340" ry="80" fill="url(#{dust})" transform="rotate(4 300 470)"/>',
    )
    chalk_dash = 'stroke-dasharray="19 2.5 7 1.8 26 3 11 2" stroke-linecap="round"'

    stars = int(data["repos"].get("quickly_access_to_deeplearning", {}).get("stars", 0))
    x = 56
    svg.add(kicker(svg, x, 88, "OPEN TEXTBOOK  ·  NUMPY → PYTORCH", yellow))
    first = "From "
    first_w = measure(first, "serif", 66)
    svg.add(
        f'<g class="rise" {delay(0.15)}>'
        + svg.text(x - 3, 168, first, "serif", 66, chalk)
        + svg.text(x - 3 + first_w, 168, "y = ax + b", "italic", 70, yellow)
        + "</g>",
        f'<g class="rise" {delay(0.3)}>' + svg.text(x - 3, 238, "to MiniMind", "serif", 66, chalk) + "</g>",
    )
    svg.add(
        f'<g class="fade" {delay(0.6)}>'
        + svg.text(x, 282, "DEEP LEARNING, ONE RUNNABLE EXERCISE AT A TIME", "mono-b", 13, pal.dim, tracking=2.2)
        + "</g>"
    )

    # The chalk note: adopted for a BUPT elective.
    svg.add(
        f'<g class="fade" {delay(1.0)}>'
        + svg.text(978, 128, "adopted as the textbook", "italic", 30, pink, "middle")
        + svg.text(978, 164, "for a BUPT elective course", "italic", 30, pink, "middle")
        + "</g>",
        f'<path class="draw" {delay(1.3)} d="{sketch_loop(978, 140, 176, 56, seed=7)}" pathLength="1" fill="none" '
        f'stroke="{pink}" stroke-width="2" opacity=".8" {chalk_dash}/>',
        f'<path class="draw" {delay(2.0)} d="M796 176C740 198 690 196 640 176" pathLength="1" fill="none" stroke="{pink}" stroke-width="2" opacity=".75"/>',
        f'<path class="fade" {delay(2.6)} d="M652 168L640 176L654 184" fill="none" stroke="{pink}" stroke-width="2" stroke-linecap="round" opacity=".75"/>',
        f'<g class="fade" {delay(1.6)}>'
        + svg.text(978, 228, "20 interactive demos · unit-tested exercises", "mono", 13.5, pal.dim, "middle")
        + "</g>",
    )

    panels = [
        (56, "BLOCK 1", "NumPy from scratch", "Linear · ReLU · backprop → MNIST"),
        (436, "BLOCK 2", "Convolution & ResNet", "im2col · BatchNorm → CIFAR-100"),
        (816, "BLOCK 3", "Transformer & MiniMind", "RoPE · GQA · SwiGLU · KV cache"),
    ]
    for i, (px, tag, title, body) in enumerate(panels):
        at = 1.2 + i * 0.35
        svg.add(
            f'<g class="fade" {delay(at)}>'
            f'<circle cx="{px + 12}" cy="{334}" r="12" fill="none" stroke="{chalk}" stroke-width="1.6" opacity=".85"/>'
            + svg.text(px + 12, 339, str(i + 1), "mono-b", 13, chalk, "middle")
            + svg.text(px + 34, 339, tag, "mono-b", 13, yellow, tracking=2.4)
            + svg.text(px, 512, title, "serif", 26, chalk)
            + svg.text(px, 540, body, "mono", 14, pal.dim)
            + "</g>"
        )
        if i:
            svg.add(
                f'<path class="draw" {delay(at + 0.2)} d="{sketch_line(px - 54, 404, px - 18, 402, seed=40 + i, amp=1)}" '
                f'pathLength="1" fill="none" stroke="{chalk}" stroke-width="2" opacity=".6"/>',
                f'<path class="fade" {delay(at + 0.6)} d="M{px - 26} 395L{px - 17} 402L{px - 27} 409" fill="none" stroke="{chalk}" '
                'stroke-width="2" stroke-linecap="round" opacity=".6"/>',
            )

    # Block 1: points and a line that keeps settling onto them.
    rng = random.Random(4)
    points = []
    for k in range(11):
        px = 92 + k * 25
        points.append((px, 452 - (px - 80) * 0.32 + rng.uniform(-13, 13)))
    svg.style(
        "@keyframes fitline{0%{transform:rotate(-16deg)}55%,85%{transform:rotate(0deg)}100%{transform:rotate(-16deg)}}",
        ".fitline{animation:fitline 7s cubic-bezier(.3,0,.2,1) 2s infinite both;transform-box:fill-box;transform-origin:50% 50%}",
    )
    svg.add(
        f'<path class="draw" {delay(1.3)} d="M74 360V462H372" pathLength="1" fill="none" stroke="{chalk}" stroke-width="1.8" opacity=".7" {chalk_dash}/>',
        f'<g class="fade" {delay(1.5)} fill="{chalk}">'
        + "".join(f'<circle cx="{num(px)}" cy="{num(py)}" r="3.4" opacity=".9"/>' for px, py in points)
        + "</g>",
        f'<g class="fade" {delay(1.8)}><path class="fitline" d="M84 {num(452 - 4 * .32)}L364 {num(452 - 284 * .32)}" stroke="{yellow}" stroke-width="2.6" stroke-linecap="round" fill="none"/></g>',
        f'<g class="fade" {delay(2.0)}>' + svg.text(300, 456, "loss → 0.042", "mono", 12, pal.dim, "end") + "</g>",
    )

    # Block 2: a 3×3 window sliding over a 6×6 input, filling a 4×4 output.
    cell, gx, gy, ox, oy = 16, 456, 358, 612, 382
    grid_cells = "".join(
        f'<rect x="{gx + c * cell}" y="{gy + r * cell}" width="{cell}" height="{cell}"/>' for r in range(6) for c in range(6)
    )
    positions = [(r, c) for r in range(4) for c in range(4)]
    slide = "".join(
        f"{num(k * 100 / 16)}%{{transform:translate({c * cell}px,{r * cell}px)}}" for k, (r, c) in enumerate(positions)
    )
    svg.style(
        f"@keyframes slide{{{slide}100%{{transform:translate(0,0)}}}}",
        ".slide{animation:slide 9.6s step-end 2.2s infinite both}",
    )
    outputs = []
    for k, (r, c) in enumerate(positions):
        start = k * 100 / 16
        svg.style(
            f"@keyframes out{k}{{0%{{opacity:.08}}{num(start)}%{{opacity:.08}}{num(start + 0.01)}%,99.9%{{opacity:.85}}100%{{opacity:.08}}}}",
            f".out{k}{{animation:out{k} 9.6s step-end 2.2s infinite both}}",
        )
        outputs.append(f'<rect class="out{k}" x="{ox + c * cell + 1}" y="{oy + r * cell + 1}" width="{cell - 2}" height="{cell - 2}" fill="{blue}"/>')
    svg.add(
        f'<g class="fade" {delay(1.7)}><g fill="none" stroke="{chalk}" stroke-width="1" opacity=".55">{grid_cells}</g>'
        f'<rect class="slide" x="{gx}" y="{gy}" width="{cell * 3}" height="{cell * 3}" fill="{yellow}" fill-opacity=".14" stroke="{yellow}" stroke-width="2"/>'
        + arrow(560, 406, 600, 406, chalk, 1.6, 6, 'opacity=".7"')
        + svg.text(580, 392, "im2col", "mono", 11.5, pal.dim, "middle")
        + f'<g fill="none" stroke="{chalk}" stroke-width="1" opacity=".55">'
        + "".join(f'<rect x="{ox + c * cell}" y="{oy + r * cell}" width="{cell}" height="{cell}"/>' for r in range(4) for c in range(4))
        + "</g>"
        + "".join(outputs)
        + "</g>"
    )

    # Block 3: the first chapter's equation as tokens, attended causally.
    tokens = ["y", "=", "a", "x", "+", "b"]
    tx0, ty, tw, tgap = 836, 440, 36, 13
    centers = [tx0 + k * (tw + tgap) + tw / 2 for k in range(len(tokens))]
    arcs, lights = [], []
    for q in range(1, len(tokens)):
        group = []
        for k in range(q):
            span = centers[q] - centers[k]
            group.append(f"M{num(centers[q])} {ty - 4}Q{num((centers[q] + centers[k]) / 2)} {num(ty - 10 - span * 0.42)} {num(centers[k])} {ty - 4}")
        arcs.append("".join(group))
        s, e = (q - 1) * 20, q * 20
        svg.style(
            f"@keyframes att{q}{{0%,{s}%{{opacity:0}}{s + 3}%,{e - 3}%{{opacity:1}}{e}%,100%{{opacity:0}}}}",
            f".att{q}{{animation:att{q} 10s ease-in-out 2.4s infinite both}}",
        )
        lights.append(
            f'<g class="att{q}" opacity="0"><path d="{"".join(group)}" fill="none" stroke="{yellow}" stroke-width="2"/>'
            f'<rect x="{num(centers[q] - tw / 2)}" y="{ty}" width="{tw}" height="30" rx="4" fill="{yellow}" fill-opacity=".16" stroke="{yellow}" stroke-width="1.8"/></g>'
        )
    svg.add(
        f'<g class="fade" {delay(2.0)}><path d="{"".join(arcs)}" fill="none" stroke="{chalk}" stroke-width="1.1" opacity=".22"/>'
        + "".join(
            f'<rect x="{num(cx - tw / 2)}" y="{ty}" width="{tw}" height="30" rx="4" fill="none" stroke="{chalk}" stroke-width="1.4" opacity=".75"/>'
            + svg.text(cx, ty + 21, tok, "mono-b", 15, chalk, "middle")
            for cx, tok in zip(centers, tokens)
        )
        + "".join(lights)
        + "</g>"
    )

    footer, fx = [], x
    star_markup, fx = meta_stars(svg, fx, 578, stars, yellow, 13)
    footer.append(star_markup)
    footer.append(svg.text(fx + 18, 578, "STARS  ·  HUGO SITE  ·  TESTS FOR GRADIENTS, SHAPES, CAUSAL MASKS", "mono", 12, pal.dim, tracking=1.4))
    svg.add(f'<g class="fade" {delay(2.4)}>' + "".join(footer) + "</g>")
    plate.close("03 / 09", corner="tr")
    return svg.render()
