"""Assemble every SVG and the README that places them."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from . import chrome, featured, projects, pulse
from .theme import AUTOKEEPER, COMPSKILL, DEEP, FPGA, HBALL, LEROBOT, NAILONG, PAGE, PRIZES, SEIYUU, Palette, button

USER = "satoshinji2992"
GH = f"https://github.com/{USER}"


@dataclass
class Link:
    label: str
    href: str
    alt: str


@dataclass
class Card:
    name: str
    href: str
    alt: str
    links: list[Link] = field(default_factory=list)
    pal: Palette = PAGE


FEATURED = [
    Card("autokeeper", f"{GH}/autokeeper",
         "AutoKeeper: play Call of Cthulhu 7e with an AI keeper, in the terminal or the browser",
         [Link("Repository", f"{GH}/autokeeper", "AutoKeeper repository"),
          Link("Latest release", f"{GH}/autokeeper/releases/latest", "Latest AutoKeeper release"),
          Link("Website", f"https://{USER}.github.io/autokeeper/", "AutoKeeper website")], AUTOKEEPER),
    Card("compskill", f"{GH}/CompSkill",
         "CompSkill: compiling execution experience for skill retrieval; first-author paper, code and compressor weights",
         [Link("Code and weights", f"{GH}/CompSkill", "CompSkill repository")], COMPSKILL),
    Card("deep-learning", f"{GH}/quickly_access_to_deeplearning",
         "From y = ax + b to MiniMind: an open deep learning textbook adopted for a university elective",
         [Link("Repository", f"{GH}/quickly_access_to_deeplearning", "Deep learning course repository"),
          Link("Read online", f"https://{USER}.github.io/quickly_access_to_deeplearning/", "Deep learning course website")], DEEP),
]

PROJECTS = [
    Card("seiyuumatch", "https://seiyuumatch.org", "SeiyuuMatch: face retrieval over 119 voice actors, live website",
         [Link("seiyuumatch.org", "https://seiyuumatch.org", "SeiyuuMatch website"),
          Link("Source", f"{GH}/SeiyuuMatch", "SeiyuuMatch source")], SEIYUU),
    Card("lerobot", "https://github.com/huggingface/lerobot/pull/2792",
         "LeRobot: merged upstream pull request 2792 for asynchronous inference",
         [Link("PR #2792", "https://github.com/huggingface/lerobot/pull/2792", "Merged LeRobot pull request 2792"),
          Link("Fork", f"{GH}/lerobot", "LeRobot fork")], LEROBOT),
    Card("hball", f"{GH}/H_ball", "H_ball and servo: electronics design contest builds with MaixCAM vision and STM32 control",
         [Link("H_ball", f"{GH}/H_ball", "H_ball repository"),
          Link("servo", f"{GH}/servo", "servo repository")], HBALL),
    Card("nailong", f"{GH}/naiLongRacing/tree/openvela", "naiLongRacing: a pseudo-3D racer in C on openvela",
         [Link("openvela branch", f"{GH}/naiLongRacing/tree/openvela", "naiLongRacing openvela branch"),
          Link("Repository", f"{GH}/naiLongRacing", "naiLongRacing repository")], NAILONG),
    Card("fpga", f"{GH}/fpga_cpu", "FPGA RISC-V CPU: RV32IM five-stage pipeline on a Spartan-6 board",
         [Link("fpga_cpu", f"{GH}/fpga_cpu", "fpga_cpu repository")], FPGA),
    Card("prizes", f"https://{USER}.github.io", "Prizes: RoboMaster University League and CUMCM national second prizes, electronics design contest provincial prizes",
         [Link("Homepage", f"https://{USER}.github.io", "Academic homepage")], PRIZES),
]

# Buttons share one displayed height: design width = 50 * displayed width / 34.
BUTTON_WIDTHS = {24: 300, 32: 400, 49: 612}


def link_width(card: Card) -> int:
    """Percent of the README width each of the card's buttons takes."""
    if card in PROJECTS:
        return 49 if len(card.links) == 1 else 24
    return 32 if len(card.links) == 3 else 49


SECTION_META = [
    "agents, research and teaching",
    "the web, robots and hardware",
    "kept daily by GitHub Actions",
    "and what each was used for",
]


def build(data: dict) -> tuple[dict[str, str], str]:
    files: dict[str, str] = {"header.svg": chrome.header(data), "footer.svg": chrome.footer(data)}
    for i, (_, _, anchor) in enumerate(chrome.NAV):
        files[f"nav-{anchor}.svg"] = chrome.nav(i)
        files[f"section-{anchor}.svg"] = chrome.section(i, SECTION_META[i])
    renderers = {
        "autokeeper": featured.autokeeper, "compskill": featured.compskill, "deep-learning": featured.deep_learning,
        "seiyuumatch": projects.seiyuumatch, "lerobot": projects.lerobot, "hball": projects.hball,
        "nailong": projects.nailong, "fpga": projects.fpga, "prizes": projects.prizes,
    }
    if not data.get("release"):
        # No published release: drop the release button rather than link to an empty page.
        for card in FEATURED:
            card.links = [link for link in card.links if "/releases/" not in link.href]
    for card in FEATURED + PROJECTS:
        files[f"card-{card.name}.svg"] = renderers[card.name](data)
        for link in card.links:
            files[button_file(card, link)] = button(link.label, card.pal, BUTTON_WIDTHS[link_width(card)])
    files["almanac.svg"] = pulse.almanac(data)
    files["instruments.svg"] = pulse.instruments(data)
    return files, readme(files, data)


