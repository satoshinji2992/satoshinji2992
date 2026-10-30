"""The live panel (contributions, activity, languages, latest release) and the toolkit index."""

from __future__ import annotations

import math
from datetime import date, timedelta

from .data import short_date
from .svg import Svg, cap_height, delay, measure, num
from .theme import PAGE, Palette, Plate, kicker

# Cool graphite, so the one data plate sits apart from the warm project plates.
PULSE = Palette("#0f1114", "#15181d", "#272c34", "#e8e6e1", "#8c9099", "#d69da9", "#66bca5", "#f0a945")
SERIES = ["#d69da9", "#66bca5", "#f0a945", "#e48a5b", "#bda8e4", "#d3ad60", "#a3cad8", "#e8a79e"]


def odometer(svg: Svg, x: float, y: float, value: int, color: str, at: float = 0.3) -> tuple[str, float]:
    """Digit windows that roll up to `value`; returns markup and total width."""
    text = f"{value:,}"
    cell_w, cell_h, size = 46, 72, 46
    out, cx = [], x
    for i, char in enumerate(text):
        if char == ",":
            out.append(svg.text(cx + 1, y + cell_h - 6, ",", "mono-b", 30, PULSE.dim))
            cx += 16
            continue
        clip = svg.uid("digit")
        svg.define(f'<clipPath id="{clip}"><rect x="{cx}" y="{y}" width="{cell_w}" height="{cell_h}" rx="6"/></clipPath>')
        digit = int(char)
        sequence = [str(n % 10) for n in range(digit + 11)]
        final = (len(sequence) - 1) * cell_h
        baseline = y + cell_h / 2 + cap_height("mono-b", size) / 2
        strip = "".join(svg.text(cx + cell_w / 2, baseline + k * cell_h, n, "mono-b", size, color, "middle") for k, n in enumerate(sequence))
        name = svg.uid("roll").replace("-", "")
        svg.style(
            f"@keyframes {name}{{from{{transform:translateY(0)}}to{{transform:translateY(-{final}px)}}}}",
            f".{name}{{animation:{name} {num(1.6 + i * 0.22)}s cubic-bezier(.2,.8,.2,1) {num(at)}s both}}",
        )
        out.append(
            f'<rect x="{cx}" y="{y}" width="{cell_w}" height="{cell_h}" rx="6" fill="#0a0c0f" stroke="{PULSE.line}"/>'
            f'<g clip-path="url(#{clip})"><g class="{name}" transform="translate(0 -{final})">{strip}</g>'
            f'<rect x="{cx}" y="{y}" width="{cell_w}" height="{num(cell_h / 2)}" fill="#fff" opacity=".035"/></g>'
            f'<path d="M{cx} {num(y + cell_h / 2)}h{cell_w}" stroke="#000" stroke-opacity=".5"/>'
        )
        cx += cell_w + 6
    return "".join(out), cx - x


