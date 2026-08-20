#!/usr/bin/env python3
"""Render the profile's self-hosted live metrics SVG.

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
OUTPUT_PATH = ROOT / "assets" / "profile-metrics.svg"
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


def render_svg(config: dict[str, Any], data: dict[str, Any]) -> str:
    accent = "#c89bad"
    accent_soft = "#8f6d7c"
    bg = "#0d1117"
    panel = "#111720"
    border = "#30363d"
    text = "#f0f3f6"
    muted = "#8b949e"
    cyan = "#78d6c6"

    def t(x: int, y: int, value: Any, size: int = 15, fill: str = text,
          weight: int = 400, family: str = "Inter,Segoe UI,sans-serif",
          spacing: float = 0.0) -> str:
        return (
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" letter-spacing="{spacing}">'
            f'{safe_text(value)}</text>'
        )

    lines: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" '
        'viewBox="0 0 1200 360" role="img" aria-labelledby="title desc">',
        '<title id="title">Automatically refreshed GitHub profile status</title>',
        '<desc id="desc">Current focus, project pulse and recent public activity.</desc>',
        '<defs>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        f'<stop offset="0" stop-color="{bg}"/>',
        '<stop offset="1" stop-color="#12131a"/>',
        '</linearGradient>',
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000" flood-opacity=".28"/>',
        '</filter>',
        '</defs>',
        '<rect x="1" y="1" width="1198" height="358" rx="18" fill="url(#bg)" '
        f'stroke="{border}" stroke-width="2"/>',
        '<path d="M26 48H1174" stroke="#262e38"/>',
        '<rect x="28" y="24" width="9" height="9" fill="#c89bad"/>',
        t(49, 34, "LIVE PROFILE // AUTO-REFRESHED", 14, muted, 600,
          "ui-monospace,SFMono-Regular,Consolas,monospace", 1.4),
        t(1044, 34, "GITHUB ACTIONS", 12, muted, 500,
          "ui-monospace,SFMono-Regular,Consolas,monospace", 1.0),
        '<path d="M376 68V330M800 68V330" stroke="#262e38"/>',
    ]

    # Column 1: lab status
    lines += [
        t(34, 82, "LAB STATUS", 13, accent, 700,
          "ui-monospace,SFMono-Regular,Consolas,monospace", 1.4),
        t(34, 118, config["mode"], 25, text, 650),
        '<circle cx="330" cy="111" r="5" fill="#78d6c6"/>',
        t(34, 150, config["now"], 14, muted),
        t(34, 184, "FOCUS", 11, muted, 600,
          "ui-monospace,SFMono-Regular,Consolas,monospace", 1.0),
        t(34, 207, config["focus"], 17, text, 550),
    ]

    stat_y = 247
    stats = [
        ("REPOSITORIES", data.get("public_repos", "—")),
        ("STARS", data.get("total_stars", "—")),
        ("FOLLOWERS", data.get("followers", "—")),
    ]
    stat_x = [34, 150, 252]
    for x, (label, value) in zip(stat_x, stats):
        lines.append(t(x, stat_y, label, 10, muted, 600,
                       "ui-monospace,SFMono-Regular,Consolas,monospace", .8))
        lines.append(t(x, stat_y + 31, value, 24, text, 650))
    lines += [
        '<path d="M34 304H342" stroke="#30363d"/>',
        t(34, 327, config["tagline"], 13, accent, 500),
    ]

    # Column 2: project pulse
    lines.append(t(404, 82, "PROJECT PULSE // 03", 13, accent, 700,
                   "ui-monospace,SFMono-Regular,Consolas,monospace", 1.4))
    project_y = [112, 180, 248]
    for idx, (item, y) in enumerate(zip(data["projects"], project_y), start=1):
        if idx > 1:
            lines.append(f'<path d="M404 {y-18}H772" stroke="#262e38"/>')
        lines += [
            t(404, y, f"0{idx}", 12, accent_soft, 700,
              "ui-monospace,SFMono-Regular,Consolas,monospace"),
            t(440, y, item["label"], 16, text, 600),
            t(440, y + 23, item["kind"], 12, muted, 500),
            t(772, y, f"★ {item.get('stars', 0)}", 12, muted, 500,
              "ui-monospace,SFMono-Regular,Consolas,monospace"),
            t(772, y + 23, compact_date(item.get("pushed_at")), 11, muted, 400,
              "ui-monospace,SFMono-Regular,Consolas,monospace"),
        ]

    # Column 3: recent activity
    lines.append(t(828, 82, "RECENT ACTIVITY", 13, accent, 700,
                   "ui-monospace,SFMono-Regular,Consolas,monospace", 1.4))
    activity_y = [116, 170, 224, 278]
    for item, y in zip(data["activity"][:4], activity_y):
        lines += [
            f'<circle cx="836" cy="{y-5}" r="4" fill="{accent}"/>',
            f'<path d="M836 {y+4}V{y+33}" stroke="{border}"/>',
            t(852, y, compact_date(item.get("created_at")), 11, muted, 500,
              "ui-monospace,SFMono-Regular,Consolas,monospace"),
            t(952, y, truncate(item.get("repo", ""), 27), 13, text, 600),
            t(852, y + 22, truncate(item.get("summary", ""), 49), 13, muted, 400),
        ]

    refreshed = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    source = "live GitHub API" if data.get("live") else "fallback snapshot"
    lines += [
        '<path d="M828 304H1166" stroke="#30363d"/>',
        t(828, 328, f"updated {refreshed} · {source}", 11, muted, 400,
          "ui-monospace,SFMono-Regular,Consolas,monospace"),
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


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

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_svg(config, data), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
