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


MONO = "ui-monospace,SFMono-Regular,Consolas,monospace"


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
        svg_text(48, 48, "TUTORIAL", 14, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.5),
        svg_text(48, 128, "Deep Learning", 55, "#f3eef1", 700, "Georgia,serif"),
        svg_text(48, 190, "FROM SCRATCH", 49, "#f3eef1", 700, "Georgia,serif"),
        svg_text(50, 232, "GRADIENTS   →   RESNET   →   TRANSFORMER", 15, "#a8afbb", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.7),
        svg_text(48, 327, "implementation-first · runnable exercises · tests", 14, "#89919f"),
        '<circle cx="870" cy="178" r="145" fill="url(#glow)"/>',
        '<g class="flow" stroke="#8f6d7c" fill="none" opacity=".58">',
        '<circle cx="946" cy="174" r="42"/><circle cx="946" cy="174" r="70"/><circle cx="946" cy="174" r="98"/>',
        '<path d="M620 92L700 128 775 82 850 142 946 76 1088 104M620 258L706 218 790 268 858 214 946 274 1090 238M700 128L706 218M775 82L790 268M850 142L858 214"/>',
        '</g>',
        '<g fill="#cf9caf">',
        ''.join(f'<circle class="pulse" style="animation-delay:{i*.13:.2f}s" cx="{x}" cy="{y}" r="7"/>' for i, (x, y) in enumerate(((620,92),(700,128),(775,82),(850,142),(946,76),(1088,104),(620,258),(706,218),(790,268),(858,214),(946,274),(1090,238)))),
        ''.join(f'<rect class="shimmer" style="animation-delay:{(r*5+c)*.08:.2f}s" x="{720+c*18}" y="{145+r*18}" width="12" height="12" rx="2"/>' for r in range(4) for c in range(5)),
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
        svg_text(34, 40, "ROBOT LEARNING", 12, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1),
        svg_text(34, 123, "LeRobot", 43, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 157, "VLA / UPSTREAM CONTRIBUTION", 9, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.5),
        svg_text(34, 190, "CAMERA + LANGUAGE  →  ACTION", 10, "#a8afbb", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(34, 224, "robot policy · joint control · hardware", 9, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 11, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<rect x="289" y="47" width="271" height="219" rx="11" fill="#080b10" stroke="#465061" stroke-width="2"/>',
        '<path d="M299 84H550" stroke="#303744"/>',
        svg_text(302, 73, "REAL-ROBOT LOOP", 9, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.5),
        svg_text(548, 73, "20 HZ", 9, "#78d6c6", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="299" y="95" width="121" height="121" rx="8"/>',
        '<rect x="430" y="95" width="120" height="121" rx="8"/>',
        '</g>',
        '<path class="flow" d="M420 155H430" stroke="#8f6d7c" fill="none"/>',
        svg_text(359, 110, "CAMERA + ROBOT ARM", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<rect x="309" y="119" width="33" height="21" rx="4" fill="none" stroke="#596273" stroke-width="2"/>',
        '<circle cx="325" cy="129" r="7" fill="none" stroke="#78d6c6" stroke-width="2"/>',
        '<circle cx="325" cy="129" r="3" fill="none" stroke="#78d6c6" stroke-width="1.5"/>',
        '<g fill="none" stroke="#cf9caf" stroke-width="3">',
        '<rect x="308" y="197" width="51" height="9" rx="4.5" stroke="#596273"/>',
        '<rect x="321" y="174" width="16" height="27" rx="8"/>',
        '<rect x="329" y="173" width="39" height="14" rx="7" transform="rotate(-55 329 180)"/>',
        '<rect x="351" y="141" width="34" height="14" rx="7" transform="rotate(28 351 148)"/>',
        '<rect x="381" y="157" width="31" height="14" rx="7" transform="rotate(-54 381 164)"/>',
        '</g>',
        '<g fill="#151b25" stroke="#f3eef1" stroke-width="2">',
        '<circle cx="329" cy="197" r="8"/><circle cx="329" cy="180" r="8"/>',
        '<circle cx="351" cy="148" r="8"/><circle cx="381" cy="164" r="8"/><circle cx="399" cy="139" r="7"/>',
        '</g>',
        '<g fill="none" stroke="#78d6c6" stroke-width="2">',
        '<circle cx="329" cy="197" r="3"/><circle cx="329" cy="180" r="3"/>',
        '<circle cx="351" cy="148" r="3"/><circle cx="381" cy="164" r="3"/><circle cx="399" cy="139" r="2.5"/>',
        '</g>',
        '<g fill="none" stroke="#78d6c6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">',
        '<rect x="397" y="134" width="17" height="9" rx="4.5" transform="rotate(-45 399 139)"/>',
        '<path d="M410 128l8-7 6 1M410 131l9 7 6-2"/>',
        '</g>',
        svg_text(359, 211, "ROBOT MANIPULATOR", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(490, 110, "VLA CONTROL", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<g fill="#202936" stroke="#596273">',
        '<rect x="439" y="119" width="45" height="20" rx="4"/><rect x="496" y="119" width="45" height="20" rx="4"/>',
        '<rect x="458" y="158" width="64" height="31" rx="6"/>',
        '</g>',
        svg_text(461, 133, "VISION", 7, "#78d6c6", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(518, 133, "LANGUAGE", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(490, 178, "VLA POLICY", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<path d="M461 139v11M518 139v11M490 189v8" stroke="#8f6d7c" class="flow"/>',
        svg_text(490, 210, "JOINT TARGETS  q₁ … q₆", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<path d="M299 236H550" stroke="#303744"/>',
        svg_text(302, 253, "CAMERA / PROPRIOCEPTION", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(541, 253, "ACTION CHUNK", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_seiyuu_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "SeiyuuMatch project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, "COMPUTER VISION", 12, "#cf9caf", 700,
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


def render_compskill_card(item: dict[str, Any]) -> str:
    """Abstract of the paper's Figure 3: four modules around one skill key, a
    retrieval path on top and the between-rounds feedback loop underneath."""
    lines = svg_frame(1200, 360, "CompSkill: compact keys, KeyOpt calibration, experience hypergraph and a frozen actor around one skill key")
    mono = MONO
    pink, dim, ink, box = "#cf9caf", "#89919f", "#edf0f5", "#151b25"
    modules = [  # (number, label, sub, x, y)
        ("1", "COMPACT KEYS", "4096-d → 512-d", 600, 108),
        ("2", "KEYOPT", "matched wins", 600, 206),
        ("3", "HYPERGRAPH", "attributed events", 978, 108),
        ("4", "FROZEN ACTOR", "original doc only", 978, 206),
    ]
    lines += [
        '<rect x="0" y="0" width="13" height="360" rx="6" fill="#cf9caf"/>',
        '<path d="M48 62H520M48 296H520M560 34V326" stroke="#303744"/>',
        svg_text(48, 48, "RESEARCH PAPER · UNDER REVIEW", 14, pink, 700, mono, spacing=1.5),
        svg_text(48, 128, "CompSkill", 55, "#f3eef1", 700, "Georgia,serif"),
        svg_text(48, 186, "experience → retrieval", 28, pink, 700, mono, spacing=.5),
        svg_text(50, 232, "KEYS   ·   KEYOPT   ·   HYPERGRAPH   ·   REVIEW", 15, "#a8afbb", 500, mono, spacing=.7),
        svg_text(48, 268, "rank skills by what actually worked on this executor", 16, ink, 600),
        svg_text(48, 327, "first author · ToolQA Hit@1 63.0% → 79.8%", 14, dim),
        '<circle cx="850" cy="182" r="150" fill="url(#glow)"/>',
        # retrieval path along the top
        '<g class="flow" fill="none" stroke="#8f6d7c" opacity=".75"><path d="M612 64H1110"/></g>',
        ''.join(
            f'<rect x="{x-50}" y="52" width="100" height="24" rx="7" fill="{box}" stroke="#3a4351"/>'
            + svg_text(x, 68, t, 9, pink if i in (0, 4) else ink, 700, mono, anchor="middle")
            for i, (x, t) in enumerate([(640, "TASK x"), (758, "TOP-10"), (876, "SCORE S"), (994, "6 + ≤4"), (1104, "ACTOR")])
        ),
        # modules
        ''.join(
            f'<rect x="{x}" y="{y}" width="160" height="62" rx="10" fill="{box}" stroke="#3a4351"/>'
            f'<circle cx="{x+20}" cy="{y+20}" r="9" fill="none" stroke="{pink}"/>'
            + svg_text(x + 20, y + 24, n, 9, pink, 700, mono, anchor="middle")
            + svg_text(x + 36, y + 25, label, 10, ink, 700, mono)
            + svg_text(x + 20, y + 47, sub, 9, dim, 500, mono)
            for n, label, sub, x, y in modules
        ),
        # links from modules to the key
        '<g class="flow" fill="none" stroke="#8f6d7c" opacity=".75">',
        '<path d="M760 139H790M760 237H790M938 139H908M938 237H908"/>',
        '</g>',
        # the skill key in the centre
        '<g class="float">',
        '<rect x="790" y="114" width="118" height="150" rx="12" fill="#151b25" stroke="#cf9caf" stroke-width="1.5"/>',
        '</g>',
        svg_text(849, 136, "SKILL KEY", 10, pink, 700, mono, anchor="middle", spacing=1),
        ''.join(
            f'<rect class="shimmer" style="animation-delay:{(r*6+c)*.07:.2f}s" x="{804 + c*15}" y="{150 + r*14}" width="10" height="9" rx="2" fill="{pink if c < 4 else "#8f6d7c"}"/>'
            for r in range(5) for c in range(6)
        ),
        svg_text(849, 236, "k⁰ + Δk ; b", 11, ink, 650, mono, anchor="middle"),
        svg_text(849, 254, "one inner product", 8, dim, 500, mono, anchor="middle"),
        # between-rounds loop along the bottom
        '<g class="flow" fill="none" stroke="#8f6d7c" opacity=".75"><path d="M1110 296H612"/><path d="M1058 268V284M640 284V268"/></g>',
        ''.join(
            f'<rect x="{x-48}" y="284" width="96" height="24" rx="7" fill="{box}" stroke="#3a4351"/>'
            + svg_text(x, 300, t, 9, ink, 650, mono, anchor="middle")
            for x, t in [(1058, "OUTCOMES"), (948, "RECORD"), (848, "FILTER"), (748, "FIT"), (648, "PUBLISH")]
        ),
        svg_text(1138, 334, "between rounds · support tasks only", 11, dim, 500, mono, anchor="end"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_autokeeper_card(item: dict[str, Any]) -> str:
    """A Cthulhu rising from the sea behind a ring of R'lyeh glyphs."""
    lines = svg_frame(1200, 360, "AutoKeeper: an AI keeper for Call of Cthulhu, drawn as Cthulhu rising")
    mono = MONO
    pink, dim, ink = "#cf9caf", "#89919f", "#edf0f5"
    tentacles = [
        "M818 196C792 228 804 262 780 288C770 299 758 296 762 284",
        "M836 204C826 240 842 270 828 300",
        "M858 208C860 246 878 270 868 304C866 312 876 314 880 306",
        "M884 208C894 246 916 262 914 300",
        "M904 202C924 232 948 248 948 282C948 294 960 296 962 286",
        "M920 192C948 214 980 222 990 256",
    ]
    glyphs = "ᚦ ᛟ ᚱ ᛉ ᛏ ᚲ ᛗ ᛞ"
    lines += [
        '<rect x="0" y="0" width="13" height="360" rx="6" fill="#cf9caf"/>',
        '<path d="M48 62H520M48 296H520M560 34V326" stroke="#303744"/>',
        svg_text(48, 48, "OPEN-SOURCE AGENT SYSTEM", 14, pink, 700, mono, spacing=1.5),
        svg_text(48, 128, "AutoKeeper", 55, "#f3eef1", 700, "Georgia,serif"),
        svg_text(48, 186, "Call of Cthulhu 7e", 30, pink, 700, mono, spacing=1),
        svg_text(50, 232, "LANGGRAPH   ·   MULTI-AGENT   ·   HARNESS", 15, "#a8afbb", 500, mono, spacing=.7),
        svg_text(48, 268, "agents tell the story, the rule engine rolls the dice", 16, ink, 600),
        svg_text(48, 327, "Claude · Codex · DeepSeek · Ollama, even fully offline", 14, dim),
        '<circle cx="870" cy="168" r="160" fill="url(#glow)"/>',
        # ring of cyclopean marks
        '<g class="orbit" opacity=".7">',
        '<circle cx="870" cy="160" r="132" fill="none" stroke="#3a4351" stroke-dasharray="2 7"/>',
        ''.join(
            (lambda x, y, k: (
                f'<path d="M{x-5} {y+4}L{x} {y-5}L{x+5} {y+4}Z" fill="none" stroke="#8f6d7c"/>' if k % 3 == 0 else
                f'<circle cx="{x}" cy="{y}" r="3" fill="none" stroke="#8f6d7c"/>' if k % 3 == 1 else
                f'<path d="M{x-4} {y-4}L{x+4} {y+4}M{x+4} {y-4}L{x-4} {y+4}" stroke="#8f6d7c"/>'
            ))(round(870 + 132 * __import__("math").cos(k * 0.5236)), round(160 + 132 * __import__("math").sin(k * 0.5236)), k)
            for k in range(12)
        ),
        '</g>',
        # sunken monoliths of R'lyeh
        '<g fill="#121720" stroke="#2c3440">',
        '<path d="M640 300L652 228L676 222L688 300Z"/><path d="M694 300L700 254L722 250L730 300Z"/>',
        '<path d="M1014 300L1024 242L1050 236L1060 300Z"/><path d="M1068 300L1080 212L1104 206L1112 300Z"/>',
        '</g>',
        # wings
        '<path d="M800 150C760 118 724 120 700 96C720 140 744 168 790 182Z" fill="#151b25" stroke="#3a4351"/>',
        '<path d="M940 150C980 118 1016 120 1040 96C1020 140 996 168 950 182Z" fill="#151b25" stroke="#3a4351"/>',
        # head
        '<g class="float">',
        '<path d="M870 66C826 66 800 104 802 146C803 178 826 202 870 206C914 202 937 178 938 146C940 104 914 66 870 66Z" fill="#151b25" stroke="#cf9caf" stroke-width="1.6"/>',
        '<path d="M826 112C846 122 852 136 846 152M914 112C894 122 888 136 894 152" fill="none" stroke="#3a4351"/>',
        '<path d="M830 126Q848 118 862 128M878 128Q892 118 910 126" fill="none" stroke="#cf9caf" stroke-width="1.4"/>',
        '<path d="M842 84Q870 74 898 84M832 100Q870 88 908 100" fill="none" stroke="#2c3440"/>',
        '<ellipse class="pulse" cx="848" cy="138" rx="9" ry="5" fill="#cf9caf"/>',
        '<ellipse class="pulse" style="animation-delay:.3s" cx="892" cy="138" rx="9" ry="5" fill="#cf9caf"/>',
        '</g>',
        # tentacles
        ''.join(
            f'<path class="float" style="animation-delay:{i*.35:.2f}s" d="{d}" fill="none" stroke="{pink if i % 2 else "#8f6d7c"}" stroke-width="{4.5 - abs(2.5 - i)*0.6:.1f}" stroke-linecap="round"/>'
            for i, d in enumerate(tentacles)
        ),
        # sea
        '<g class="flow" fill="none" stroke="#3a4351" stroke-width="1.5">',
        '<path d="M600 300Q630 290 660 300T720 300T780 300T840 300T900 300T960 300T1020 300T1080 300T1140 300"/>',
        '<path d="M630 314Q660 304 690 314T750 314T810 314T870 314T930 314T990 314T1050 314T1110 314"/>',
        '</g>',
        svg_text(600, 344, "PH'NGLUI MGLW'NAFH CTHULHU R'LYEH WGAH'NAGL FHTAGN", 10, dim, 500, mono, spacing=.6),
        svg_text(1138, 344, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}', 12, dim, 500, mono, anchor="end"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_electronics_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "H_ball and servo electronics competition project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, item.get("kicker", "ELECTRONICS COMPETITION"), 11, "#cf9caf", 700,
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
        svg_text(34, 40, item.get("kicker", "OPENVELA GAME PORT"), 11, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.75),
        svg_text(34, 106, "naiLong", 34, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 146, "RACING", 32, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 181, "EMBEDDED 3D GAME", 11, "#a8afbb", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.45),
        svg_text(34, 216, "C  ·  LVGL  ·  SDL  ·  OPENVELA", 10, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.2),
        svg_text(34, 247, "portable game loop / UI runtime", 10, "#89919f", 500,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 10, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<rect x="289" y="46" width="271" height="219" rx="11" fill="#080b10" stroke="#465061" stroke-width="2"/>',
        '<rect x="298" y="55" width="253" height="192" rx="6" fill="#111923" stroke="#303744"/>',
        '<path d="M308 84H541" stroke="#303744"/>',
        svg_text(309, 74, "RACE / 02", 9, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.5),
        svg_text(540, 74, "P 01   082 KM/H", 9, "#78d6c6", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        '<path d="M309 105H540" stroke="#596273" stroke-width="1"/>',
        '<path d="M398 105H452L542 238H306Z" fill="#171e29" stroke="#596273" stroke-width="1.5"/>',
        '<path d="M398 105L306 238M452 105L542 238" stroke="#8f6d7c" stroke-width="1.5"/>',
        '<path class="flow" d="M425 110V124M425 137V154M425 168V190M425 204V232" stroke="#cf9caf" stroke-width="2"/>',
        '<path d="M382 116L348 238M468 116L502 238" stroke="#596273" stroke-dasharray="5 9"/>',
        '<g class="shimmer" fill="#cf9caf">',
        '<path d="M391 121h9l-5 7h-9zM450 121h9l5 7h-9z"/>',
        '<path d="M366 153h13l-8 10h-13zM477 153h13l8 10h-13z"/>',
        '<path d="M337 195h18l-11 13h-18zM493 195h18l11 13h-18z"/>',
        '</g>',
        '<g class="pulse" fill="#78d6c6">',
        '<circle cx="316" cy="105" r="3"/><circle cx="534" cy="105" r="3"/>',
        '</g>',
        '<g class="float">',
        '<path d="M398 214L409 205H441L452 214 459 237H391Z" fill="#cf9caf" stroke="#f3eef1" stroke-width="1.5"/>',
        '<path d="M408 207h34l-6 12h-22z" fill="#182331" stroke="#78d6c6"/>',
        '<path d="M398 225h54" stroke="#f3eef1" stroke-width="1.5"/>',
        '<circle cx="403" cy="239" r="5" fill="#080b10" stroke="#78d6c6" stroke-width="2"/>',
        '<circle cx="447" cy="239" r="5" fill="#080b10" stroke="#78d6c6" stroke-width="2"/>',
        '</g>',
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="307" y="94" width="46" height="17" rx="4"/><rect x="493" y="94" width="47" height="17" rx="4"/>',
        '</g>',
        svg_text(330, 106, "LAP 02/03", 7, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(516, 106, "BOOST 74%", 7, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="299" y="252" width="77" height="22" rx="5"/><rect x="384" y="252" width="77" height="22" rx="5"/><rect x="469" y="252" width="77" height="22" rx="5"/>',
        '</g>',
        svg_text(337, 267, "OPENVELA", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(422, 267, "LVGL UI", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(507, 267, "SDL", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


def render_fpga_card(item: dict[str, Any]) -> str:
    lines = svg_frame(590, 300, "FPGA RISC-V CPU project card")
    lines += [
        '<rect width="10" height="300" rx="5" fill="#cf9caf"/>',
        '<path d="M34 54H260M272 26V274" stroke="#303744"/>',
        svg_text(34, 40, "DIGITAL SYSTEMS", 11, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.75),
        svg_text(34, 112, "FPGA", 36, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 151, "CPU", 36, "#f3eef1", 700, "Georgia,serif"),
        svg_text(34, 186, "RV32I · FIVE-STAGE PIPELINE", 10, "#a8afbb", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.25),
        svg_text(34, 220, "SystemVerilog / BRAM / UART", 11, "#edf0f5", 600),
        svg_text(34, 243, "instruction + data paths", 10, "#89919f"),
        svg_text(34, 267, f'★ {item.get("stars", 0)} · {compact_date(item.get("pushed_at"))}',
                 10, "#89919f", 500, "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<rect x="289" y="47" width="271" height="219" rx="11" fill="#080b10" stroke="#465061" stroke-width="2"/>',
        '<path d="M299 84H550" stroke="#303744"/>',
        svg_text(302, 73, "RV32I CORE / RTL", 9, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        svg_text(548, 73, "50 MHZ", 9, "#78d6c6", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="end"),
        '<rect x="299" y="96" width="251" height="109" rx="8" fill="#151b25" stroke="#3a4351"/>',
        '<path class="flow" d="M307 118H542M307 190H542" stroke="#596273" fill="none"/>',
        '<g fill="#202936" stroke="#596273">',
        ''.join(f'<rect x="{306+i*48}" y="137" width="41" height="40" rx="5"/>' for i in range(5)),
        '</g>',
        '<g class="shimmer" fill="#cf9caf">',
        ''.join(f'<rect style="animation-delay:{i*.18:.2f}s" x="{311+i*48}" y="142" width="31" height="5" rx="2"/>' for i in range(5)),
        '</g>',
        '<g class="flow" stroke="#8f6d7c" stroke-width="1.5">',
        ''.join(f'<path d="M{347+i*48} 157H{354+i*48}"/>' for i in range(4)),
        '</g>',
        svg_text(326, 164, "IF", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(374, 164, "ID", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(422, 164, "EX", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(470, 164, "MEM", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(518, 164, "WB", 9, "#edf0f5", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<g class="pulse" fill="#78d6c6">',
        ''.join(f'<circle style="animation-delay:{i*.2:.2f}s" cx="{318+i*48}" cy="188" r="3"/>' for i in range(5)),
        '</g>',
        '<path d="M326 205V222M422 205V222M518 205V222" stroke="#8f6d7c" class="flow"/>',
        '<g fill="#151b25" stroke="#3a4351">',
        '<rect x="299" y="228" width="77" height="27" rx="6"/><rect x="386" y="228" width="77" height="27" rx="6"/><rect x="473" y="228" width="77" height="27" rx="6"/>',
        '</g>',
        svg_text(337, 246, "BRAM", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(424, 246, "I-CACHE", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(511, 246, "UART MMIO", 8, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        svg_text(299, 274, "32-BIT INSTRUCTION / DATA PATH", 8, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
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
    lines.append(svg_text(410, 92, "PROJECT PULSE", 12, "#cf9caf", 700,
                          "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3))
    for item, y in zip(data["projects"], [126, 196, 266]):
        lines += [
            f'<rect x="410" y="{y-11}" width="8" height="8" rx="2" fill="#cf9caf"/>',
            svg_text(430, y, item["label"], 16, "#edf0f5", 650),
            svg_text(430, y+23, item["kind"], 12, "#89919f", 500),
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
        (432, 48, "EMBODIED INTELLIGENCE", "PERCEPTION · CONTROL", 0.0),
        (930, 48, "VISION–LANGUAGE–ACTION", "VISION · LANGUAGE · ACTION", .55),
        (432, 218, "ROBOT LEARNING", "POLICY · DATA · REAL WORLD", 1.1),
        (930, 218, "MULTIMODAL AGENTS", "MEMORY · PLANNING · SKILLS", 1.65),
    ]
    lines += [
        '<path d="M386 34V296M40 72H346" stroke="#303744"/>',
        svg_text(40, 54, "RESEARCH SIGNAL / ACTIVE", 13, "#cf9caf", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=1.3),
        svg_text(40, 132, "Perceive.", 37, "#f3eef1", 700, "Georgia,serif"),
        svg_text(40, 175, "Reason. Act.", 37, "#f3eef1", 700, "Georgia,serif"),
        svg_text(40, 222, "Systems that connect visual understanding,", 13, "#89919f"),
        svg_text(40, 244, "language-conditioned goals, and control.", 13, "#89919f"),
        svg_text(40, 290, "MEMORY  →  PLANNING  →  SKILLS", 11, "#a8afbb", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '<g fill="none" stroke="#303744" opacity=".8">',
        '<path d="M404 24H1172M404 306H1172"/><path d="M414 34v14M1158 34v14M414 282v14M1158 282v14"/>',
        '</g>',
        '<g class="flow" fill="none" stroke="#8f6d7c" opacity=".72">',
        '<path d="M670 80C714 82 738 130 773 151M930 80C872 83 850 130 807 151"/>',
        '<path d="M670 250C714 248 738 200 773 178M930 250C872 248 850 201 807 178"/>',
        '</g>',
        '<circle cx="790" cy="165" r="126" fill="url(#glow)"/>',
        '<g class="orbit" fill="none" stroke="#8f6d7c" opacity=".74">',
        '<ellipse cx="790" cy="165" rx="100" ry="44"/>'
        '<ellipse cx="790" cy="165" rx="48" ry="103" transform="rotate(33 790 165)"/>'
        '<ellipse cx="790" cy="165" rx="30" ry="86" transform="rotate(-47 790 165)"/>',
        '</g>',
        '<g fill="#0f141d" stroke="#cf9caf" stroke-width="1.5">',
        '<circle cx="890" cy="165" r="6"/><circle cx="754" cy="69" r="5"/><circle cx="723" cy="220" r="5"/>',
        '</g>',
        '<circle class="pulse" cx="890" cy="165" r="2.5" fill="#78d6c6"/>',
        '<circle class="pulse" style="animation-delay:.8s" cx="754" cy="69" r="2" fill="#cf9caf"/>',
        '<circle class="radar" cx="790" cy="165" r="49" fill="none" stroke="#cf9caf"/>',
        '<circle cx="790" cy="165" r="34" fill="#111722" stroke="#cf9caf" stroke-width="1.5"/>',
        '<circle cx="790" cy="165" r="25" fill="none" stroke="#596273"/>',
        svg_text(790, 160, "AGENT", 12, "#f3eef1", 700,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle", spacing=1),
        svg_text(790, 180, "CORE", 10, "#89919f", 600,
                 "ui-monospace,SFMono-Regular,Consolas,monospace", anchor="middle"),
        '<g fill="#cf9caf" opacity=".75">',
        '<rect x="675" y="162" width="5" height="5" rx="1"/><rect x="900" y="162" width="5" height="5" rx="1"/>',
        '<rect x="788" y="48" width="5" height="5" rx="1"/><rect x="788" y="277" width="5" height="5" rx="1"/>',
        '</g>',
    ]
    for x, y, label, detail, delay in nodes:
        lines += [
            f'<g class="float" style="animation-delay:{delay}s">',
            f'<rect x="{x}" y="{y}" width="238" height="64" rx="11" fill="#121823" stroke="#465061"/>',
            f'<rect x="{x+1}" y="{y+1}" width="236" height="62" rx="10" fill="none" stroke="#232b38"/>',
            f'<rect class="signal" style="animation-delay:{delay}s" x="{x}" y="{y}" width="5" height="64" rx="2" fill="#cf9caf"/>',
            f'<path d="M{x+18} {y+13}h18M{x+18} {y+13}v10M{x+220} {y+51}h-18M{x+220} {y+51}v-10" stroke="#596273"/>',
            f'<rect x="{x+19}" y="{y+24}" width="8" height="8" rx="2" fill="#cf9caf"/>',
            svg_text(x+40, y+34, label, 11, "#edf0f5", 650,
                     "ui-monospace,SFMono-Regular,Consolas,monospace"),
            svg_text(x+40, y+52, detail, 8, "#89919f", 600,
                     "ui-monospace,SFMono-Regular,Consolas,monospace", spacing=.45),
            '</g>',
        ]
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def render_toolchain() -> str:
    lines = svg_frame(1200, 235, "Animated tools and systems stack")
    columns = [
        (375, "LEARNING", ["PyTorch", "NumPy", "Transformers"]),
        (655, "EMBODIED", ["LeRobot", "Isaac Lab", "ROS"]),
        (935, "SYSTEMS", ["Python", "C++", "Linux"]),
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


def render_section_header(number: str, label: str, meta: str) -> str:
    """Render a compact editorial header that keeps README section anchors intact."""
    width, height = 1200, 62
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{safe_text(label)}">',
        '<defs><linearGradient id="section-bg" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#111722"/><stop offset=".72" stop-color="#0d121a"/>'
        '<stop offset="1" stop-color="#151a24"/></linearGradient></defs>',
        '<style>.section-rule{stroke:#3a4351}.section-accent{fill:#cf9caf}'
        '.section-index{fill:#cf9caf}.section-label{fill:#edf0f5}'
        '.section-meta{fill:#89919f}</style>',
        '<rect x="0" y="3" width="1200" height="52" rx="10" fill="url(#section-bg)" stroke="#303744"/>',
        '<rect x="0" y="3" width="6" height="52" rx="3" class="section-accent"/>',
        '<path d="M20 51H1180" class="section-rule" stroke-width="1"/>',
        '<path d="M20 51H210" stroke="#cf9caf" stroke-width="1.5"/>',
        f'<text x="22" y="37" class="section-index" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
        f'font-size="14" font-weight="700" letter-spacing="1.2">{safe_text(number)} /</text>',
        f'<text x="78" y="38" class="section-label" font-family="Inter,Segoe UI,sans-serif" '
        f'font-size="26" font-weight="700" letter-spacing=".3">{safe_text(label.upper())}</text>',
        f'<text x="1176" y="36" text-anchor="end" class="section-meta" '
        f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" '
        f'font-weight="700" letter-spacing="1">{safe_text(meta.upper())}</text>',
        '<circle cx="1188" cy="36" r="3" fill="#78d6c6"/>',
        '<path d="M1110 12v7M1122 12v7M1134 12v7" stroke="#596273" stroke-width="2"/>',
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
        "showcase-compskill.svg": render_compskill_card(showcases["compskill"]),
        "showcase-autokeeper.svg": render_autokeeper_card(showcases["autokeeper"]),
        "showcase-electronics.svg": render_electronics_card(showcases["electronics"]),
        "showcase-nailong.svg": render_nailong_card(showcases["nailong"]),
        "showcase-fpga.svg": render_fpga_card(showcases["fpga-cpu"]),
        "button-compskill.svg": render_link_button("Anonymous code ↗", 286),
        "button-autokeeper-repo.svg": render_link_button("Open repository →", 286),
        "button-autokeeper-release.svg": render_link_button("Latest release ↗", 286),
        "button-hball.svg": render_link_button("Open H_ball →", 286, 76, 22),
        "button-servo.svg": render_link_button("Open servo →", 286, 76, 22),
        "button-nailong.svg": render_link_button("Open naiLongRacing / openvela →", 590, 76, 22),
        "button-fpga.svg": render_link_button("Open fpga_cpu →", 590, 76, 22),
        "button-deep-repo.svg": render_link_button("Open repository →", 286),
        "button-deep-tutorial.svg": render_link_button("Interactive tutorial ↗", 286),
        "button-seiyuu-site.svg": render_link_button("Visit website ↗", 286, 76, 22),
        "button-seiyuu-source.svg": render_link_button("Open source →", 286, 76, 22),
        "button-lerobot-repo.svg": render_link_button("Open repository →", 286, 76, 22),
        "button-lerobot-pr.svg": render_link_button("Merged PR #2792 ↗", 286, 76, 22),
        "nav-01-research.svg": render_nav_item("01", "Research interests"),
        "nav-02-selected.svg": render_nav_item("02", "Selected work"),
        "nav-03-live.svg": render_nav_item("03", "Live activity"),
        "nav-04-tools.svg": render_nav_item("04", "Tools I actually use"),
        "section-01-research.svg": render_section_header("01", "Currently exploring", "Active research"),
        "section-02-selected.svg": render_section_header("02", "Selected work", "08 projects"),
        "section-03-live.svg": render_section_header("03", "Live profile", "Auto-refreshed"),
        "section-04-tools.svg": render_section_header("04", "Tools I actually use", "Runtime stack"),
        # Keep the previous names available so local Markdown previews that have
        # not reloaded the README do not show a broken-image placeholder.
        "section-research.svg": render_section_header("01", "Currently exploring", "Active research"),
        "section-selected.svg": render_section_header("02", "Selected work", "08 projects"),
        "section-live.svg": render_section_header("03", "Live profile", "Auto-refreshed"),
        "section-tools.svg": render_section_header("04", "Tools I actually use", "Runtime stack"),
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
