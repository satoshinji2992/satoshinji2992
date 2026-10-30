"""The three full-width plates: AutoKeeper, CompSkill and the deep learning course."""

from __future__ import annotations

import random

from .data import long_date
from .svg import SRC, Svg, data_uri, delay, fit, measure, num, wrap
from .theme import (
    AUTOKEEPER,
    COMPSKILL,
    DEEP,
    FLICKER,
    GOLD,
    ROMAN,
    Plate,
    arrow,
    bullet_lines,
    grain,
    kicker,
    ornament_rule,
    seal,
    sketch_line,
    sketch_loop,
    star,
    torn_rect,
)

AK_FRAMES = [
    ("title", "the title screen"),
    ("library", "reading old papers in the library"),
    ("map", "the town map"),
    ("combat", "a fight, rolled by the rules"),
    ("styles", "four ways to draw a picture"),
]
AK_LOOP = 25  # seconds; five reels of five seconds


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


def handover(name: str, count: int, index: int, fade: float = 1.2) -> str:
    """Like crossfade, but the outgoing item is gone before the next one appears (for text)."""
    seg = 100 / count
    s, e = index * seg, (index + 1) * seg
    if index == 0:
        stops = [(0, 1), (e - 2 * fade, 1), (e - fade, 0), (100, 0)]
    else:
        stops = [(0, 0), (s, 0), (s + fade, 1), (e - 2 * fade, 1), (e - fade, 0), (100, 0)]
    return f"@keyframes {name}{{" + "".join(f"{num(p)}%{{opacity:{o}}}" for p, o in stops) + "}"


def meta_stars(svg: Svg, x: float, y: float, stars: int, color: str, size: float = 18, face: str = "italic") -> tuple[str, float]:
    """A drawn star and a count; returns the markup and the x after it."""
    r = size * 0.34
    out = star(x + r, y - size * 0.3, r, color) + svg.text(x + 2 * r + 6, y, str(stars), face, size, color)
    return out, x + 2 * r + 6 + measure(str(stars), face, size)