def pulse(data: dict) -> str:
    pal = PULSE
    w, h = 1200, 600
    svg = Svg(w, h, "Pulse: contributions over the last year, recent activity, languages and the latest release")
    plate = Plate(svg, pal)
    plate.open()
    svg.add(
        kicker(svg, 40, 62, "PULSE  ·  LIVE FROM THE GITHUB API", pal.accent),
        svg.text(w - 40, 62, f"REFRESHED {short_date(data['refreshed'] + 'T00:00:00Z').upper()}", "mono-b", 12, pal.dim, "end", tracking=2.2),
        f'<path d="M40 82H{w - 40}" stroke="{pal.line}"/>',
    )

    cal = data["calendar"]
    markup, width = odometer(svg, 40, 112, int(cal["total"]), pal.ink)
    svg.add(
        markup,
        f'<g class="fade" {delay(0.8)}>'
        + svg.text(42, 222, "contributions in the last year", "italic", 24, "#c8c5be")
        + svg.text(42, 252, f"{data['stars']} stars across {data['public_repos']} public repositories", "mono", 13, pal.dim)
        + "</g>",
    )

    # One bar per week, log scaled so quiet months still show next to busy ones.
    counts = cal["counts"]
    start = date.fromisoformat(cal["start"])
    weeks = [sum(counts[i:i + 7]) for i in range(0, len(counts), 7)]
    peak = max(weeks) or 1
    bx0, base, bar_w, gap, tall = 420, 252, 9, 5, 136
    bars, months = [], []
    busiest = sorted(weeks, reverse=True)[2] if len(weeks) > 2 else peak
    for k, total in enumerate(weeks):
        height = 2 if total == 0 else max(5, math.log1p(total) / math.log1p(peak) * tall)
        color = pal.line if total == 0 else pal.accent3 if total >= busiest else pal.accent2
        x = bx0 + k * (bar_w + gap)
        bars.append(
            f'<rect class="bar" style="animation-delay:{num(0.4 + k * 0.025)}s" x="{x}" y="{num(base - height)}" '
            f'width="{bar_w}" height="{num(height)}" rx="2" fill="{color}"/>'
        )
        week_start = start + timedelta(days=7 * k)
        if week_start.day <= 7:
            months.append(svg.text(x, base + 22, week_start.strftime("%b").upper(), "mono", 11, pal.dim, tracking=1))
    top = max(range(len(weeks)), key=lambda k: weeks[k])
    top_x = bx0 + top * (bar_w + gap) + bar_w / 2
    top_y = base - tall
    week_of = (start + timedelta(days=7 * top)).strftime("%d %b")
    svg.style(
        "@keyframes bar{from{transform:scaleY(0)}}",
        ".bar{animation:bar 1s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:50% 100%}",
    )
    note = f"{weeks[top]} in the week of {week_of}"
    svg.add(
        f'<path d="M{bx0} {base + 0.5}H{bx0 + len(weeks) * (bar_w + gap) - gap}" stroke="{pal.line}"/>',
        "".join(bars),
        "".join(months),
        f'<g class="fade" {delay(2.0)}><path d="M{num(top_x)} {num(top_y - 8)}V{num(top_y - 26)}H{num(top_x - 14)}" fill="none" stroke="{pal.dim}"/>'
        + svg.text(top_x - 20, top_y - 22, note, "mono", 12, pal.dim, "end")
        + "</g>",
    )

    # Recent activity.
    y0 = 334
    svg.add(f'<path d="M40 304H{w - 40}" stroke="{pal.line}"/>', kicker(svg, 40, y0, "RECENT", pal.accent2, 12, 0.9))
    for i, item in enumerate(data.get("activity", [])[:4]):
        y = y0 + 48 + i * 50
        day = short_date(item["date"] + "T00:00:00Z")[:6].upper()
        svg.add(
            f'<g class="rise" {delay(1.0 + i * 0.1)}>'
            f'<circle cx="46" cy="{y - 5}" r="4" fill="{SERIES[i % 4]}"/>'
            + (f'<path d="M46 {y + 3}V{y + 37}" stroke="{pal.line}"/>' if i < 3 else "")
            + svg.text(62, y, day, "mono-b", 12, pal.dim, tracking=1.4)
            + svg.text(140, y + 1, item["repo"], "serif", 23, pal.ink)
            + svg.text(140 + measure(item["repo"], "serif", 23) + 14, y, item["summary"], "mono", 12.5, pal.dim)
            + "</g>"
        )

    # Languages by repository count.
    lx, lw = 690, 470
    languages = data.get("languages", [])[:7]
    total = sum(count for _, count in languages) or 1
    svg.add(kicker(svg, lx, y0, "LANGUAGES  ·  BY REPOSITORY", pal.accent3, 12, 0.9))
    cx = lx
    segments, legend = [], []
    legend_x, legend_y = lx, y0 + 66
    for i, (name, count) in enumerate(languages):
        seg_w = lw * count / total
        segments.append(
            f'<rect class="grow" style="animation-delay:{num(1.1 + i * 0.08)}s" x="{num(cx)}" y="{y0 + 22}" width="{num(max(seg_w - 3, 2))}" height="12" rx="2" fill="{SERIES[i]}"/>'
        )
        cx += seg_w
        item_w = 26 + measure(name, "mono", 12) + measure(str(count), "mono", 12)
        if legend_x + item_w > lx + lw:
            legend_x, legend_y = lx, legend_y + 26
        lxx, lyy = legend_x, legend_y
        legend_x += item_w + 22
        legend.append(
            f'<circle cx="{lxx + 5}" cy="{lyy - 4}" r="4.5" fill="{SERIES[i]}"/>'
            + svg.text(lxx + 16, lyy, name, "mono", 12, pal.ink)
            + svg.text(lxx + 20 + measure(name, "mono", 12), lyy, str(count), "mono", 12, pal.dim)
        )
    svg.add("".join(segments), f'<g class="fade" {delay(1.4)}>' + "".join(legend) + "</g>")

    # Latest AutoKeeper release, as a ticket stub.
    release = data.get("release") or {}
    tx, ty, tw, th = lx, 452, lw, 92
    notch = 10
    ticket = (
        f"M{tx + 8} {ty}H{tx + tw - 8}Q{tx + tw} {ty} {tx + tw} {ty + 8}V{ty + th / 2 - notch}"
        f"A{notch} {notch} 0 0 0 {tx + tw} {ty + th / 2 + notch}V{ty + th - 8}Q{tx + tw} {ty + th} {tx + tw - 8} {ty + th}"
        f"H{tx + 8}Q{tx} {ty + th} {tx} {ty + th - 8}V{ty + th / 2 + notch}A{notch} {notch} 0 0 0 {tx} {ty + th / 2 - notch}"
        f"V{ty + 8}Q{tx} {ty} {tx + 8} {ty}Z"
    )
    stub = tx + tw - 132
    svg.add(
        f'<g class="rise" {delay(1.5)}><path d="{ticket}" fill="#1b1311" stroke="#4a2c26"/>'
        f'<path d="M{stub} {ty + 10}V{ty + th - 10}" stroke="#4a2c26" stroke-dasharray="3 4"/>'
        + svg.text(tx + 22, ty + 30, "LATEST RELEASE", "mono-b", 11, "#c95c4d", tracking=2.4)
        + svg.text(tx + 22, ty + 68, "AutoKeeper", "serif", 30, "#ecdfc8")
        + svg.text(tx + 22 + measure("AutoKeeper", "serif", 30) + 14, ty + 67, release.get("tag", ""), "mono-b", 15, "#a6a268", tracking=1)
        + svg.text(stub + 66, ty + 42, short_date(release.get("published_at"))[:6].upper(), "mono-b", 15, "#ecdfc8", "middle", tracking=1.5)
        + svg.text(stub + 66, ty + 62, short_date(release.get("published_at"))[-4:], "mono", 12, "#a89785", "middle", tracking=2)
        + "</g>"
    )
    plate.close()
    return svg.render()


