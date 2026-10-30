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
    """The paper's architecture figure, redrawn in ink on old paper."""
    pal = COMPSKILL
    ink, red, lead = pal.ink, pal.accent, pal.dim
    blue, ochre, violet, slate = pal.accent2, "#a8692c", "#6a5288", "#4b5563"
    box, cell = "#efe4c9", "#cfd0d0"
    w, h = 1200, 880
    svg = Svg(w, h, "CompSkill: compiling execution experience for skill retrieval; the paper's architecture, redrawn")
    sheet = torn_rect(10, 18, 1180, h - 36, 5.5, seed=29, edges="tb")
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
        f'<circle cx="{num(rng.uniform(30, 1170))}" cy="{num(rng.uniform(30, h - 30))}" r="{num(rng.uniform(4, 22))}" '
        f'fill="#8a6234" opacity="{num(rng.uniform(.03, .09))}"/>'
        for _ in range(26)
    )
    svg.add(
        f'<path d="{sheet}" transform="translate(5 8)" fill="#000" opacity=".32"/>',
        f'<path d="{sheet}" fill="url(#{paper})"/>',
        f'<g clip-path="url(#{clip})">{foxing}',
        grain(svg, 0, 0, w, h, 0.85),
        f'<rect width="{w}" height="{h}" fill="url(#{burn})"/>',
        f'<rect x="34" y="44" width="1132" height="{h - 88}" fill="none" stroke="{ink}" stroke-opacity=".25" stroke-width="1.2"/>'
        f'<rect x="39" y="49" width="1122" height="{h - 98}" fill="none" stroke="{ink}" stroke-opacity=".14"/>',
    )

    # Title band: the paper on the left, three results on the right.
    x = 66
    svg.add(kicker(svg, x, 94, "First-author paper · Code", red))
    svg.add(f'<g class="rise" {delay(0.15)}>' + svg.text(x - 4, 172, "CompSkill", "serif", 84, ink) + "</g>")
    svg.add(f'<g class="rise" {delay(0.3)}>' + svg.text(x, 210, "Compiling execution experience for skill retrieval", "italic", 26, "#3e3124") + "</g>")
    results = [("79.8%", "ToolQA hit@1", "baseline 63.0"), ("70.9", "SkillRet NDCG@10", "baseline 64.0"), ("8×", "smaller keys", "4096 → 512-d")]
    for i, (value, caption, note) in enumerate(results):
        rx = 680 + i * 164
        width = measure(value, "serif", 48)
        svg.add(
            f'<g class="rise" {delay(0.6 + i * 0.15)}>'
            + svg.text(rx, 150, value, "serif", 48, ink)
            + svg.text(rx, 180, caption, "allsc", 14.5, lead, tracking=1.2)
            + svg.text(rx, 204, note, "italic", 17, lead)
            + "</g>",
            f'<path class="draw" {delay(1.2 + i * 0.2)} d="{sketch_line(rx - 2, 160, rx + width + 8, 158, seed=i + 3, amp=1.2)}" '
            f'pathLength="1" fill="none" stroke="{red}" stroke-width="2" stroke-linecap="round" opacity=".8"/>',
        )
    svg.add(f'<path class="draw" {delay(0.4)} d="M64 236H1136" pathLength="1" stroke="{ink}" stroke-opacity=".35" stroke-width="1.2" fill="none"/>')

    # The figure. Panels sit where they do in the paper: (1) top left, (2) bottom left,
    # the skill key in the centre, (3) top right, (4) bottom right, the support loop along the bottom.
    fy = 256

    def panel(px: float, py: float, pw: float, ph: float, color: str, number: str, title: str, at: float) -> str:
        return (
            f'<g class="fade" {delay(at)}>'
            f'<rect x="{num(px)}" y="{num(py)}" width="{num(pw)}" height="{num(ph)}" rx="5" fill="{color}" fill-opacity=".09" stroke="{color}" stroke-width="1.6"/>'
            f'<rect x="{num(px)}" y="{num(py)}" width="{num(pw)}" height="32" rx="5" fill="{color}" fill-opacity=".85"/>'
            f'<rect x="{num(px)}" y="{num(py + 26)}" width="{num(pw)}" height="6" fill="{color}" fill-opacity=".85"/>'
            + (f'<circle cx="{num(px + 18)}" cy="{num(py + 16)}" r="10" fill="#f3ead6"/>' + svg.text(px + 18, py + 21, number, "serif", 15, color, "middle") if number else "")
            + svg.text(px + (36 if number else 14), py + 23, title, "serif", 20, "#f6eedc")
            + "</g>"
        )

    def sub(px: float, py: float, pw: float, ph: float, title: str, color: str) -> str:
        return (
            f'<rect x="{num(px)}" y="{num(py)}" width="{num(pw)}" height="{num(ph)}" rx="4" fill="#f4ecd9" fill-opacity=".75" stroke="{color}" stroke-opacity=".7" stroke-width="1.1"/>'
            + svg.text(px + 10, py + 22, title, "serif", 18, ink)
        )

    def bar(bx: float, by: float, n: int, cw: float, ch: float, color: str, hi: int = -1) -> str:
        return "".join(
            f'<rect x="{num(bx + k * cw)}" y="{num(by)}" width="{num(cw)}" height="{num(ch)}" fill="{"#e2b48a" if k == hi else cell}" stroke="{color}" stroke-width=".9"/>'
            for k in range(n)
        )

    # Top flow: task → semantic top-10 → calibrated score → 6 kept + ≤4 recalled → (3).
    flow = [("task x", ""), ("semantic top-10", "1"), ("calibrated score S", "2"), ("6 kept + ≤4 recalled", "3")]
    size = 16
    widths = [64 if not n else measure(t, "serif-m", size) + 30 for t, n in flow]
    gap = (892 - 300 - sum(widths) - 26) / len(flow)
    fx = 300
    for i, ((label, number), width) in enumerate(zip(flow, widths)):
        if number:
            part = (
                svg.text(fx, fy + 30, label, "serif-m", size, "#3a4458")
                + f'<circle cx="{num(fx + width - 10)}" cy="{fy + 24}" r="10" fill="#3a4458"/>'
                + svg.text(fx + width - 10, fy + 29, number, "serif", 14, "#f3ead6", "middle")
            )
        else:
            part = f'<path d="M{fx} {fy + 6}h64v32h-42l-9 9v-9h-13z" fill="{box}" stroke="{ink}" stroke-width="1.3" stroke-linejoin="round"/>' + svg.text(fx + 14, fy + 29, label, "italic", 19, ink)
        svg.add(f'<g class="fade" {delay(0.6 + i * 0.12)}>{part}</g>')
        svg.add(arrow(fx + width + 5, fy + 24, fx + width + gap - 5, fy + 24, "#3a4458", 1.3, 7, f'class="fade" {delay(0.7)}'))
        fx += width + gap
    svg.add(arrow(282, fy + 24, 296, fy + 24, "#3a4458", 1.3, 7, f'class="fade" {delay(0.7)}'))
    svg.style(
        "@keyframes probe{0%{transform:translateX(0);opacity:0}8%{opacity:1}72%{transform:translateX(560px);opacity:1}"
        "78%,100%{transform:translateX(560px);opacity:0}}",
        ".probe{animation:probe 9s cubic-bezier(.45,0,.55,1) 2.5s infinite both}",
    )
    svg.add(f'<circle class="probe" cx="330" cy="{fy + 54}" r="4.5" fill="{red}"/>')

    # (1) Compact keys.
    px, py, pw, ph = 52, fy, 230, 286
    svg.add(panel(px, py, pw, ph, blue, "1", "Compact keys", 0.9))
    docs = "".join(f'<rect x="{px + 16 + d * 5}" y="{py + 66 + d * 5}" width="40" height="50" rx="2" fill="#f7f0de" stroke="{ink}" stroke-width="1.1"/>' for d in range(3))
    svg.add(
        f'<g class="fade" {delay(1.0)}>'
        + sub(px + 8, py + 40, pw - 16, 118, "Skill library", blue)
        + docs + svg.text(px + 46, py + 102, "skill", "italic", 15, ink, "middle")
        + f'<rect x="{px + 92}" y="{py + 70}" width="30" height="26" rx="3" fill="#c8ccd2" stroke="{ink}" stroke-width="1.1"/>' + svg.text(px + 107, py + 89, "E", "serif", 17, ink, "middle")
        + f'<rect x="{px + 92}" y="{py + 112}" width="30" height="26" rx="3" fill="#e8c497" stroke="{ink}" stroke-width="1.1"/>' + svg.text(px + 107, py + 131, "C", "italic", 17, ink, "middle")
        + bar(px + 136, py + 76, 6, 13, 14, blue) + bar(px + 150, py + 118, 4, 13, 14, blue)
        + arrow(px + 122, py + 83, px + 134, py + 83, blue, 1.1, 5) + arrow(px + 122, py + 125, px + 148, py + 125, blue, 1.1, 5)
        + arrow(px + 175, py + 92, px + 175, py + 114, blue, 1.1, 5)
        + svg.text(px + 140, py + 150, "4096-d → 512-d", "italic", 15, lead)
        + sub(px + 8, py + 166, pw - 16, 112, "Key index", blue)
        + "".join(
            svg.text(px + 22, py + 210 + k * 22, f"s{k + 1}", "italic", 16, red if k == 1 else ink)
            + bar(px + 42, py + 198 + k * 22, 7, 12, 14, red if k == 1 else blue, 6 if k == 1 else -1)
            for k in range(3)
        )
        + f'<rect x="{px + 150}" y="{py + 198}" width="62" height="40" rx="6" fill="#f6e3c4" stroke="{ink}" stroke-width="1.1"/>'
        + "".join(f'<circle cx="{px + 164 + c * 14}" cy="{py + 209 + r * 16}" r="4" fill="{blue}"/>' for r in range(2) for c in range(3))
        + svg.text(px + 181, py + 258, "top-10 pool", "italic", 15, ink, "middle")
        + "</g>"
    )

    # (2) KeyOpt calibration.
    px, py, pw, ph = 52, fy + 300, 230, 296
    svg.add(panel(px, py, pw, ph, ochre, "2", "KeyOpt calibration", 1.2))
    cards = "".join(
        f'<rect x="{px + 18 + k * 66}" y="{py + 68}" width="38" height="46" rx="2" fill="#f7f0de" stroke="{ink}" stroke-width="1.1"/>'
        + svg.text(px + 37 + k * 66, py + 96, "task", "italic", 13, ink, "middle")
        + f'<circle cx="{px + 52 + k * 66}" cy="{py + 112}" r="7" fill="{"#5f8a5a" if k == 0 else red}"/>'
        + (f'<path d="M{px + 48 + k * 66} {py + 112}l3 3 5-6" fill="none" stroke="#fff" stroke-width="1.6"/>' if k == 0
           else f'<path d="M{px + 49 + k * 66} {py + 109}l6 6M{px + 55 + k * 66} {py + 109}l-6 6" stroke="#fff" stroke-width="1.6"/>')
        for k in range(3)
    )
    svg.add(
        f'<g class="fade" {delay(1.3)}>'
        + sub(px + 8, py + 40, pw - 16, 118, "Matched support", ochre) + cards
        + svg.text(px + 20, py + 146, "same task: loss(Sa − Sb) → c", "italic", 15, ink)
        + sub(px + 8, py + 166, pw - 16, 122, "Bounded key edit", ochre)
        + f'<circle cx="{px + 66}" cy="{py + 238}" r="34" fill="none" stroke="{ochre}" stroke-width="1.3" stroke-dasharray="4 4"/>'
        + arrow(px + 40, py + 268, px + 66, py + 204, ink, 1.2, 7)
        + arrow(px + 40, py + 268, px + 92, py + 222, blue, 1.2, 7)
        + arrow(px + 40, py + 268, px + 96, py + 240, ochre, 1.2, 7)
        + svg.text(px + 64, py + 200, "q", "italic", 16, ink) + svg.text(px + 96, py + 220, "k⁰", "italic", 16, blue) + svg.text(px + 100, py + 248, "k′", "italic", 16, ochre)
        + bar(px + 124, py + 210, 6, 13, 14, blue, 5)
        + svg.text(px + 124, py + 246, "[k⁰ + Δk ; b]", "serif-m", 16, ink)
        + svg.text(px + 124, py + 270, "change ≤ c", "italic", 15, lead)
        + "</g>"
    )

    # The skill key, centre.
    px, py, pw, ph = 296, fy + 66, 592, 404
    svg.add(
        f'<g class="fade" {delay(1.0)}>'
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="6" fill="{red}" fill-opacity=".06" stroke="{red}" stroke-width="1.8"/>'
        f'<rect x="{px}" y="{py}" width="{pw}" height="54" rx="6" fill="{red}" fill-opacity=".85"/>'
        + svg.text(px + pw / 2, py + 24, "The skill key", "serif", 22, "#f6eedc", "middle")
        + svg.text(px + pw / 2, py + 46, "fitted between rounds · read with one inner product and a clip", "italic", 16, "#f3e3d0", "middle")
        + "</g>"
    )
    cw3 = (pw - 32) / 3
    reads = [
        ("One read", ["=S=r+β+clip(d)+ac", "no LLM call"]),
        ("Coffee case", ["single-day  .844", "range  .835   + .37", "rank 2 → 1"]),
        ("One row per edit", ["s₁ … s₄: local edits", "each one can be undone"]),
    ]
    reads[2] = ("One row per edit", ["s1 … s4: local edits", "each one can be undone"])

    def line_text(lx: float, ly: float, text: str) -> str:
        # Lines starting with "=" are formulas, set in the mono face that has the Greek.
        if text.startswith("="):
            return svg.text(lx, ly, text[1:], "mono", 14, ink)
        return svg.text(lx, ly, text, "italic", 15.5, ink)
    svg.add(f'<g class="fade" {delay(1.4)}>' + svg.text(px + 12, py + 78, "Reading the key", "serif", 19, red) + svg.text(px + 170, py + 78, "at test time", "italic", 16, lead))
    for k, (title, lines) in enumerate(reads):
        bx = px + 8 + k * (cw3 + 8)
        svg.add(sub(bx, py + 90, cw3, 98, title, red) + "".join(line_text(bx + 10, py + 136 + j * 21, line) for j, line in enumerate(lines)))
    svg.add("</g>")
    svg.style("@keyframes edit{0%,30%{opacity:.3}38%,62%{opacity:1}75%,100%{opacity:.3}}", ".edit{animation:edit 9s ease-in-out 2.5s infinite both}")
    kb = px + 50
    svg.add(
        f'<g class="fade" {delay(1.6)}>'
        + svg.text(px + 14, py + 222, "k⁰", "italic", 20, blue) + svg.text(px + 14, py + 246, "Δk", "italic", 20, ochre)
        + bar(kb, py + 206, 22, 13, 18, blue)
        + f'<rect class="edit" x="{kb}" y="{py + 230}" width="{22 * 13}" height="8" fill="{ochre}" opacity=".8"/>'
        + f'<rect x="{kb + 22 * 13 + 10}" y="{py + 206}" width="22" height="22" fill="#e2b48a" stroke="{ochre}" stroke-width="1.2"/>' + svg.text(kb + 22 * 13 + 21, py + 223, "b", "italic", 17, ink, "middle")
        + svg.text(kb + 22 * 13 + 44, py + 224, "key = [k⁰ + Δk ; b]", "serif-m", 19, ink)
        + svg.text(kb + 22 * 13 + 44, py + 246, "one key per skill", "italic", 15, lead)
        + "</g>"
    )
    writes = [
        ("k⁰: only keys move", ["requests pull the key", "toward raw queries"]),
        ("Δk: query advantage", ["won pulls in, lost pushes out", "=Δk ~ Σ±(q−μ)"]),
        ("b: not task ease", ["raw rates mislead;", "compare the same task"]),
    ]
    svg.add(f'<g class="fade" {delay(1.8)}>' + svg.text(px + 12, py + 280, "Writing the key", "serif", 19, blue) + svg.text(px + 166, py + 280, "between rounds", "italic", 16, lead))
    for k, (title, lines) in enumerate(writes):
        bx = px + 8 + k * (cw3 + 8)
        svg.add(sub(bx, py + 292, cw3, 104, title, ochre if k else blue) + "".join(line_text(bx + 10, py + 338 + j * 21, line) for j, line in enumerate(lines)))
    svg.add("</g>")

    # (3) Experience hypergraph.
    px, py, pw, ph = 902, fy, 246, 334
    svg.add(panel(px, py, pw, ph, violet, "3", "Experience hypergraph", 1.2))
    nodes = [(924, fy + 92), (950, fy + 72), (972, fy + 104), (938, fy + 122), (1000, fy + 78), (1018, fy + 112), (992, fy + 130)]
    svg.add(
        f'<g class="fade" {delay(1.4)}>'
        + sub(px + 8, py + 40, pw - 16, 118, "Attributed events", violet)
        + f'<path d="M914 {fy + 90}C918 {fy + 62} 966 {fy + 58} 980 {fy + 86}C992 {fy + 112} 974 {fy + 140} 946 {fy + 138}C920 {fy + 136} 910 {fy + 112} 914 {fy + 90}Z" fill="{blue}" fill-opacity=".16" stroke="{blue}" stroke-width="1.1"/>'
        + f'<path d="M964 {fy + 98}C968 {fy + 66} 1016 {fy + 60} 1030 {fy + 92}C1040 {fy + 120} 1020 {fy + 146} 992 {fy + 142}C970 {fy + 140} 960 {fy + 120} 964 {fy + 98}Z" fill="{violet}" fill-opacity=".14" stroke="{violet}" stroke-width="1.1"/>'
        + f'<path d="M924 {fy + 92}L950 {fy + 72}L972 {fy + 104}L938 {fy + 122}ZM972 {fy + 104}L1000 {fy + 78}L1018 {fy + 112}L992 {fy + 130}Z" fill="none" stroke="{ink}" stroke-width="1.1" opacity=".7"/>'
        + "".join(f'<circle cx="{nx}" cy="{ny}" r="4" fill="{ink}"/>' for nx, ny in nodes)
        + "".join(svg.text(1046, fy + 82 + j * 19, t, "italic", 15, ink) for j, t in enumerate(["task", "executor", "versions", "arms (s, y)"]))
        + sub(px + 8, py + 166, pw - 16, 66, "Admit & read · recall", violet)
        + "".join(f'<circle cx="{px + 26 + c * 13}" cy="{py + 216}" r="5" fill="{violet}"/>' for c in range(4))
        + svg.text(px + 90, py + 221, "6 kept + 4 recalled", "italic", 15.5, ink)
        + sub(px + 8, py + 240, pw - 16, 86, "Evidence review", violet)
        + f'<rect x="{px + 22}" y="{py + 272}" width="26" height="34" rx="2" fill="#f7f0de" stroke="{ink}" stroke-width="1.1"/>'
        + "".join(f'<path d="M{px + 27} {py + 282 + j * 7}h16" stroke="{ink}" stroke-width=".9"/>' for j in range(3))
        + arrow(px + 54, py + 289, px + 74, py + 289, ink, 1.1, 5)
        + svg.text(px + 82, py + 286, "cited skill,", "italic", 15.5, ink) + svg.text(px + 82, py + 306, "cited evidence", "italic", 15.5, ink)
        + "</g>"
    )
    # The original document handed to the actor.
    svg.add(
        f'<g class="fade" {delay(1.9)}><path d="M902 {fy + 346}h64l14 14v46h-78z" fill="{red}" fill-opacity=".85"/>'
        + svg.text(938, fy + 370, "original", "italic", 15, "#f6eedc", "middle") + svg.text(938, fy + 390, "doc only", "italic", 15, "#f6eedc", "middle")
        + arrow(984, fy + 384, 1004, fy + 384, red, 1.3, 6)
        + "</g>"
    )

    # (4) Execution with a frozen actor.
    px, py, pw, ph = 1008, fy + 346, 140, 250
    svg.add(panel(px, py, pw, ph, slate, "4", "Execution", 1.5))
    for i, name in enumerate(["ToolQA", "AppWorld", "ALFWorld"]):
        wx, wy = px + 10 + i * 6, py + 44 + i * 52
        svg.add(
            f'<g class="fade" {delay(1.7 + i * 0.1)}><rect x="{wx}" y="{wy}" width="112" height="44" rx="3" fill="#f6efdf" stroke="{ink}" stroke-width="1.1"/>'
            f'<path d="M{wx} {wy + 11}H{wx + 112}" stroke="{ink}" stroke-width=".9"/>'
            + "".join(f'<circle cx="{wx + 8 + d * 7}" cy="{wy + 5.5}" r="1.7" fill="{ink}"/>' for d in range(3))
            + svg.text(wx + 56, wy + 33, name, "serif", 17, ink, "middle")
            + "</g>"
        )
    svg.add(f'<g class="fade" {delay(2.0)}>' + svg.text(px + pw / 2, py + 228, "frozen actor", "serif", 18, ink, "middle") + "</g>")

    # Between rounds: support tasks only.
    px, py, pw, ph = 296, fy + 484, 698, 112
    svg.add(
        f'<g class="fade" {delay(2.0)}><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="6" fill="{slate}" fill-opacity=".08" stroke="{slate}" stroke-width="1.4"/>'
        + svg.text(px + 14, py + 28, "Between rounds: support only", "serif", 19, ink)
        + svg.text(px + pw - 14, py + 28, "frozen at test time", "italic", 16, lead, "end")
        + "</g>"
    )
    steps = [("Publish", "1"), ("Fit KeyOpt", "2"), ("Filter", "3"), ("Record", "3"), ("Outcomes", "4")]
    bw, gap = 118, 18
    svg.style("@keyframes back{to{stroke-dashoffset:-22}}", ".back{animation:back 2.4s linear infinite}")
    for i, (step, n) in enumerate(steps):
        bx = px + 14 + i * (bw + gap)
        svg.add(
            f'<g class="fade" {delay(2.1 + i * 0.08)}><rect x="{bx}" y="{py + 42}" width="{bw}" height="54" rx="4" fill="#f6efdf" stroke="{ink}" stroke-width="1.2"/>'
            + svg.text(bx + bw / 2, py + 76, step, "serif", 18, ink, "middle")
            + f'<circle cx="{bx + bw - 8}" cy="{py + 44}" r="10" fill="#3a4458"/>' + svg.text(bx + bw - 8, py + 49, n, "serif", 13, "#f3ead6", "middle")
            + "</g>"
        )
        if i:
            svg.add(arrow(bx - 2, py + 69, bx - gap + 3, py + 69, violet if i > 2 else blue, 1.3, 6, f'class="fade" {delay(2.2 + i * 0.08)}'))
    svg.add(
        f'<path class="back" d="M1008 {py + 69}H{px + 14 + 5 * (bw + gap) - gap + 2}" stroke="{slate}" stroke-width="1.4" stroke-dasharray="6 5" fill="none"/>',
        f'<path class="back" d="M{px + 14 + bw / 2} {py + 42}V{fy + 66 + 404 + 4}" stroke="{ochre}" stroke-width="1.4" stroke-dasharray="6 5" fill="none"/>',
    )
    svg.add("</g>", f'<path d="{sheet}" fill="none" stroke="#b9a37d" stroke-width="1.2"/>')
    svg.add(svg.text(1134, 82, "Plate II", "allsc", 15, lead, "end", tracking=2.4))
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