def autokeeper(data: dict) -> str:
    pal = AUTOKEEPER
    w, h = 1200, 600
    svg = Svg(w, h, "AutoKeeper: play Call of Cthulhu, seventh edition, with an AI keeper, in the terminal or the browser")
    plate = Plate(svg, pal)
    plate.open()
    glow = svg.uid("glow")
    svg.define(
        f'<radialGradient id="{glow}" cx=".68" cy=".46" r=".62">'
        '<stop offset="0" stop-color="#4a1d14" stop-opacity=".7"/>'
        f'<stop offset="1" stop-color="{pal.bg}" stop-opacity="0"/></radialGradient>'
    )
    svg.style(FLICKER)
    svg.add(f'<rect class="flicker" width="{w}" height="{h}" fill="url(#{glow})"/>')
    svg.add(f'<g opacity=".2"><g class="spin" style="animation-duration:200s">{seal(390, 136, 110, GOLD, 0.8)}</g></g>')

    x = 58
    svg.add(kicker(svg, x, 90, "Call of Cthulhu · Seventh Edition", pal.accent))
    size = fit("AutoKeeper", "serif", 92, 390)
    svg.add(f'<g class="rise" {delay(0.15)}>' + svg.text(x - 4, 172, "AutoKeeper", "serif", size, pal.ink) + "</g>")
    tagline = wrap("Play Call of Cthulhu with an AI keeper, in the terminal or the browser.", "italic", 27, 390)
    svg.add(f'<g class="rise" {delay(0.3)}>' + svg.lines(x, 218, tagline, 33, face="italic", size=27, fill="#cbbda4") + "</g>")
    svg.add(ornament_rule(svg, x, 448, 284, GOLD, at=0.45))
    bullets = [
        "keeper, NPCs and arbiter as LangGraph agents",
        "seventh-edition rules, physics-thrown dice",
        "true-colour ASCII art, procedural music",
        "solo or online, in a terminal or a browser",
    ]
    svg.add(bullet_lines(svg, x, 332, bullets, "#dccfb6", GOLD, size=20, leading=32, at=0.6))
    svg.add(f'<g class="fade" {delay(1.1)}>' + svg.text(x, 478, "DeepSeek · Claude · Codex · Ollama", "allsc", 15, pal.dim, tracking=2.2) + "</g>")

    release = data.get("release") or {}
    repo = data["repos"].get("autokeeper", {})
    if release:
        line = f"Latest edition {release.get('tag', '')}, {long_date(release.get('published_at'))}"
    else:
        line = f"Last revised {long_date(repo.get('pushed_at'))}"
    stars_markup = ""
    if int(repo.get("stars", 0)):
        stars_markup, _ = meta_stars(svg, x + measure(line, "italic", 20) + 22, 532, int(repo.get("stars", 0)), pal.dim, 20)
    svg.add(f'<g class="fade" {delay(1.25)}>' + svg.text(x, 532, line, "italic", 20, "#c9b99d") + stars_markup + "</g>")

    # A reel of screenshots in an old projector: sepia, scratches and a soft flicker.
    sx, sy, sw, sh = 476, 40, 690, 470
    ix, iy, iw, ih = 492, 90, 658, 370
    strip, picture = svg.uid("strip"), svg.uid("picture")
    svg.define(
        f'<clipPath id="{strip}"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="6"/></clipPath>',
        f'<clipPath id="{picture}"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="2"/></clipPath>',
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
        "@keyframes gate{0%,100%{opacity:1}23%{opacity:.9}41%{opacity:.97}62%{opacity:.88}80%{opacity:.96}}",
        ".gate{animation:gate 2.6s steps(6) infinite}",
    )
    svg.add(
        f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="6" fill="#080504" stroke="#2c1f1a"/>',
        f'<g clip-path="url(#{strip})"><g class="feed" fill="#22181a">{holes}</g></g>',
    )
    frames = []
    for i, (name, _) in enumerate(AK_FRAMES):
        svg.style(crossfade(f"ak{i}", len(AK_FRAMES), i), f".ak{i}{{animation:ak{i} {AK_LOOP}s linear infinite}}")
        hidden = ' opacity="0"' if i else ""
        frames.append(
            f'<image class="ak{i}" href="{data_uri(SRC / "autokeeper" / f"{name}.jpg")}" x="{ix}" y="{iy}" '
            f'width="{iw}" height="{ih}" preserveAspectRatio="xMidYMid slice"{hidden}/>'
        )
    vignette = svg.uid("vignette")
    svg.define(
        f'<radialGradient id="{vignette}" cx=".5" cy=".5" r=".7"><stop offset=".5" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#140904" stop-opacity=".8"/></radialGradient>'
    )
    rng = random.Random(1890)
    scratches = []
    for k in range(4):
        sx0 = rng.uniform(ix + 40, ix + iw - 40)
        period = rng.uniform(2.2, 5.5)
        svg.style(
            f"@keyframes scratch{k}{{0%,100%{{opacity:0;transform:translateX(0)}}"
            f"{num(rng.uniform(5, 30))}%{{opacity:.5;transform:translateX({num(rng.uniform(-12, 12))}px)}}"
            f"{num(rng.uniform(32, 40))}%{{opacity:0}}{num(rng.uniform(60, 80))}%{{opacity:.3;transform:translateX({num(rng.uniform(-30, 30))}px)}}"
            f"{num(rng.uniform(82, 90))}%{{opacity:0}}}}"
        )
        scratches.append(
            f'<path d="M{num(sx0)} {iy}L{num(sx0 + rng.uniform(-4, 4))} {iy + ih}" stroke="#f4e7cf" stroke-width="{num(rng.uniform(.5, 1.1))}" '
            f'opacity="0" style="animation:scratch{k} {num(period)}s steps(1) infinite"/>'
        )
    svg.add(
        f'<g clip-path="url(#{picture})"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#000"/>'
        f'<g class="gate"><g class="drift">{"".join(frames)}</g>'
        f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#6e4a2a" opacity=".5" style="mix-blend-mode:color"/>'
        f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#3a2414" opacity=".25" style="mix-blend-mode:multiply"/></g>'
        + grain(svg, ix, iy, iw, ih, 1)
        + "".join(scratches)
        + f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="url(#{vignette})"/></g>',
        f'<rect x="{ix + .5}" y="{iy + .5}" width="{iw - 1}" height="{ih - 1}" rx="2" fill="none" stroke="#000" stroke-opacity=".6"/>',
    )
    # Caption and reel numerals, in step with the frames.
    for i, (_, label) in enumerate(AK_FRAMES):
        hidden = ' opacity="0"' if i else ""
        reel = f"Reel {ROMAN[i + 1]}"
        svg.style(handover(f"akc{i}", len(AK_FRAMES), i), f".akc{i}{{animation:akc{i} {AK_LOOP}s linear infinite}}")
        svg.add(
            f'<g class="akc{i}"{hidden}>'
            + svg.text(sx + 2, 553, reel, "allsc", 15, pal.accent, tracking=2.4)
            + svg.text(sx + 2 + measure(reel, "allsc", 15, 2.4) + 16, 553, label, "italic", 21, pal.ink)
            + "</g>"
        )
    nx = sx + sw
    for i in reversed(range(len(AK_FRAMES))):
        numeral = ROMAN[i + 1]
        nx -= measure(numeral, "allsc", 16, 1.5)
        hidden = ' opacity="0"' if i else ""
        svg.add(
            svg.text(nx, 553, numeral, "allsc", 16, pal.line, tracking=1.5)
            + f'<g class="akc{i}"{hidden}>' + svg.text(nx, 553, numeral, "allsc", 16, GOLD, tracking=1.5) + "</g>"
        )
        nx -= 18
    plate.close(1, corner="tl")
    return svg.render()