TOOLKIT = [
    ("LEARNING", "#d69da9", [
        ("PyTorch", "PPO, LoRA, the MiniMind block"),
        ("NumPy", "networks by hand, blocks 1–2"),
        ("LangGraph", "AutoKeeper's agents"),
        ("TensorRT", "YOLO on a Jetson Orin NX"),
    ]),
    ("ROBOTS", "#66bca5", [
        ("LeRobot", "ACT and π0 on a real arm"),
        ("Isaac Lab", "wheel-leg PPO policies"),
        ("ROS 2", "auto-aim and MPC nodes"),
        ("MuJoCo", "sim-to-sim checks"),
    ]),
    ("SYSTEMS", "#f0a945", [
        ("Python", "most of everything above"),
        ("C / C++", "firmware, a game core"),
        ("Linux", "WSL, Nginx and systemd"),
        ("Actions", "CI for the course and this page"),
    ]),
    ("HARDWARE", "#e48a5b", [
        ("STM32", "gimbal PID, servo PWM"),
        ("MaixCAM", "YOLO11n at the edge"),
        ("Jetson", "TensorRT inference"),
        ("Verilog", "an RV32IM pipeline"),
    ]),
]


def toolkit(data: dict) -> str:
    pal = PAGE
    w, h = 1200, 400
    svg = Svg(w, h, "Toolkit: the tools behind these projects, and what each one was used for")
    plate = Plate(svg, pal)
    plate.open()
    col_w, x0 = 270, 40
    for g, (group, color, items) in enumerate(TOOLKIT):
        x = x0 + g * (col_w + 20)
        svg.add(
            f'<g class="fade" {delay(0.1 + g * 0.1)}>' + svg.text(x, 66, group, "mono-b", 12, color, tracking=2.6) + "</g>",
            f'<rect x="{x}" y="80" width="{col_w - 10}" height="1" fill="{pal.line}"/>',
            f'<rect class="grow" {delay(0.2 + g * 0.1)} x="{x}" y="79.5" width="36" height="2" fill="{color}"/>',
        )
        for i, (name, use) in enumerate(items):
            y = 128 + i * 70
            svg.add(
                f'<g class="rise" {delay(0.3 + g * 0.1 + i * 0.07)}>'
                f'<rect x="{x}" y="{y - 13}" width="7" height="7" transform="rotate(45 {x + 3.5} {y - 9.5})" fill="{color}"/>'
                + svg.text(x + 20, y, name, "serif", 27, pal.ink)
                + svg.text(x + 20, y + 24, use, "mono", 12, pal.dim)
                + "</g>"
            )
    plate.close()
    return svg.render()
