#!/usr/bin/env python3
"""Generate self-hosted SVG cards and refresh live README data.

Uses only the Python standard library. GitHub Actions supplies GITHUB_TOKEN.
When the API is unavailable, the renderer falls back to data/status.json so
the profile remains available even during a temporary API failure.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "status.json"
README_PATH = ROOT / "README.md"
ASSETS_PATH = ROOT / "assets"
START_MARKER = "<!-- LIVE_PROFILE:START -->"
END_MARKER = "<!-- LIVE_PROFILE:END -->"
API_ROOT = "https://api.github.com"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def api_get(path: str, token: str | None) -> Any:
    url = path if path.startswith("http") else f"{API_ROOT}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-renderer",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_date(value: str | None) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def compact_date(value: str | None) -> str:
    parsed = parse_date(value)
    if parsed.year == 1970:
        return "unknown"
    return parsed.strftime("%d %b %Y")


def short_repo(full_name: str, username: str) -> str:
    prefix = f"{username}/"
    return full_name[len(prefix):] if full_name.startswith(prefix) else full_name


def safe_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def truncate(value: str, limit: int) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip() + "…"


def summarize_event(event: dict[str, Any], username: str) -> dict[str, str] | None:
    event_type = event.get("type", "")
    repo_full = event.get("repo", {}).get("name", "")
    if not repo_full or repo_full == f"{username}/{username}":
        return None

    payload = event.get("payload", {})
    repo = short_repo(repo_full, username)

    if event_type == "PushEvent":
        count = int(payload.get("size") or len(payload.get("commits", [])) or 1)
        summary = f"pushed {count} commit{'s' if count != 1 else ''}"
    elif event_type == "CreateEvent":
        ref_type = payload.get("ref_type", "item")
        summary = f"created a {ref_type}"
    elif event_type == "PullRequestEvent":
        action = payload.get("action", "updated")
        summary = f"{action} a pull request"
    elif event_type == "IssuesEvent":
        action = payload.get("action", "updated")
        summary = f"{action} an issue"
    elif event_type == "IssueCommentEvent":
        summary = "commented on an issue"
    elif event_type == "ForkEvent":
        summary = "forked the repository"
    elif event_type == "WatchEvent":
        summary = "starred the repository"
    elif event_type == "ReleaseEvent":
        action = payload.get("action", "published")
        summary = f"{action} a release"
    else:
        return None

    return {
        "created_at": event.get("created_at", ""),
        "repo": repo,
        "summary": summary,
    }


def collect_live_data(config: dict[str, Any], username: str, token: str | None) -> dict[str, Any]:
    user = api_get(f"/users/{urllib.parse.quote(username)}", token)
    all_repos = api_get(
        f"/users/{urllib.parse.quote(username)}/repos"
        "?per_page=100&type=owner&sort=updated",
        token,
    )

    total_stars = sum(
        int(repo.get("stargazers_count", 0))
        for repo in all_repos
        if not repo.get("fork", False)
    )

    projects: list[dict[str, Any]] = []
    for item in config["projects"]:
        repo = api_get(
            f"/repos/{urllib.parse.quote(username)}/{urllib.parse.quote(item['repo'])}",
            token,
        )
        projects.append(
            {
                **item,
                "pushed_at": repo.get("pushed_at") or repo.get("updated_at"),
                "stars": int(repo.get("stargazers_count", 0)),
                "fork": bool(repo.get("fork", False)),
            }
        )

    events = api_get(
        f"/users/{urllib.parse.quote(username)}/events/public?per_page=100",
        token,
    )
    label_map = {item["repo"]: item["label"] for item in config["projects"]}
    activity: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in events:
        item = summarize_event(event, username)
        if item is None:
            continue
        item["repo"] = label_map.get(item["repo"], item["repo"])
        key = (item["created_at"][:10], item["repo"], item["summary"])
        if key in seen:
            continue
        seen.add(key)
        activity.append(item)
        if len(activity) == 4:
            break

    return {
        "public_repos": int(user.get("public_repos", len(all_repos))),
        "followers": int(user.get("followers", 0)),
        "total_stars": total_stars,
        "projects": projects,
        "activity": activity or config["fallback_activity"],
        "live": True,
    }


def collect_fallback_data(config: dict[str, Any]) -> dict[str, Any]:
    projects = [
        {
            **item,
            "pushed_at": item.get("fallback_pushed_at"),
            "stars": item.get("fallback_stars", 0),
            "fork": item.get("kind") == "upstream fork",
        }
        for item in config["projects"]
    ]
    return {
        **config["fallback"],
        "projects": projects,
        "activity": config["fallback_activity"],
        "live": False,
    }


def svg_text(
    x: int,
    y: int,
    value: Any,
    size: int = 16,
    fill: str = "#edf0f5",
    weight: int = 400,
    family: str = "Inter,Segoe UI,sans-serif",
    anchor: str = "start",
    spacing: float = 0,
) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'letter-spacing="{spacing}">{safe_text(value)}</text>'
    )


def svg_frame(width: int, height: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{safe_text(title)}">',
        '<defs>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '<stop offset="0" stop-color="#0b0e14"/><stop offset="1" stop-color="#11151d"/>',
        '</linearGradient>',
        '<radialGradient id="glow"><stop stop-color="#c89bad" stop-opacity=".14"/>'
        '<stop offset="1" stop-color="#c89bad" stop-opacity="0"/></radialGradient>',
        '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".72" '
        'numOctaves="3" seed="11"/><feColorMatrix values="1 0 0 0 0 0 1 0 0 0 '
        '0 0 1 0 0 0 0 0 .055 0"/><feBlend in="SourceGraphic" mode="screen"/></filter>',
        '</defs>',
        f'<rect width="{width}" height="{height}" rx="18" fill="url(#bg)"/>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" '
        'fill="none" stroke="#303744" stroke-width="2"/>',
        f'<rect width="{width}" height="{height}" rx="18" fill="transparent" filter="url(#grain)"/>',
    ]


def render_deep_learning_card(item: dict[str, Any]) -> str:
    lines = svg_frame(1200, 360, "Deep Learning from Scratch project card")
    lines += [
        '<rect x="0" y="0" width="13" height="360" rx="6" fill="#cf9caf"/>',
        '<path d="M48 62H520M48 296H520M560 34V326" stroke="#303744"/>',
        svg_text(48, 48, "01 / TUTORIAL", 14, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.5),
        svg_text(48, 128, "Deep Learning", 55, "#f3eef1", 700, "Georgia,serif"),
        svg_text(48, 190, "FROM SCRATCH", 49, "#f3eef1", 700, "Georgia,serif"),
        svg_text(50, 232, "GRADIENTS   →   RESNET   →   TRANSFORMER", 15, "#a8afbb", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.7),
        svg_text(48, 327, "implementation-first · runnable exercises · tests", 14, "#89919f"),
        '<circle cx="870" cy="178" r="145" fill="url(#glow)"/>',
        '<g stroke="#8f6d7c" fill="none" opacity=".58">',
        '<circle cx="946" cy="174" r="42"/><circle cx="946" cy="174" r="70"/>'
        '<circle cx="946" cy="174" r="98"/>',
        '<path d="M620 92L700 128 775 82 850 142 946 76 1088 104M620 258L706 218 '
        '790 268 858 214 946 274 1090 238M700 128L706 218M775 82L790 268M850 142L858 214"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(f'<circle cx="{x}" cy="{y}" r="7"/>' for x, y in [
            (620,92),(700,128),(775,82),(850,142),(946,76),(1088,104),
            (620,258),(706,218),(790,268),(858,214),(946,274),(1090,238)]),
        ''.join(f'<rect x="{720 + c*18}" y="{145 + r*18}" width="12" height="12" rx="2"/>'
                for r in range(4) for c in range(5)),
        '</g>',
        svg_text(600, 326, "NUMPY", 13, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(790, 326, f'★ {item.get("stars", 0)}', 13, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(1138, 326, compact_date(item.get("pushed_at")), 13, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_lerobot_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "LeRobot Lab project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, "02 / ROBOT LEARNING", 12, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1),
        svg_text(34, 111, "LeRobot", 39, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 153, "LAB", 39, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 190, "OBSERVE  →  REPRESENT  →  ACT", 11, "#a8afbb", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 11, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g fill="none" stroke="#596273">',
        '<rect x="294" y="82" width="78" height="132" rx="8"/>'
        '<rect x="390" y="82" width="78" height="132" rx="8"/>'
        '<rect x="486" y="82" width="78" height="132" rx="8"/>',
        '<path d="M372 148H390M468 148H486"/>',
        '<path d="M311 128L329 111 352 142 329 162 311 128M503 172L521 154 543 165"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(f'<circle cx="{x}" cy="{y}" r="5"/>' for x,y in [(311,128),(329,111),(352,142),(329,162),(503,172),(521,154),(543,165)]),
        ''.join(f'<rect x="{405+c*13}" y="{113+r*13}" width="8" height="8" rx="1"/>' for r in range(4) for c in range(4)),
        '</g>',
        svg_text(333, 237, "OBSERVE", 10, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(429, 237, "REPRESENT", 10, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(525, 237, "ACT", 10, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_seiyuu_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "SeiyuuMatch project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, "03 / COMPUTER VISION", 12, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1),
        svg_text(34, 111, "Seiyuu", 38, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 153, "MATCH", 38, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 190, "EMBED  →  COMPARE  →  RANK", 11, "#a8afbb", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 11, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g fill="none" stroke="#8f6d7c">',
        '<circle cx="350" cy="143" r="34"/><circle cx="350" cy="143" r="57"/>'
        '<circle cx="350" cy="143" r="80"/>',
        '<path d="M325 120L367 105 381 151 346 174 318 151Z"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(f'<circle cx="{x}" cy="{y}" r="5"/>' for x,y in [(325,120),(367,105),(381,151),(346,174),(318,151)]),
        '</g>',
        '<g fill="#1a202b" stroke="#394252">',
        ''.join(f'<rect x="440" y="{72+i*37}" width="118" height="25" rx="5"/>' for i in range(5)),
        '</g><g fill="#cf9caf">',
        ''.join(f'<rect x="455" y="{80+i*37}" width="{75-i*8}" height="9" rx="4"/>' for i in range(5)),
        '</g>',
        svg_text(350, 258, "FACE EMBEDDING", 10, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_profile_svg(config: dict[str, Any], data: dict[str, Any]) -> str:
    lines = svg_frame(1200, 360, "Live GitHub profile metrics")
    lines += [
        '<path d="M28 54H1172M382 74V326M802 74V326" stroke="#303744"/>',
        '<rect x="28" y="25" width="9" height="9" fill="#cf9caf"/>',
        svg_text(50, 35, "LIVE PROFILE // AUTO-REFRESHED", 14, "#9da5b2", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3),
        svg_text(1168, 35, "GITHUB ACTIONS", 12, "#737d8c", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end", spacing=1),
        svg_text(34, 92, "LAB STATUS", 12, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3),
        svg_text(34, 132, config["mode"], 27, "#edf0f5", 700),
        '<circle cx="340" cy="124" r="6" fill="#78d6c6"/>',
        svg_text(34, 165, config["now"], 13, "#89919f"),
        svg_text(34, 205, "FOCUS", 11, "#89919f", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1),
        svg_text(34, 230, config["focus"], 17, "#edf0f5", 600),
    ]
    for x, label, value in [(34,"REPOSITORIES",data.get("public_repos","—")),
                             (156,"STARS",data.get("total_stars","—")),
                             (264,"FOLLOWERS",data.get("followers","—"))]:
        lines += [svg_text(x, 274, label, 10, "#89919f", 700,
                          "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.8),
                  svg_text(x, 309, value, 25, "#edf0f5", 700)]
    lines.append(svg_text(410, 92, "PROJECT PULSE // 03", 12, "#cf9caf", 700,
                          "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3))
    for index, (item, y) in enumerate(zip(data["projects"], [126, 196, 266]), start=1):
        lines += [
            svg_text(410, y, f"0{index}", 12, "#8f6d7c", 700,
                     "ui-monospace,SFMono-Regular,Consolas,monospace"),
            svg_text(447, y, item["label"], 16, "#edf0f5", 650),
            svg_text(447, y+23, item["kind"], 12, "#89919f", 500),
            svg_text(774, y, f'★ {item.get("stars", 0)}', 11, "#89919f", 500,
                     "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
            svg_text(774, y+23, compact_date(item.get("pushed_at")), 11, "#89919f", 500,
                     "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        ]
    lines.append(svg_text(830, 92, "RECENT ACTIVITY", 12, "#cf9caf", 700,
                          "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3))
    for item, y in zip(data["activity"][:4], [126, 181, 236, 291]):
        lines += [
            f'<circle cx="838" cy="{y-6}" r="4" fill="#cf9caf"/>',
            svg_text(855, y, compact_date(item.get("created_at")), 11, "#89919f", 500,
                     "ui-monospace,SFMono-Regular,Consolas,monospace"),
            svg_text(958, y, truncate(item.get("repo", ""), 24), 13, "#edf0f5", 650),
            svg_text(855, y+22, truncate(item.get("summary", ""), 43), 12, "#89919f"),
        ]
    refreshed = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines += [svg_text(1168, 336, f"updated {refreshed}", 10, "#737d8c", 500,
                       "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"), '</svg>']
    return "\n".join(lines) + "\n"


def write_svg_assets(config: dict[str, Any], data: dict[str, Any]) -> None:
    ASSETS_PATH.mkdir(parents=True, exist_ok=True)
    outputs = {
        "project-deep-learning.svg": render_deep_learning_card(data["projects"][0]),
        "project-lerobot.svg": render_lerobot_card(data["projects"][1]),
        "project-seiyuumatch.svg": render_seiyuu_card(data["projects"][2]),
        "profile-metrics.svg": render_profile_svg(config, data),
    }
    for filename, content in outputs.items():
        (ASSETS_PATH / filename).write_text(content, encoding="utf-8")


def render_readme_section(
    config: dict[str, Any], data: dict[str, Any], username: str
) -> str:
    """Embed the rendered component and keep an accessible text fallback."""
    projects: list[str] = []
    for index, item in enumerate(data["projects"], start=1):
        repo = urllib.parse.quote(item["repo"])
        url = f"https://github.com/{urllib.parse.quote(username)}/{repo}"
        projects.append(
            f'<p><code>0{index}</code> '
            f'<a href="{url}"><strong>{safe_text(item["label"])}</strong></a><br>'
            f'<sub>{safe_text(item["kind"])} · ★ {item.get("stars", 0)} · '
            f'updated {safe_text(compact_date(item.get("pushed_at")))}</sub></p>'
        )

    activity: list[str] = []
    for item in data["activity"][:4]:
        activity.append(
            f'<p>● <strong>{safe_text(truncate(item.get("repo", ""), 27))}</strong><br>'
            f'<sub>{safe_text(compact_date(item.get("created_at")))} · '
            f'{safe_text(truncate(item.get("summary", ""), 49))}</sub></p>'
        )

    refreshed = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    source = "live GitHub API" if data.get("live") else "fallback snapshot"
    return "\n".join(
        [
            START_MARKER,
            '<p align="center">',
            f'  <img src="./assets/profile-metrics.svg?v={datetime.now(timezone.utc).strftime("%Y%m%d%H%M")}" '
            'width="100%" alt="Live GitHub profile metrics">',
            '</p>',
            '<details>',
            '<summary><strong>Accessible live data</strong></summary>',
            '<table><tr><td><strong>Status</strong></td><td><strong>Repositories</strong></td>'
            '<td><strong>Stars</strong></td><td><strong>Followers</strong></td></tr>',
            f'<tr><td>{safe_text(config["mode"])}</td><td>{safe_text(data.get("public_repos", "—"))}</td>'
            f'<td>{safe_text(data.get("total_stars", "—"))}</td><td>{safe_text(data.get("followers", "—"))}</td></tr></table>',
            '<table><tr><td width="52%" valign="top"><strong>PROJECT PULSE</strong>',
            "".join(projects),
            '</td><td width="48%" valign="top"><strong>RECENT ACTIVITY</strong>',
            "".join(activity),
            '</td></tr></table>',
            f'<sub>Auto-refreshed {refreshed} · {source}</sub>',
            '</details>',
            END_MARKER,
        ]
    )


def update_readme(section: str) -> None:
    current = README_PATH.read_text(encoding="utf-8")
    start = current.find(START_MARKER)
    end = current.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError("README live-profile markers are missing or out of order")
    end += len(END_MARKER)
    README_PATH.write_text(current[:start] + section + current[end:], encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Render from the fallback snapshot without calling the GitHub API.",
    )
    args = parser.parse_args()

    config = load_config()
    username = os.environ.get("GITHUB_USERNAME", "satoshinji2992")
    token = os.environ.get("GITHUB_TOKEN")

    if args.offline:
        data = collect_fallback_data(config)
    else:
        try:
            data = collect_live_data(config, username, token)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
            print(f"GitHub API unavailable, using fallback snapshot: {exc}", file=sys.stderr)
            data = collect_fallback_data(config)

    write_svg_assets(config, data)
    update_readme(render_readme_section(config, data, username))
    print(f"Updated {README_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
