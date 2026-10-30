"""The almanac (a year of contributions, a ledger, languages, the latest edition) and the instruments index."""

from __future__ import annotations

import math
from datetime import date, timedelta

from .data import long_date, short_date
from .svg import Svg, delay, measure, num
from .theme import GOLD, PAGE, Palette, Plate, kicker, ornament_rule, torn_rect

ALMANAC = Palette("#0e0c0a", "#16130f", "#2d2721", "#e8dfcc", "#9a9081", GOLD, "#86ab9b", "#b0634a")
# Muted pigments for the language swatches.
PIGMENTS = ["#b88a92", "#86ab9b", GOLD, "#b0634a", "#9a8bb8", "#cdbf9f", "#7d93a0", "#a07850"]


def _polar(cx: float, cy: float, r: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def almanac(data: dict) -> str:
    pal = ALMANAC
    w, h = 1200, 620
    svg = Svg(w, h, "Almanac: a year of contributions, the recent ledger, languages and AutoKeeper's latest edition")
    plate = Plate(svg, pal)
    plate.open()
    svg.add(
        kicker(svg, 52, 66, "Almanac · from the GitHub API", GOLD),
        svg.text(w - 52, 66, f"Refreshed {long_date(data['refreshed'] + 'T00:00:00Z')}", "italic", 21, pal.dim, "end"),
    )

    # The year as a ring: one spoke per week, log scaled, clockwise from the top.
    cal = data["calendar"]
    counts = cal["counts"]
    start = date.fromisoformat(cal["start"])
    weeks = [sum(counts[i:i + 7]) for i in range(0, len(counts), 7)]
    peak = max(weeks) or 1
    busiest = sorted(weeks, reverse=True)[min(2, len(weeks) - 1)]
    cx, cy, inner, depth = 300, 350, 104, 84
    step = 360 / len(weeks)
    spokes = []
    for k, total in enumerate(weeks):
        a = k * step + step / 2
        length = 3 if total == 0 else max(8, math.log1p(total) / math.log1p(peak) * depth)
        x0, y0 = _polar(cx, cy, inner, a)
        x1, y1 = _polar(cx, cy, inner + length, a)
        color = pal.line if total == 0 else pal.accent if total >= busiest else pal.accent2
        spokes.append(
            f'<path class="spoke" style="animation-delay:{num(0.4 + k * 0.03)}s" d="M{num(x0)} {num(y0)}L{num(x1)} {num(y1)}" '
            f'stroke="{color}" stroke-width="7" stroke-linecap="round" pathLength="1"/>'
        )
    months = []
    for k in range(len(weeks)):
        day = start + timedelta(days=7 * k)
        if day.day <= 7:
            a = k * step
            lx, ly = _polar(cx, cy, inner + depth + 34, a + step / 2)
            months.append(svg.text(lx, ly + 5, day.strftime("%b"), "italic", 17, pal.dim, "middle"))
            tx0, ty0 = _polar(cx, cy, inner + depth + 12, a)
            tx1, ty1 = _polar(cx, cy, inner + depth + 20, a)
            months.append(f'<path d="M{num(tx0)} {num(ty0)}L{num(tx1)} {num(ty1)}" stroke="{GOLD}" stroke-opacity=".5" stroke-width="1.2"/>')
    outer = inner + depth + 16

    def tick(d: int) -> str:
        a0 = _polar(cx, cy, outer + 40, d)
        a1 = _polar(cx, cy, outer + (47 if d % 30 == 0 else 43), d)
        return f"M{num(a0[0])} {num(a0[1])}L{num(a1[0])} {num(a1[1])}"

    top = max(range(len(weeks)), key=lambda k: weeks[k])
    px, py = _polar(cx, cy, inner + depth + 4, top * step + step / 2)
    svg.style(
        "@keyframes spoke{from{stroke-dasharray:1 1;stroke-dashoffset:1}to{stroke-dasharray:1 1;stroke-dashoffset:0}}",
        ".spoke{animation:spoke 1.1s cubic-bezier(.2,.8,.2,1) both}",
    )
    svg.add(
        f'<circle cx="{cx}" cy="{cy}" r="{inner - 8}" fill="none" stroke="{GOLD}" stroke-opacity=".35" stroke-width="1.2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{outer}" fill="none" stroke="{GOLD}" stroke-opacity=".25" stroke-width="1.2"/>',
        f'<g opacity=".5"><g class="spin" style="animation-duration:240s"><circle cx="{cx}" cy="{cy}" r="{outer + 40}" fill="none" stroke="{GOLD}" stroke-opacity=".5" stroke-width="1.2"/>'
        f'<path d="{"".join(tick(d) for d in range(0, 360, 5))}" stroke="{GOLD}" stroke-width="1.1"/></g></g>',
        "".join(spokes),
        "".join(months),
        f'<g class="fade" {delay(2.2)}><circle cx="{num(px)}" cy="{num(py)}" r="6" fill="none" stroke="{GOLD}" stroke-width="1.5"/></g>',
        f'<g class="rise" {delay(0.3)}>'
        + svg.text(cx, cy + 4, f"{int(cal['total']):,}", "serif", 54, pal.ink, "middle")
        + svg.text(cx, cy + 34, "contributions", "allsc", 16, GOLD, "middle", tracking=2)
        + svg.text(cx, cy - 46, "the last year", "italic", 19, pal.dim, "middle")
        + "</g>",
    )
    busiest_day = (start + timedelta(days=7 * top)).strftime("%d %b").lstrip("0")
    svg.add(f'<g class="fade" {delay(2.2)}>' + svg.text(cx, cy + 66, f"busiest week, {busiest_day}: {weeks[top]}", "italic", 16, pal.dim, "middle") + "</g>")

    # The ledger.
    lx, lw = 640, 508
    svg.add(
        f'<g class="fade" {delay(0.6)}>' + svg.text(lx, 128, f"{data['stars']} stars across {data['public_repos']} public repositories", "italic", 22, pal.ink) + "</g>",
        ornament_rule(svg, lx, lx + lw, 154, GOLD, "⁂", 20, 0.8),
        kicker(svg, lx, 194, "Ledger", pal.accent2, 17, 0.9),
    )
    for i, item in enumerate(data.get("activity", [])[:4]):
        y = 232 + i * 40
        day = short_date(item["date"] + "T00:00:00Z")[:6]
        svg.add(
            f'<g class="rise" {delay(1.0 + i * 0.1)}>'
            + svg.text(lx, y, day, "allsc", 16, GOLD, tracking=1.2)
            + svg.text(lx + 74, y, item["repo"], "serif", 23, pal.ink)
            + svg.text(lx + 74 + measure(item["repo"], "serif", 23) + 12, y, item["summary"], "italic", 18, pal.dim)
            + "</g>"
        )

    # Languages, as pigment swatches sized by repository count.
    languages = data.get("languages", [])[:7]
    total = sum(count for _, count in languages) or 1
    y0 = 418
    svg.add(kicker(svg, lx, y0, "Languages · by repository", pal.accent2, 17, 1.0))
    sx = lx
    swatches, legend = [], []
    lgx, lgy = lx, y0 + 62
    for i, (name, count) in enumerate(languages):
        seg = lw * count / total
        swatches.append(
            f'<rect class="grow" style="animation-delay:{num(1.1 + i * 0.08)}s" x="{num(sx)}" y="{y0 + 16}" width="{num(max(seg - 4, 3))}" height="14" rx="1" fill="{PIGMENTS[i]}"/>'
        )
        sx += seg
        label = f"{name} {count}"
        width = 20 + measure(label, "italic", 18)
        if lgx + width > lx + lw:
            lgx, lgy = lx, lgy + 26
        legend.append(f'<rect x="{num(lgx)}" y="{lgy - 11}" width="10" height="10" fill="{PIGMENTS[i]}"/>' + svg.text(lgx + 18, lgy, label, "italic", 18, pal.ink))
        lgx += width + 18
    svg.add("".join(swatches), f'<g class="fade" {delay(1.4)}>' + "".join(legend) + "</g>")

    # The latest AutoKeeper edition, as a tag tied with string.
    release = data.get("release")
    if release:
        stamp = f"{release.get('tag', '')} · {short_date(release.get('published_at'))[:6]}"
    else:
        stamp = short_date(data["repos"].get("autokeeper", {}).get("pushed_at"))
    tx, ty, tw, th = lx + 196, 524, 312, 70
    tag = torn_rect(tx, ty, tw, th, 1.6, seed=66, edges="r")
    svg.add(
        f'<g class="rise" {delay(1.5)}>'
        f'<path d="M{tx - 40} {ty + 6}C{tx - 22} {ty + 18} {tx - 10} {ty + 28} {tx + 14} {ty + th / 2}" fill="none" stroke="#c9b48a" stroke-width="1.4" opacity=".7"/>'
        f'<path d="{tag}" fill="#e6d9bd"/><circle cx="{tx + 14}" cy="{ty + th / 2}" r="5" fill="{pal.bg}" stroke="#a08a5c" stroke-width="1.2"/>'
        + svg.text(tx + 32, ty + 27, "Latest edition" if release else "Last revised", "allsc", 15, "#8f3a2c", tracking=1.6)
        + svg.text(tx + 32, ty + 56, "AutoKeeper", "serif", 26, "#2a2017")
        + svg.text(tx + tw - 14, ty + 56, stamp, "italic", 19, "#5a4a36", "end")
        + "</g>"
    )
    plate.close()
    return svg.render()


INSTRUMENTS = [
    ("Learning", "#c08d97", [
        ("PyTorch", "PPO, LoRA, the MiniMind block"),
        ("NumPy", "networks by hand, blocks 1–2"),
        ("LangGraph", "AutoKeeper's agents"),
        ("TensorRT", "YOLO on a Jetson Orin NX"),
    ]),
    ("Robots", "#86ab9b", [
        ("LeRobot", "ACT and π0 on a real arm"),
        ("Isaac Lab", "wheel-leg PPO policies"),
        ("ROS 2", "auto-aim and MPC nodes"),
        ("MuJoCo", "sim-to-sim checks"),
    ]),
    ("Systems", GOLD, [
        ("Python", "most of everything above"),
        ("C / C++", "firmware, a game core"),
        ("Linux", "WSL, Nginx and systemd"),
        ("Actions", "CI for the course and this page"),
    ]),
    ("Hardware", "#b56a4c", [
        ("STM32", "gimbal PID, servo PWM"),
        ("MaixCAM", "YOLO11n at the edge"),
        ("Jetson", "TensorRT inference"),
        ("Verilog", "an RV32IM pipeline"),
    ]),
]


def instruments(data: dict) -> str:
    pal = PAGE
    w, h = 1200, 420
    svg = Svg(w, h, "Instruments: the tools behind these projects, and what each one was used for")
    plate = Plate(svg, pal)
    plate.open()
    col_w, x0 = 262, 52
    for g, (group, color, items) in enumerate(INSTRUMENTS):
        x = x0 + g * (col_w + 20)
        svg.add(
            kicker(svg, x, 70, group, color, 18, 0.1 + g * 0.1),
            f'<path class="draw" {delay(0.2 + g * 0.1)} pathLength="1" d="M{x} 86H{x + col_w - 16}" stroke="{color}" stroke-opacity=".55" stroke-width="1.3" fill="none"/>',
        )
        for i, (name, use) in enumerate(items):
            y = 134 + i * 72
            svg.add(
                f'<g class="rise" {delay(0.3 + g * 0.1 + i * 0.07)}>'
                f'<path d="M{x + 3.5} {y - 15.5}L{x + 7} {y - 12}L{x + 3.5} {y - 8.5}L{x} {y - 12}Z" fill="{color}"/>'
                + svg.text(x + 20, y, name, "serif", 29, pal.ink)
                + svg.text(x + 20, y + 26, use, "italic", 19, pal.dim)
                + "</g>"
            )
    plate.close()
    return svg.render()