def button_file(card: Card, link: Link) -> str:
    slug = "-".join("".join(c if c.isalnum() else " " for c in link.label.lower()).split())
    return f"btn-{card.name}-{slug}.svg"


def src(files: dict[str, str], name: str) -> str:
    digest = hashlib.sha1(files[name].encode("utf-8")).hexdigest()[:10]
    return f"./assets/{name}?v={digest}"


def img(files: dict[str, str], name: str, width: str, alt: str) -> str:
    return f'<img src="{src(files, name)}" width="{width}" alt="{alt}">'


def readme(files: dict[str, str], data: dict) -> str:
    out = [
        "<!-- Generated by scripts/render_profile.py; edit the script or data/status.json, not this file. -->",
        "",
        '<p align="center">',
        f'  {img(files, "header.svg", "100%", "Agents, reinforcement learning, robotics")}',
        "</p>",
        "",
        '<p align="center">',
    ]
    for numeral, label, anchor in chrome.NAV:
        out.append(f'  <a href="#{anchor}">{img(files, f"nav-{anchor}.svg", "24%", f"{numeral}. {label}")}</a>')
    out += ["</p>", ""]

    def section(index: int) -> None:
        numeral, label, anchor = chrome.NAV[index]
        out.extend([
            f'<a name="{anchor}"></a>',
            '<p align="center">',
            f'  {img(files, f"section-{anchor}.svg", "100%", f"{numeral}. {label}")}',
            "</p>",
            "",
        ])

    section(0)
    for card in FEATURED:
        width = f"{link_width(card)}%"
        out += [
            '<p align="center">',
            f'  <a href="{card.href}">{img(files, f"card-{card.name}.svg", "100%", card.alt)}</a><br>',
        ]
        for link in card.links:
            out.append(f'  <a href="{link.href}">{img(files, button_file(card, link), width, link.alt)}</a>')
        out += ["</p>", ""]

    section(1)
    for left, right in zip(PROJECTS[::2], PROJECTS[1::2]):
        out += [
            '<p align="center">',
            f'  <a href="{left.href}">{img(files, f"card-{left.name}.svg", "49%", left.alt)}</a>',
            f'  <a href="{right.href}">{img(files, f"card-{right.name}.svg", "49%", right.alt)}</a><br>',
        ]
        for card in (left, right):
            width = f"{link_width(card)}%"
            for link in card.links:
                out.append(f'  <a href="{link.href}">{img(files, button_file(card, link), width, link.alt)}</a>')
        out += ["</p>", ""]

    section(2)
    out += [
        '<p align="center">',
        f'  {img(files, "almanac.svg", "100%", "Almanac: a year of contributions, recent activity, languages and the latest AutoKeeper release")}',
        "</p>",
        "",
    ]
    section(3)
    out += [
        '<p align="center">',
        f'  {img(files, "instruments.svg", "100%", "Instruments: the tools behind these projects and what each was used for")}',
        "</p>",
        "",
        '<p align="center">',
        f'  <a href="#featured">{img(files, "footer.svg", "100%", "Back to top")}</a>',
        "</p>",
        "",
    ]
    out += text_version(data)
    return "\n".join(out)


def text_version(data: dict) -> list[str]:
    release = data.get("release") or {}
    cal = data["calendar"]
    rows = [
        f"- **AutoKeeper**: Call of Cthulhu 7e with an AI keeper, terminal or browser."
        + (f" Latest release {release['tag']}." if release.get("tag") else "")
        + f" [Repository]({GH}/autokeeper)",
        f"- **CompSkill**: compiling execution experience for skill retrieval; first-author paper, code and compressor weights. [Repository]({GH}/CompSkill)",
        f"- **From y = ax + b to MiniMind**: an open deep learning textbook, adopted for a university elective. [Repository]({GH}/quickly_access_to_deeplearning)",
        "- **SeiyuuMatch**: face retrieval over 119 voice actors. [seiyuumatch.org](https://seiyuumatch.org)",
        "- **LeRobot**: merged upstream fix for asynchronous inference. [PR #2792](https://github.com/huggingface/lerobot/pull/2792)",
        f"- **H_ball + servo**: electronics design contest builds, MaixCAM vision and STM32 control. [H_ball]({GH}/H_ball) · [servo]({GH}/servo)",
        f"- **naiLongRacing**: a pseudo-3D racer in C on openvela. [openvela branch]({GH}/naiLongRacing/tree/openvela)",
        f"- **FPGA CPU**: RV32IM five-stage pipeline on a Spartan-6 board. [fpga_cpu]({GH}/fpga_cpu)",
        "- **Prizes**: RoboMaster University League and CUMCM (China Undergraduate Mathematical Contest in Modeling), national 2nd (2026); electronics design contest, provincial 2nd (2026) and 3rd (2025).",
        f"- **Almanac**: {cal['total']} contributions in the last year; {data['stars']} stars across {data['public_repos']} public repositories.",
    ]
    return ["<details>", "<summary>Text version</summary>", "", *rows, "", "</details>", ""]
