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


def collect_showcase_item(item: dict[str, Any], username: str, token: str | None) -> dict[str, Any]:
    """Collect one showcase, allowing a single visual to represent several repos."""
    repo_names = list(item.get("repos") or ([item["repo"]] if item.get("repo") else []))
    snapshots: list[dict[str, Any]] = []
    unavailable: list[str] = []
    for repo_name in repo_names:
        try:
            snapshots.append(
                api_get(
                    f"/repos/{urllib.parse.quote(username)}/{urllib.parse.quote(repo_name)}",
                    token,
                )
            )
        except urllib.error.HTTPError as exc:
            # A private repository is intentionally still a valid showcase. Keep
            # its configured snapshot while allowing the public cards to refresh.
            if exc.code in (403, 404):
                unavailable.append(repo_name)
                continue
            raise

    pushed_values = [
        snapshot.get("pushed_at") or snapshot.get("updated_at")
        for snapshot in snapshots
        if snapshot.get("pushed_at") or snapshot.get("updated_at")
    ]
    pushed_at = max(pushed_values, key=parse_date) if pushed_values else item.get("fallback_pushed_at")
    if not snapshots:
        return {
            **item,
            "repo": item.get("repo") or (repo_names[0] if repo_names else ""),
            "repos": repo_names,
            "pushed_at": item.get("fallback_pushed_at"),
            "stars": item.get("fallback_stars", 0),
            "fork": False,
            "unavailable_repos": unavailable,
        }

    return {
        **item,
        "repo": item.get("repo") or (repo_names[0] if repo_names else ""),
        "repos": repo_names,
        "pushed_at": pushed_at,
        "stars": sum(int(snapshot.get("stargazers_count", 0)) for snapshot in snapshots),
        "fork": all(bool(snapshot.get("fork", False)) for snapshot in snapshots),
        "unavailable_repos": unavailable,
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

    showcases = [
        collect_showcase_item(item, username, token)
        for item in config.get("showcases", [])
    ]

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
        "showcases": showcases,
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
    showcases = [
        {
            **item,
            "repo": item.get("repo") or (item.get("repos") or [""])[0],
            "repos": list(item.get("repos") or ([item["repo"]] if item.get("repo") else [])),
            "pushed_at": item.get("fallback_pushed_at"),
            "stars": item.get("fallback_stars", 0),
            "fork": False,
        }
        for item in config.get("showcases", [])
    ]
    return {
        **config["fallback"],
        "projects": projects,
        "showcases": showcases,
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
    rendered_size = max(size + 1, round(size * 1.08))
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" '
        f'font-size="{rendered_size}" font-weight="{weight}" text-anchor="{anchor}" '
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
        '<style>',
        '@keyframes pulse{0%,100%{opacity:.42;transform:scale(.86)}50%{opacity:1;transform:scale(1.12)}}',
        '@keyframes flow{to{stroke-dashoffset:-42}}',
        '@keyframes shimmer{0%,100%{opacity:.3}50%{opacity:1}}',
        '@keyframes radar{0%{opacity:.8;transform:scale(.72)}75%,100%{opacity:0;transform:scale(1.18)}}',
        '@keyframes bar{0%,100%{transform:scaleX(.45);opacity:.5}50%{transform:scaleX(1);opacity:1}}',
        '@keyframes orbit{to{transform:rotate(360deg)}}',
        '@keyframes float{0%,100%{transform:translateY(-3px)}50%{transform:translateY(4px)}}',
        '@keyframes signal{0%,100%{opacity:.28}45%,55%{opacity:1}}',
        '.pulse{animation:pulse 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}',
        '.flow{stroke-dasharray:7 10;animation:flow 2.2s linear infinite}',
        '.shimmer{animation:shimmer 2.8s ease-in-out infinite}',
        '.radar{animation:radar 3.2s ease-out infinite;transform-box:fill-box;transform-origin:center}',
        '.bar{animation:bar 3s ease-in-out infinite;transform-box:fill-box;transform-origin:left center}',
        '.orbit{animation:orbit 18s linear infinite;transform-box:fill-box;transform-origin:center}',
        '.float{animation:float 4.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}',
        '.signal{animation:signal 2.6s ease-in-out infinite}',
        '@media(prefers-reduced-motion:reduce){.pulse,.flow,.shimmer,.radar,.bar,.orbit,.float,.signal{animation:none!important}}',
        '</style>',
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
        '<g class="flow" stroke="#8f6d7c" fill="none" opacity=".58">',
        '<circle cx="946" cy="174" r="42"/><circle cx="946" cy="174" r="70"/>'
        '<circle cx="946" cy="174" r="98"/>',
        '<path d="M620 92L700 128 775 82 850 142 946 76 1088 104M620 258L706 218 '
        '790 268 858 214 946 274 1090 238M700 128L706 218M775 82L790 268M850 142L858 214"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(f'<circle class="pulse" style="animation-delay:{i*.13:.2f}s" cx="{x}" cy="{y}" r="7"/>' for i, (x, y) in enumerate([
            (620,92),(700,128),(775,82),(850,142),(946,76),(1088,104),
            (620,258),(706,218),(790,268),(858,214),(946,274),(1090,238)])),
        ''.join(f'<rect class="shimmer" style="animation-delay:{(r*5+c)*.08:.2f}s" x="{720 + c*18}" y="{145 + r*18}" width="12" height="12" rx="2"/>'
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
    lines = svg_frame(590, 300, "LeRobot upstream contribution project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, "03 / ROBOT LEARNING", 12, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1),
        svg_text(34, 123, "LeRobot", 43, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 157, "UPSTREAM CONTRIBUTION", 10, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.5),
        svg_text(34, 190, "OBSERVE  →  REPRESENT  →  ACT", 11, "#a8afbb", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 11, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g fill="none" stroke="#596273">',
        '<rect x="294" y="82" width="78" height="132" rx="8"/>'
        '<rect x="390" y="82" width="78" height="132" rx="8"/>'
        '<rect x="486" y="82" width="78" height="132" rx="8"/>',
        '<path class="flow" d="M372 148H390M468 148H486"/>',
        '<path d="M311 128L329 111 352 142 329 162 311 128M503 172L521 154 543 165"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(f'<circle class="pulse" style="animation-delay:{i*.18:.2f}s" cx="{x}" cy="{y}" r="5"/>' for i,(x,y) in enumerate([(311,128),(329,111),(352,142),(329,162),(503,172),(521,154),(543,165)])),
        ''.join(f'<rect class="shimmer" style="animation-delay:{(r*4+c)*.1:.2f}s" x="{405+c*13}" y="{113+r*13}" width="8" height="8" rx="1"/>' for r in range(4) for c in range(4)),
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
        svg_text(34, 40, "02 / COMPUTER VISION", 12, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1),
        svg_text(34, 111, "Seiyuu", 38, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 153, "MATCH", 38, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 190, "EMBED  →  COMPARE  →  RANK", 11, "#a8afbb", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(34, 226, "PRODUCTION WEBSITE", 10, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.4),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 11, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g fill="none" stroke="#8f6d7c">',
        '<circle cx="350" cy="143" r="34"/><circle class="radar" cx="350" cy="143" r="57"/>'
        '<circle class="radar" style="animation-delay:1.6s" cx="350" cy="143" r="80"/>',
        '<path d="M325 120L367 105 381 151 346 174 318 151Z"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(f'<circle class="pulse" style="animation-delay:{i*.22:.2f}s" cx="{x}" cy="{y}" r="5"/>' for i,(x,y) in enumerate([(325,120),(367,105),(381,151),(346,174),(318,151)])),
        '</g>',
        '<g fill="#1a202b" stroke="#394252">',
        ''.join(f'<rect x="440" y="{72+i*37}" width="118" height="25" rx="5"/>' for i in range(5)),
        '</g><g fill="#cf9caf">',
        ''.join(f'<rect class="bar" style="animation-delay:{i*.24:.2f}s" x="455" y="{80+i*37}" width="{75-i*8}" height="9" rx="4"/>' for i in range(5)),
        '</g>',
        svg_text(350, 258, "FACE EMBEDDING", 10, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_skillagent_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "SkillAgent multimodal hypergraph latent-space paper card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, "04 / RESEARCH PAPER", 11, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.75),
        svg_text(34, 112, "SkillAgent", 34, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 151, "LSRH", 24, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=2),
        svg_text(34, 186, "MULTIMODAL · HYPERGRAPH", 10, "#a8afbb", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.3),
        svg_text(34, 214, "structure selects", 14, "#edf0f5", 600),
        svg_text(34, 239, "latent programs preserve content", 11, "#89919f"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 10, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<circle cx="420" cy="150" r="115" fill="url(#glow)"/>',
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="294" y="56" width="58" height="22" rx="6"/><rect x="370" y="56" width="58" height="22" rx="6"/><rect x="446" y="56" width="58" height="22" rx="6"/>',
        '</g>',
        svg_text(323, 71, "VISION", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(399, 71, "TEXT", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(475, 71, "STATE", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<g class="flow" fill="none" stroke="#8f6d7c" opacity=".72">',
        '<path d="M323 78V92M399 78V90M475 78V94"/>',
        '<path d="M300 92L350 128 400 90 450 128 510 94M300 220L350 184 400 220 450 184 510 220"/>',
        '<path d="M350 128L350 184M400 90L400 220M450 128L450 184M520 150H550"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(
            f'<circle class="pulse" style="animation-delay:{i*.13:.2f}s" cx="{x}" cy="{y}" r="5"/>'
            for i, (x, y) in enumerate([
                (300, 92), (350, 128), (400, 90), (450, 128), (510, 94),
                (300, 220), (350, 184), (400, 220), (450, 184), (510, 220),
            ])
        ),
        '</g>',
        '<g class="float">',
        '<rect x="335" y="127" width="32" height="88" rx="8" fill="#151b25" stroke="#cf9caf"/>',
        '<rect x="384" y="108" width="32" height="128" rx="8" fill="#151b25" stroke="#cf9caf"/>',
        '<rect x="433" y="127" width="32" height="88" rx="8" fill="#151b25" stroke="#cf9caf"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(
            f'<rect class="shimmer" style="animation-delay:{(r*2+c)*.15:.2f}s" x="{393 + c*10}" y="{126 + r*17}" width="7" height="7" rx="2"/>'
            for r in range(6) for c in range(2)
        ),
        '</g>',
        svg_text(351, 231, "GRAPH", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(400, 252, "LATENT", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(449, 231, "ACTION", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<g class="signal">',
        '<rect x="510" y="127" width="60" height="50" rx="8" fill="#151b25" stroke="#3a4351"/>',
        svg_text(540, 148, "SKILL", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(540, 163, "PROGRAM", 8, "#edf0f5", 650,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '</g>',
        svg_text(302, 282, "STRUCTURE  →  LATENT  →  ACTION", 9, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_electronics_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "H_ball and servo electronics competition project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, item.get("kicker", "05 / ELECTRONICS COMPETITION"), 11, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.65),
        svg_text(34, 113, "H_ball", 37, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 151, "+ servo", 30, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 186, "VISION  →  UART  →  CONTROL", 10, "#a8afbb", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.35),
        svg_text(34, 223, "MAIXCAM · STM32 · SENSORS", 10, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.35),
        svg_text(34, 267, f'2 REPOS · ★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 10, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g class="flow" fill="none" stroke="#8f6d7c">',
        '<path d="M304 144H350M402 144H438M352 122H366M438 122H452"/>',
        '<path d="M350 155H366M438 155H452" stroke-dasharray="3 4"/>',
        '</g>',
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="294" y="88" width="58" height="112" rx="9"/>',
        '<rect x="366" y="81" width="72" height="126" rx="9"/>',
        '<rect x="452" y="91" width="108" height="98" rx="9"/>',
        '<path d="M300 102h-8M300 118h-8M300 134h-8M300 150h-8M300 166h-8M300 182h-8"/>',
        '<path d="M432 96h9M432 112h9M432 128h9M432 144h9M432 160h9M432 176h9M432 192h9"/>',
        '</g>',
        '<g class="pulse" fill="#cf9caf">',
        '<circle cx="323" cy="118" r="10"/><circle cx="323" cy="146" r="6"/><circle cx="323" cy="174" r="6"/>',
        '</g>',
        '<g class="shimmer" fill="#cf9caf">',
        '<circle cx="392" cy="112" r="5"/><circle cx="412" cy="112" r="5"/>',
        '<circle cx="392" cy="132" r="5"/><circle cx="412" cy="132" r="5"/>',
        '<circle cx="392" cy="152" r="5"/><circle cx="412" cy="152" r="5"/>',
        '<circle cx="392" cy="172" r="5"/><circle cx="412" cy="172" r="5"/>',
        '</g>',
        '<g class="float" fill="none" stroke="#cf9caf">',
        '<circle cx="500" cy="140" r="25"/><path d="M500 140l18-12M500 140v18M500 140h-18"/>',
        '<path d="M466 169h18l5-12 7 24 7-19 7 12h20" stroke-dasharray="4 3"/>',
        '</g>',
        svg_text(323, 104, "LENS", 7, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(402, 101, "UART", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(506, 109, "PWM", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(323, 218, "CAM", 9, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(402, 231, "MCU", 9, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(506, 211, "SERVO", 9, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_nailong_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "naiLongRacing embedded 3D game project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, item.get("kicker", "06 / EMBEDDED 3D GAME"), 11, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.75),
        svg_text(34, 111, "naiLong", 34, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 151, "Racing", 34, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 186, "OPENVELA  ·  LVGL  ·  SDL", 10, "#a8afbb", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.25),
        svg_text(34, 223, "PURE C GAME CORE / PORTABLE VIEW", 9, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.25),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 10, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="296" y="54" width="76" height="24" rx="6"/><rect x="478" y="54" width="78" height="24" rx="6"/>',
        '</g>',
        svg_text(306, 70, "TRACK 01", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(546, 70, "SPEED  082", 7, "#78d6c6", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        '<g class="flow" fill="none" stroke="#596273" opacity=".9">',
        '<path d="M304 86L548 86M292 244L560 244M337 86L375 244M515 86L477 244"/>',
        '<path d="M365 116L422 244M490 116L435 244"/>',
        '</g>',
        '<path class="flow" d="M420 90V242" stroke="#cf9caf" stroke-width="2" stroke-dasharray="3 9"/>',
        '<path class="signal" d="M425 100L454 244H396Z" fill="#cf9caf" opacity=".18"/>',
        '<g class="float" fill="#cf9caf">',
        '<path d="M421 171l24 0 12 22-48 0z"/>',
        '<circle cx="420" cy="196" r="5"/><circle cx="451" cy="196" r="5"/>',
        '</g>',
        '<g class="pulse" fill="#cf9caf">',
        '<circle cx="304" cy="86" r="5"/><circle cx="548" cy="86" r="5"/>',
        '<circle cx="292" cy="244" r="5"/><circle cx="560" cy="244" r="5"/>',
        '</g>',
        '<g fill="none" stroke="#78d6c6" opacity=".7">',
        '<path d="M315 230h18M507 230h18"/><path d="M324 225v10M516 225v10"/>',
        '</g>',
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="300" y="259" width="91" height="22" rx="5"/><rect x="405" y="259" width="91" height="22" rx="5"/><rect x="510" y="259" width="50" height="22" rx="5"/>',
        '</g>',
        svg_text(345, 274, "OPENVELA", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(450, 274, "LVGL", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(535, 274, "SDL", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_fpga_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "FPGA RISC-V CPU project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, "07 / DIGITAL SYSTEMS", 11, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.75),
        svg_text(34, 112, "FPGA", 36, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 151, "CPU", 36, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 186, "RV32I · PIPELINE · CACHE", 10, "#a8afbb", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.25),
        svg_text(34, 220, "SystemVerilog / BRAM / UART", 11, "#edf0f5", 600),
        svg_text(34, 243, "single-cycle → five-stage", 10, "#89919f"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 10, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="294" y="54" width="94" height="22" rx="6"/><rect x="402" y="54" width="147" height="22" rx="6"/>',
        '</g>',
        svg_text(306, 69, "RV32I CORE", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(539, 69, "INSTRUCTION BUS  /  32-BIT", 7, "#78d6c6", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        '<g class="flow" fill="none" stroke="#8f6d7c">',
        '<path d="M300 108H560M300 207H560"/>',
        '<path d="M300 114V201M560 114V201" stroke-dasharray="3 5"/>',
        '</g>',
        '<g fill="#151b25" stroke="#3a4351">',
        ''.join(f'<rect x="{294+i*55}" y="{126 if i%2 == 0 else 84}" width="45" height="40" rx="7"/>' for i in range(5)),
        '<rect x="305" y="225" width="68" height="33" rx="7"/><rect x="393" y="225" width="68" height="33" rx="7"/><rect x="481" y="225" width="68" height="33" rx="7"/>',
        '</g>',
        '<g class="shimmer" fill="#cf9caf">',
        ''.join(f'<rect style="animation-delay:{i*.18:.2f}s" x="{301+i*55}" y="{142 if i%2 == 0 else 100}" width="31" height="7" rx="3"/>' for i in range(5)),
        '</g>',
        '<g class="pulse" fill="#cf9caf">',
        ''.join(f'<circle style="animation-delay:{i*.2:.2f}s" cx="{300+i*55}" cy="{115 if i%2 == 0 else 181}" r="4"/>' for i in range(5)),
        '</g>',
        '<g fill="#cf9caf" opacity=".75">',
        '<path d="M294 91h-8M294 101h-8M294 111h-8M294 121h-8M294 131h-8M294 141h-8M294 151h-8M294 161h-8M294 171h-8M294 181h-8"/>',
        '<path d="M560 91h8M560 101h8M560 111h8M560 121h8M560 131h8M560 141h8M560 151h8M560 161h8M560 171h8M560 181h8"/>',
        '</g>',
        svg_text(316, 151, "IF", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(371, 109, "ID", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(426, 151, "EX", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(481, 109, "MEM", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(536, 151, "WB", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(339, 246, "BRAM", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(427, 246, "I-CACHE", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(515, 246, "UART", 8, "#cf9caf", 700,
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
        '<circle class="pulse" cx="340" cy="124" r="6" fill="#78d6c6"/>',
        svg_text(34, 165, config["now"], 12, "#89919f"),
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
            f'<circle class="pulse" style="animation-delay:{(y-126)*.012:.2f}s" cx="838" cy="{y-6}" r="4" fill="#cf9caf"/>',
            svg_text(855, y, compact_date(item.get("created_at")), 11, "#89919f", 500,
                     "ui-monospace,SFMono-Regular,Consolas,monospace"),
            svg_text(958, y, truncate(item.get("repo", ""), 24), 13, "#edf0f5", 650),
            svg_text(855, y+22, truncate(item.get("summary", ""), 43), 12, "#89919f"),
        ]
    refreshed = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines += [svg_text(1168, 336, f"updated {refreshed}", 10, "#737d8c", 500,
                       "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"), '</svg>']
    return "\n".join(lines) + "\n"


def render_research_map() -> str:
    lines = svg_frame(1200, 330, "Animated research interests map")
    nodes = [
        (440, 56, "01", "EMBODIED INTELLIGENCE", 0.0),
        (930, 56, "02", "VISION-LANGUAGE-ACTION", .55),
        (440, 216, "03", "ROBOT LEARNING", 1.1),
        (930, 216, "04", "MULTIMODAL AGENTS", 1.65),
    ]
    lines += [
        '<path d="M386 34V296M40 72H346" stroke="#303744"/>',
        svg_text(40, 54, "RESEARCH VECTOR // 04", 13, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3),
        svg_text(40, 132, "Perceive.", 37, "#f3eef1", 700, "Georgia,serif"),
        svg_text(40, 175, "Reason. Act.", 37, "#f3eef1", 700, "Georgia,serif"),
        svg_text(40, 222, "Systems that connect visual understanding,", 13, "#89919f"),
        svg_text(40, 244, "language-conditioned goals, and control.", 13, "#89919f"),
        svg_text(40, 290, "MEMORY  →  PLANNING  →  SKILLS", 11, "#a8afbb", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g class="flow" fill="none" stroke="#8f6d7c" opacity=".65">',
        '<path d="M650 86L790 165L930 86M650 246L790 165L930 246"/>',
        '</g>',
        '<circle cx="790" cy="165" r="112" fill="url(#glow)"/>',
        '<g class="orbit" fill="none" stroke="#8f6d7c" opacity=".7">',
        '<ellipse cx="790" cy="165" rx="92" ry="46"/>'
        '<ellipse cx="790" cy="165" rx="46" ry="92" transform="rotate(34 790 165)"/>',
        '<circle cx="882" cy="165" r="7" fill="#cf9caf" stroke="none"/>'
        '<circle cx="757" cy="81" r="6" fill="#78d6c6" stroke="none"/>',
        '</g>',
        '<circle class="radar" cx="790" cy="165" r="45" fill="none" stroke="#cf9caf"/>',
        '<circle cx="790" cy="165" r="31" fill="#171d27" stroke="#cf9caf"/>',
        svg_text(790, 160, "AGENT", 12, "#f3eef1", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle", spacing=1),
        svg_text(790, 180, "CORE", 10, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
    ]
    for x, y, number, label, delay in nodes:
        lines += [
            f'<g class="float" style="animation-delay:{delay}s">',
            f'<rect x="{x}" y="{y}" width="220" height="60" rx="10" fill="#151b25" stroke="#3a4351"/>',
            f'<rect class="signal" style="animation-delay:{delay}s" x="{x}" y="{y}" width="5" height="60" rx="2" fill="#cf9caf"/>',
            svg_text(x+20, y+27, number, 11, "#cf9caf", 700,
                     "ui-monospace,SFMono-Regular,Consolas,monospace"),
            svg_text(x+20, y+47, label, 11, "#edf0f5", 650,
                     "ui-monospace,SFMono-Regular,Consolas,monospace"),
            '</g>',
        ]
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def render_toolchain() -> str:
    lines = svg_frame(1200, 235, "Animated tools and systems stack")
    columns = [
        (375, "01 / LEARNING", ["PyTorch", "NumPy", "Transformers"]),
        (655, "02 / EMBODIED", ["LeRobot", "Isaac Lab", "ROS"]),
        (935, "03 / SYSTEMS", ["Python", "C++", "Linux"]),
    ]
    lines += [
        '<path d="M330 28V207M40 67H292" stroke="#303744"/>',
        svg_text(40, 49, "WORKING STACK", 13, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3),
        svg_text(40, 120, "Build it.", 35, "#f3eef1", 700, "Georgia,serif"),
        svg_text(40, 160, "Trace it.", 35, "#f3eef1", 700, "Georgia,serif"),
        svg_text(40, 201, "TEST  →  PROFILE  →  SHIP", 11, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<path class="flow" d="M385 181H1128" stroke="#8f6d7c" fill="none"/>',
    ]
    for column_index, (x, heading, tools) in enumerate(columns):
        lines += [
            svg_text(x, 48, heading, 12, "#cf9caf", 700,
                     "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1),
            f'<rect x="{x}" y="66" width="235" height="93" rx="11" fill="#151b25" stroke="#3a4351"/>',
        ]
        for tool_index, tool in enumerate(tools):
            y = 91 + tool_index * 27
            delay = column_index * .5 + tool_index * .18
            lines += [
                f'<circle class="pulse" style="animation-delay:{delay:.2f}s" cx="{x+19}" cy="{y-4}" r="4" fill="#cf9caf"/>',
                svg_text(x+34, y, tool, 14, "#edf0f5", 600),
                f'<rect class="shimmer" style="animation-delay:{delay:.2f}s" x="{x+150}" y="{y-11}" '
                f'width="{54 + tool_index*9}" height="7" rx="3" fill="#8f6d7c"/>',
            ]
        lines += [
            f'<circle class="pulse" style="animation-delay:{column_index*.5:.2f}s" cx="{x+8}" cy="181" r="6" fill="#78d6c6"/>',
        ]
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def render_link_button(
    label: str, width: int = 590, height: int = 38, font_size: int = 15
) -> str:
    """Render a card-width action control that remains clickable when wrapped in an anchor."""
    center = height / 2
    icon_y = center - 4.5
    text_y = center + font_size * 0.36
    arrow_top = center - 6
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{safe_text(label)}">',
        '<defs><linearGradient id="linkbg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#171d27"/><stop offset="1" stop-color="#202733"/>'
        '</linearGradient></defs>',
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="9" fill="url(#linkbg)" stroke="#3a4351" stroke-width="2"/>',
        f'<rect x="14" y="{icon_y:.1f}" width="9" height="9" rx="2" fill="#cf9caf"/>',
        f'<text x="34" y="{text_y:.1f}" fill="#edf0f5" font-family="Inter,Segoe UI,sans-serif" '
        f'font-size="{font_size}" font-weight="700" letter-spacing=".2">{safe_text(label)}</text>',
        f'<path d="M{width-30} {arrow_top:.1f}l6 6-6 6" fill="none" stroke="#cf9caf" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/>',
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_nav_item(number: str, label: str) -> str:
    """Render a borderless editorial index item for the README directory."""
    width, height = 280, 52
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{safe_text(label)}">',
        '<style>.nav-label{fill:#edf0f5;stroke:#0b0e14;stroke-width:2;paint-order:stroke fill;stroke-linejoin:round}'
        '.nav-index{stroke:#0b0e14;stroke-width:1.5;paint-order:stroke fill}.nav-rule{stroke:#737d8c}</style>',
        '<rect x="0" y="11" width="3" height="30" rx="1.5" fill="#cf9caf"/>',
        '<path class="nav-rule" d="M0 50H280" stroke-width="1.5"/>',
        f'<text class="nav-index" x="14" y="18" fill="#cf9caf" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
        f'font-size="10" font-weight="700" letter-spacing="1.1">{safe_text(number)}</text>',
        f'<text class="nav-label" x="14" y="40" font-family="Inter,Segoe UI,sans-serif" '
        f'font-size="15" font-weight="700" letter-spacing=".45">{safe_text(label.upper())}</text>',
        '</svg>',
    ]) + "\n"


def write_svg_assets(config: dict[str, Any], data: dict[str, Any]) -> None:
    ASSETS_PATH.mkdir(parents=True, exist_ok=True)
    projects = {item["repo"]: item for item in data["projects"]}
    showcases = {item["id"]: item for item in data.get("showcases", [])}
    outputs = {
        "project-deep-learning.svg": render_deep_learning_card(
            projects["quickly_access_to_deeplearning"]
        ),
        "project-lerobot.svg": render_lerobot_card(projects["lerobot"]),
        "project-seiyuumatch.svg": render_seiyuu_card(projects["SeiyuuMatch"]),
        "profile-metrics.svg": render_profile_svg(config, data),
        "research-map.svg": render_research_map(),
        "toolchain.svg": render_toolchain(),
        "showcase-skillagent.svg": render_skillagent_card(showcases["skillagent"]),
        "showcase-electronics.svg": render_electronics_card(showcases["electronics"]),
        "showcase-nailong.svg": render_nailong_card(showcases["nailong"]),
        "showcase-fpga.svg": render_fpga_card(showcases["fpga-cpu"]),
        "button-skillagent.svg": render_link_button("Open agentskill-LSRH →"),
        "button-hball.svg": render_link_button("Open H_ball →", 286),
        "button-servo.svg": render_link_button("Open servo →", 286),
        "button-nailong.svg": render_link_button("Open naiLongRacing / openvela →"),
        "button-fpga.svg": render_link_button("Open fpga_cpu →"),
        "button-deep-repo.svg": render_link_button("Open repository →", 286),
        "button-deep-tutorial.svg": render_link_button("Interactive tutorial ↗", 286),
        "button-seiyuu-site.svg": render_link_button("Visit website ↗", 286, 76, 22),
        "button-seiyuu-source.svg": render_link_button("Open source →", 286, 76, 22),
        "button-lerobot-repo.svg": render_link_button("Open repository →", 286, 76, 22),
        "button-lerobot-pr.svg": render_link_button("Merged PR #2792 ↗", 286, 76, 22),
        "nav-research.svg": render_nav_item("01", "Research interests"),
        "nav-selected.svg": render_nav_item("02", "Selected work"),
        "nav-live.svg": render_nav_item("03", "Live activity"),
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
