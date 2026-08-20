#!/usr/bin/env python3
"""Refresh the profile's native live-data components in README.md.

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


def render_readme_section(
    config: dict[str, Any], data: dict[str, Any], username: str
) -> str:
    """Render live data as selectable, accessible GitHub-native HTML."""
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
            '<table>',
            '  <tr>',
            '    <td width="40%" valign="top">',
            '      <sub>LAB STATUS</sub><br>',
            f'      <strong>{safe_text(config["mode"])}</strong> &nbsp; 🟢<br><br>',
            f'      {safe_text(config["now"])}<br><br>',
            f'      <sub>FOCUS</sub><br><strong>{safe_text(config["focus"])}</strong>',
            '    </td>',
            '    <td width="20%" align="center" valign="middle">',
            f'      <sub>REPOSITORIES</sub><br><strong>{safe_text(data.get("public_repos", "—"))}</strong>',
            '    </td>',
            '    <td width="20%" align="center" valign="middle">',
            f'      <sub>STARS</sub><br><strong>{safe_text(data.get("total_stars", "—"))}</strong>',
            '    </td>',
            '    <td width="20%" align="center" valign="middle">',
            f'      <sub>FOLLOWERS</sub><br><strong>{safe_text(data.get("followers", "—"))}</strong>',
            '    </td>',
            '  </tr>',
            '</table>',
            '<table>',
            '  <tr>',
            '    <td width="52%" valign="top">',
            '      <strong>PROJECT PULSE // 03</strong>',
            "      " + "\n      ".join(projects),
            '    </td>',
            '    <td width="48%" valign="top">',
            '      <strong>RECENT ACTIVITY</strong>',
            "      " + "\n      ".join(activity),
            '    </td>',
            '  </tr>',
            '</table>',
            f'<sub>Auto-refreshed {refreshed} · {source}</sub>',
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

    update_readme(render_readme_section(config, data, username))
    print(f"Updated {README_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