def compskill(data: dict) -> str:
    pal = COMPSKILL
    ink, blue, red, lead, cell = pal.ink, pal.accent2, pal.accent, pal.dim, "#cbccce"
    box = "#efe4c9"
    w, h = 1200, 640
    svg = Svg(w, h, "CompSkill: compiling execution experience for skill retrieval; first-author paper")
    sheet = torn_rect(10, 18, 1180, 604, 5.5, seed=29, edges="tb")
    clip, paper, burn = svg.uid("sheet"), svg.uid("paper"), svg.uid("burn")
    svg.define(
        f'<clipPath id="{clip}"><path d="{sheet}"/></clipPath>',
        f'<linearGradient id="{paper}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eee3c8"/>'
        '<stop offset=".6" stop-color="#e3d4b3"/><stop offset="1" stop-color="#d5c19b"/></linearGradient>',
        f'<radialGradient id="{burn}" cx=".5" cy=".5" r=".75"><stop offset=".62" stop-color="#6b4a24" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#6b4a24" stop-opacity=".4"/></radialGradient>',
    )
    rng = random.Random(1897)
    foxing = "".join(
        f'<circle cx="{num(rng.uniform(30, 1170))}" cy="{num(rng.uniform(30, 610))}" r="{num(rng.uniform(4, 22))}" '
        f'fill="#8a6234" opacity="{num(rng.uniform(.04, .11))}"/>'
        for _ in range(22)
    )
    svg.add(
        f'<path d="{sheet}" transform="translate(5 8)" fill="#000" opacity=".32"/>',
        f'<path d="{sheet}" fill="url(#{paper})"/>',
        f'<g clip-path="url(#{clip})">{foxing}',
        grain(svg, 0, 0, w, h, 0.85),
        f'<rect width="{w}" height="{h}" fill="url(#{burn})"/>',
        # A printer's double rule, set inside the torn edges.
        f'<rect x="34" y="44" width="1132" height="552" fill="none" stroke="{ink}" stroke-opacity=".22"/>'
        f'<rect x="38" y="48" width="1124" height="544" fill="none" stroke="{ink}" stroke-opacity=".12"/>',
    )

    # Left column: title and results.
    x = 66
    svg.add(kicker(svg, x, 92, "First-author paper · Code", red))
    size = fit("CompSkill", "serif", 92, 352)
    svg.add(f'<g class="rise" {delay(0.15)}>' + svg.text(x - 4, 178, "CompSkill", "serif", size, ink) + "</g>")
    svg.add(
        f'<g class="rise" {delay(0.3)}>'
        + svg.lines(x, 224, ["Compiling execution experience", "for skill retrieval"], 34, face="italic", size=28, fill="#3e3124")
        + "</g>"
    )
    results = [
        ("79.8%", "ToolQA hit@1 · baseline 63.0"),
        ("70.9", "SkillRet NDCG@10 · baseline 64.0"),
        ("8×", "smaller keys · 4096 → 512-d"),
    ]
    for i, (value, caption) in enumerate(results):
        y = 348 + i * 92
        width = measure(value, "serif", 54)
        svg.add(
            f'<g class="rise" {delay(0.7 + i * 0.18)}>'
            + svg.text(x - 2, y, value, "serif", 54, ink)
            + svg.text(x, y + 30, caption, "allsc", 15, lead, tracking=1.6)
            + "</g>",
            f'<path class="draw" {delay(1.3 + i * 0.2)} d="{sketch_line(x - 4, y + 9, x + width + 10, y + 7, seed=i + 3, amp=1.4)}" '
            f'pathLength="1" fill="none" stroke="{red}" stroke-width="1.9" stroke-linecap="round" opacity=".8"/>',
        )
    svg.add(
        f'<path class="draw" {delay(0.4)} d="M430 70V582" pathLength="1" stroke="{blue}" stroke-width="1.35" '
        'stroke-dasharray="5 5" opacity=".45" fill="none"/>'
    )

    # The test-time path along the top: task → ① → ② → ③ → ④.
    flow = [("task", ""), ("top-10", "1"), ("score S", "2"), ("6 + ≤4", "3"), ("actor", "4")]
    widths = [measure(label, "serif-m", 22) + (32 if number else 30) for label, number in flow]
    left, right, y = 476, 1140, 112
    gap = (right - left - sum(widths)) / (len(flow) - 1)
    fx = left
    for i, ((label, number), width) in enumerate(zip(flow, widths)):
        if number:
            part = (
                f'<circle cx="{num(fx + 11)}" cy="{y - 7}" r="11" fill="none" stroke="{ink}" stroke-width="1.45"/>'
                + svg.text(fx + 11, y - 2, number, "serif-m", 14, ink, "middle")
                + svg.text(fx + 30, y, label, "serif-m", 22, ink)
            )
        else:
            part = (
                f'<path d="M{num(fx)} {y - 26}h{num(width)}v32h-{num(width - 22)}l-9 9v-9h-13z" fill="{box}" '
                f'stroke="{ink}" stroke-width="1.45" stroke-linejoin="round"/>'
                + svg.text(fx + 14, y - 3, label, "italic", 22, ink)
            )
        svg.add(f'<g class="fade" {delay(0.5 + i * 0.15)}>{part}</g>')
        if i < len(flow) - 1:
            ax = fx + width + 8
            svg.add(arrow(ax, y - 7, ax + gap - 16, y - 7, ink, 1, 7, f'class="fade" {delay(0.6 + i * 0.15)}'))
        fx += width + gap
    svg.style(
        "@keyframes probe{0%{transform:translateX(0);opacity:0}6%{opacity:1}70%{transform:translateX(640px);opacity:1}"
        "76%,100%{transform:translateX(640px);opacity:0}}",
        ".probe{animation:probe 9s cubic-bezier(.45,0,.55,1) 2.5s infinite both}",
    )
    svg.add(
        f'<path d="M482 134H1136" stroke="{blue}" stroke-width="1.35" stroke-dasharray="2 5" opacity=".5"/>',
        f'<circle class="probe" cx="484" cy="134" r="4" fill="{red}"/>',
    )

    def heading(xx: float, yy: float, number: str, text: str, at: float) -> str:
        return (
            f'<g class="fade" {delay(at)}><circle cx="{num(xx + 10)}" cy="{num(yy - 7)}" r="10" fill="none" stroke="{ink}" stroke-width="1.45"/>'
            + svg.text(xx + 10, yy - 2.5, number, "serif-m", 13, ink, "middle")
            + svg.text(xx + 28, yy, text, "serif-m", 21, ink)
            + "</g>"
        )

    # ① compact keys.
    svg.add(heading(476, 188, "1", "compact keys", 1.0))
    cells = "".join(f'<rect x="{476 + c * 9}" y="208" width="9" height="15" fill="{cell}" stroke="{blue}" stroke-width="1.25"/>' for c in range(16))
    short = "".join(f'<rect x="{538 + c * 9}" y="294" width="9" height="15" fill="{cell}" stroke="{blue}" stroke-width="1.25"/>' for c in range(2))
    svg.add(
        f'<g class="fade" {delay(1.1)}>{cells}'
        + svg.text(476, 246, "4096-d", "italic", 17, lead)
        + f'<path d="M524 252H572L560 274H536Z" fill="none" stroke="{ink}" stroke-width="1.45" stroke-linejoin="round"/>'
        + arrow(548, 226, 548, 248, ink, 1, 5)
        + arrow(548, 276, 547, 291, ink, 1, 5)
        + short
        + svg.text(562, 307, "512-d", "italic", 17, lead)
        + "</g>",
        f'<g class="fade" {delay(1.9)}>'
        + svg.text(476, 356, "×8 fewer", "italic", 21, red)
        + svg.text(476, 380, "coordinates", "italic", 21, red)
        + f'<path d="M560 344C590 340 600 326 590 314" fill="none" stroke="{red}" stroke-width="1.55"/>'
        + "</g>",
    )

    # ② KeyOpt calibration and the skill key.
    svg.add(heading(664, 188, "2", "KeyOpt calibration", 1.2))
    ox, oy = 690, 326
    svg.add(
        f'<g class="fade" {delay(1.4)}>'
        f'<circle cx="842" cy="244" r="28" fill="none" stroke="{blue}" stroke-width="1.35" stroke-dasharray="4 4"/>'
        + arrow(ox, oy, 772, 214, ink, 1.2, 9)
        + arrow(ox, oy, 840, 244, blue, 1.2, 9)
        + arrow(ox, oy, 826, 224, red, 1.2, 9)
        + svg.text(752, 210, "q", "italic", 22, ink)
        + svg.text(852, 272, "k⁰", "italic", 22, blue)
        + svg.text(818, 214, "k′", "italic", 22, red)
        + f'<circle cx="{ox}" cy="{oy}" r="2.6" fill="{ink}"/>'
        + svg.text(800, 302, "score change ≤ c", "italic", 19, lead)
        + "</g>"
    )
    key_cells = "".join(f'<rect x="{664 + c * 13}" y="356" width="13" height="18" fill="{cell}" stroke="{blue}" stroke-width="1.25"/>' for c in range(20))
    svg.style(
        "@keyframes edit{0%,30%{opacity:.25}38%,62%{opacity:1}75%,100%{opacity:.25}}",
        ".edit{animation:edit 9s ease-in-out 2.5s infinite both}",
    )
    svg.add(
        f'<g class="fade" {delay(1.6)}>{key_cells}'
        f'<rect class="edit" x="664" y="377" width="260" height="5" fill="{red}" opacity=".7"/>'
        f'<rect x="930" y="356" width="18" height="18" fill="#efd6c8" stroke="{red}" stroke-width="1.35"/>'
        + svg.text(939, 370, "b", "italic", 17, red, "middle")
        + svg.text(664, 412, "key = [k⁰ + Δk ; b]", "serif-m", 22, ink)
        + "</g>",
        f'<g class="fade" {delay(2.1)}>' + svg.text(664, 440, "read with one inner product and a clip", "italic", 19, red) + "</g>",
    )

    # ③ the experience hypergraph.
    svg.add(heading(978, 188, "3", "hypergraph", 1.4))
    nodes = [(996, 240), (1032, 218), (1050, 266), (1006, 294), (1092, 228), (1118, 274), (1080, 306)]
    blob_a = "M984 234C990 204 1040 200 1062 226C1080 250 1060 304 1022 306C990 308 978 266 984 234Z"
    blob_b = "M1040 256C1046 218 1100 202 1126 234C1140 266 1118 322 1080 318C1050 314 1036 288 1040 256Z"
    svg.add(
        f'<g class="fade" {delay(1.7)}>'
        f'<path d="{blob_a}" fill="{blue}" fill-opacity=".1" stroke="{blue}" stroke-width="1.35"/>'
        f'<path d="{blob_b}" fill="{red}" fill-opacity=".08" stroke="{red}" stroke-width="1.35"/>'
        f'<path d="M996 240L1032 218L1050 266L1006 294ZM1050 266L1092 228L1118 274L1080 306Z" fill="none" stroke="{ink}" stroke-width="1.35" opacity=".7"/>'
        + "".join(f'<circle cx="{nx}" cy="{ny}" r="4" fill="{ink}"/>' for nx, ny in nodes)
        + svg.text(978, 350, "attributed events", "italic", 18, lead)
        + svg.text(978, 372, "task · executor · version", "allsc", 14.5, lead, tracking=1.2)
        + "</g>"
    )

    # Between rounds: publish ← fit ← filter ← record ← outcomes, fed by ④.
    svg.add(f'<g class="fade" {delay(2.0)}>' + svg.text(476, 486, "between rounds · support tasks only", "italic", 20, blue) + "</g>")
    steps = ["Publish", "Fit", "Filter", "Record", "Outcomes"]
    bw, bgap, by = 84, 13, 504
    svg.style("@keyframes back{to{stroke-dashoffset:22}}", ".back{animation:back 2.4s linear infinite}")
    for i, step in enumerate(steps):
        bx = 476 + i * (bw + bgap)
        svg.add(
            f'<g class="fade" {delay(2.1 + i * 0.08)}><rect x="{bx}" y="{by}" width="{bw}" height="32" rx="2" fill="{box}" stroke="{ink}" stroke-width="1.45"/>'
            + svg.text(bx + bw / 2, by + 21, step, "allsc", 14, ink, "middle", tracking=1.2)
            + "</g>"
        )
        if i:
            svg.add(arrow(bx - 2, by + 16, bx - bgap + 3, by + 16, blue, 1, 5, f'class="fade" {delay(2.2 + i * 0.08)}'))
    end = 476 + 5 * (bw + bgap)
    svg.add(f'<path class="back" d="M{end + 30} {by + 16}H{end - bgap + 2}" stroke="{blue}" stroke-width="1.45" stroke-dasharray="5 6" fill="none"/>')
    svg.add(heading(1000, 474, "4", "frozen actor", 1.8))
    for i, name in enumerate(["ToolQA", "AppWorld", "ALFWorld"]):
        wx, wy = 1004 + i * 12, 488 + i * 31
        svg.add(
            f'<g class="fade" {delay(1.9 + i * 0.1)}><rect x="{wx}" y="{wy}" width="124" height="38" rx="2" fill="{box}" stroke="{ink}" stroke-width="1.45"/>'
            f'<path d="M{wx} {wy + 10}H{wx + 124}" stroke="{ink}" stroke-width="1.15"/>'
            + "".join(f'<circle cx="{wx + 8 + d * 7}" cy="{wy + 5}" r="1.5" fill="{ink}"/>' for d in range(3))
            + svg.text(wx + 10, wy + 28, name, "italic", 17, ink)
            + "</g>"
        )
    svg.add(f'<g class="fade" {delay(2.3)}>' + svg.text(476, 576, "the actor reads the original skill document only", "italic", 19, red) + "</g>")
    svg.add("</g>", f'<path d="{sheet}" fill="none" stroke="#b9a37d" stroke-width="1.25"/>')
    svg.add(svg.text(1134, 76, "Plate II", "allsc", 14, lead, "end", tracking=2.4))
    return svg.render()


def deep_learning(data: dict) -> str:
    pal = DEEP
    chalk, yellow, pink, blue = pal.ink, pal.accent, pal.accent2, pal.accent3
    w, h = 1200, 600
    svg = Svg(w, h, "From y = ax + b to MiniMind: an open deep learning textbook, adopted for a university elective")
    plate = Plate(svg, pal)
    plate.open()
    glow, grid, dust = svg.uid("glow"), svg.uid("grid"), svg.uid("dust")
    svg.define(
        f'<radialGradient id="{glow}" cx=".45" cy=".4" r=".7"><stop offset="0" stop-color="#1f2b25"/>'
        f'<stop offset="1" stop-color="{pal.bg}"/></radialGradient>',
        f'<pattern id="{grid}" width="30" height="30" patternUnits="userSpaceOnUse">'
        '<path d="M30 0H0V30" fill="none" stroke="#e9f2ec" stroke-opacity=".03"/></pattern>',
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
    x = 58
    svg.add(kicker(svg, x, 90, "Open textbook · NumPy → PyTorch", yellow))
    first = "From "
    first_w = measure(first, "serif", 66)
    svg.add(
        f'<g class="rise" {delay(0.15)}>'
        + svg.text(x - 3, 168, first, "serif", 66, chalk)
        + svg.text(x - 3 + first_w, 168, "y = ax + b", "italic", 70, yellow)
        + "</g>",
        f'<g class="rise" {delay(0.3)}>' + svg.text(x - 3, 238, "to MiniMind", "serif", 66, chalk) + "</g>",
        f'<g class="fade" {delay(0.6)}>' + svg.text(x, 284, "deep learning, one runnable exercise at a time", "italic", 22, pal.dim) + "</g>",
    )

    # The chalk note: adopted for a university elective.
    svg.add(
        f'<g class="fade" {delay(1.0)}>'
        + svg.text(978, 128, "adopted as the textbook", "italic", 30, pink, "middle")
        + svg.text(978, 164, "for a university elective", "italic", 30, pink, "middle")
        + "</g>",
        f'<path class="draw" {delay(1.3)} d="{sketch_loop(978, 140, 176, 56, seed=7)}" pathLength="1" fill="none" '
        f'stroke="{pink}" stroke-width="1.9" opacity=".8" {chalk_dash}/>',
        f'<path class="draw" {delay(2.0)} d="M796 176C740 198 690 196 640 176" pathLength="1" fill="none" stroke="{pink}" stroke-width="1.9" opacity=".75"/>',
        f'<path class="fade" {delay(2.6)} d="M652 168L640 176L654 184" fill="none" stroke="{pink}" stroke-width="1.9" stroke-linecap="round" opacity=".75"/>',
        f'<g class="fade" {delay(1.6)}>' + svg.text(978, 230, "twenty interactive demos · unit-tested exercises", "italic", 18, pal.dim, "middle") + "</g>",
    )

    panels = [
        (58, "Block I", "NumPy from scratch", "Linear, ReLU, backprop → MNIST"),
        (436, "Block II", "Convolution & ResNet", "im2col, BatchNorm → CIFAR-100"),
        (816, "Block III", "Transformer & MiniMind", "RoPE, GQA, SwiGLU, KV cache"),
    ]
    for i, (px, tag, title, body) in enumerate(panels):
        at = 1.2 + i * 0.35
        tag_w = measure(tag, "allsc", 16, 2.4)
        svg.add(
            f'<g class="fade" {delay(at)}>'
            + svg.text(px, 338, tag, "allsc", 16, yellow, tracking=2.4)
            + f'<path d="{sketch_line(px, 346, px + tag_w, 345, seed=60 + i, amp=0.8)}" fill="none" stroke="{yellow}" stroke-width="1.55" opacity=".55"/>'
            + svg.text(px, 512, title, "serif", 26, chalk)
            + svg.text(px, 540, body, "italic", 19, pal.dim)
            + "</g>"
        )
        if i:
            svg.add(
                f'<path class="draw" {delay(at + 0.2)} d="{sketch_line(px - 54, 404, px - 18, 402, seed=40 + i, amp=1)}" '
                f'pathLength="1" fill="none" stroke="{chalk}" stroke-width="1.9" opacity=".6"/>',
                f'<path class="fade" {delay(at + 0.6)} d="M{px - 26} 395L{px - 17} 402L{px - 27} 409" fill="none" stroke="{chalk}" '
                'stroke-width="1.9" stroke-linecap="round" opacity=".6"/>',
            )

    # Block I: points and a line that keeps settling onto them.
    rng = random.Random(4)
    points = []
    for k in range(11):
        px = 92 + k * 25
        points.append((px, 452 - (px - 80) * 0.32 + rng.uniform(-13, 13)))
    svg.style(
        "@keyframes fitline{0%{transform:rotate(-16deg)}55%,85%{transform:rotate(0deg)}100%{transform:rotate(-16deg)}}",
        ".fitline{animation:fitline 8s cubic-bezier(.3,0,.2,1) 2s infinite both;transform-box:fill-box;transform-origin:50% 50%}",
    )
    svg.add(
        f'<path class="draw" {delay(1.3)} d="M74 360V462H372" pathLength="1" fill="none" stroke="{chalk}" stroke-width="1.7" opacity=".7" {chalk_dash}/>',
        f'<g class="fade" {delay(1.5)} fill="{chalk}">'
        + "".join(f'<circle cx="{num(px)}" cy="{num(py)}" r="3" opacity=".9"/>' for px, py in points)
        + "</g>",
        f'<g class="fade" {delay(1.8)}><path class="fitline" d="M84 {num(452 - 4 * .32)}L364 {num(452 - 284 * .32)}" stroke="{yellow}" stroke-width="2" stroke-linecap="round" fill="none"/></g>',
        f'<g class="fade" {delay(2.0)}>' + svg.text(300, 456, "loss → 0.042", "italic", 17, pal.dim, "end") + "</g>",
    )

    # Block II: a 3×3 window sliding over a 6×6 input, filling a 4×4 output.
    cell, gx, gy, ox, oy = 16, 456, 358, 612, 382
    grid_cells = "".join(f'<rect x="{gx + c * cell}" y="{gy + r * cell}" width="{cell}" height="{cell}"/>' for r in range(6) for c in range(6))
    positions = [(r, c) for r in range(4) for c in range(4)]
    slide = "".join(f"{num(k * 100 / 16)}%{{transform:translate({c * cell}px,{r * cell}px)}}" for k, (r, c) in enumerate(positions))
    svg.style(f"@keyframes slide{{{slide}100%{{transform:translate(0,0)}}}}", ".slide{animation:slide 12.8s step-end 2.2s infinite both}")
    outputs = []
    for k, (r, c) in enumerate(positions):
        start = k * 100 / 16
        svg.style(
            f"@keyframes out{k}{{0%{{opacity:.08}}{num(start)}%{{opacity:.08}}{num(start + 0.01)}%,99.9%{{opacity:.8}}100%{{opacity:.08}}}}",
            f".out{k}{{animation:out{k} 12.8s step-end 2.2s infinite both}}",
        )
        outputs.append(f'<rect class="out{k}" x="{ox + c * cell + 1}" y="{oy + r * cell + 1}" width="{cell - 2}" height="{cell - 2}" fill="{blue}"/>')
    svg.add(
        f'<g class="fade" {delay(1.7)}><g fill="none" stroke="{chalk}" stroke-width="1.25" opacity=".55">{grid_cells}</g>'
        f'<rect class="slide" x="{gx}" y="{gy}" width="{cell * 3}" height="{cell * 3}" fill="{yellow}" fill-opacity=".12" stroke="{yellow}" stroke-width="1.9"/>'
        + arrow(560, 406, 600, 406, chalk, 1.3, 6, 'opacity=".7"')
        + svg.text(580, 390, "im2col", "italic", 16, pal.dim, "middle")
        + f'<g fill="none" stroke="{chalk}" stroke-width="1.25" opacity=".55">'
        + "".join(f'<rect x="{ox + c * cell}" y="{oy + r * cell}" width="{cell}" height="{cell}"/>' for r in range(4) for c in range(4))
        + "</g>"
        + "".join(outputs)
        + "</g>"
    )

    # Block III: the first chapter's equation as tokens, attended causally.
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
            f".att{q}{{animation:att{q} 12s ease-in-out 2.4s infinite both}}",
        )
        lights.append(
            f'<g class="att{q}" opacity="0"><path d="{"".join(group)}" fill="none" stroke="{yellow}" stroke-width="1.8"/>'
            f'<rect x="{num(centers[q] - tw / 2)}" y="{ty}" width="{tw}" height="30" rx="2" fill="{yellow}" fill-opacity=".14" stroke="{yellow}" stroke-width="1.7"/></g>'
        )
    svg.add(
        f'<g class="fade" {delay(2.0)}><path d="{"".join(arcs)}" fill="none" stroke="{chalk}" stroke-width="1.35" opacity=".22"/>'
        + "".join(
            f'<rect x="{num(cx - tw / 2)}" y="{ty}" width="{tw}" height="30" rx="2" fill="none" stroke="{chalk}" stroke-width="1.55" opacity=".75"/>'
            + svg.text(cx, ty + 22, tok, "italic", 22, chalk, "middle")
            for cx, tok in zip(centers, tokens)
        )
        + "".join(lights)
        + "</g>"
    )

    star_markup, fx = meta_stars(svg, x, 578, stars, yellow, 18, "italic")
    svg.add(
        f'<g class="fade" {delay(2.4)}>' + star_markup
        + svg.text(fx + 16, 578, "stars · a Hugo site · tests for gradients, shapes and causal masks", "italic", 18, pal.dim)
        + "</g>"
    )
    plate.close(3, corner="tr")
    return svg.render()
