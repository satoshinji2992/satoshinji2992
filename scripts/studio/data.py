"""Live GitHub data, with the snapshot in data/status.json as a fallback.

Each source (profile, repositories, events, release, contribution calendar)
falls back on its own, so one failing endpoint never blanks the whole page.
"""

from __future__ import annotations

import copy
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from typing import Any

from .svg import ROOT

CONFIG_PATH = ROOT / "data" / "status.json"
API = "https://api.github.com"
CALENDAR_QUERY = (
    "query($login:String!){user(login:$login){contributionsCollection{contributionCalendar"
    "{totalContributions weeks{contributionDays{date contributionCount}}}}}}"
)
FAILURES = (OSError, KeyError, TypeError, ValueError)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def request(path: str, token: str | None, body: dict | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-renderer",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = None
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API}{path}", data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def short_date(value: str | None) -> str:
    parsed = parse_time(value)
    return parsed.strftime("%d %b %Y") if parsed else ""


def month_year(value: str | None) -> str:
    parsed = parse_time(value)
    return parsed.strftime("%b %Y") if parsed else ""


def summarize(event: dict[str, Any], username: str) -> dict[str, str] | None:
    repo = event.get("repo", {}).get("name", "")
    if not repo or repo == f"{username}/{username}":
        return None
    payload = event.get("payload") or {}
    kind = event.get("type")
    if kind == "ReleaseEvent":
        summary = f"released {payload.get('release', {}).get('tag_name', 'a version')}"
    elif kind == "PushEvent" and payload.get("ref") in ("refs/heads/main", "refs/heads/master"):
        summary = "pushed to main"
    elif kind == "CreateEvent" and payload.get("ref_type") == "repository":
        summary = "created the repository"
    elif kind == "PullRequestEvent":
        number = payload.get("number") or payload.get("pull_request", {}).get("number", "")
        summary = f"{payload.get('action', 'updated')} PR #{number}"
    elif kind == "ForkEvent":
        summary = "forked the repository"
    else:
        return None
    short = repo.split("/", 1)[1] if repo.startswith(f"{username}/") else repo
    return {"date": event.get("created_at", "")[:10], "repo": short, "summary": summary}


def group_activity(items: list[dict[str, str]], limit: int = 4) -> list[dict[str, str]]:
    """One line per repository and day, newest first, releases leading."""
    groups: dict[tuple[str, str], list[str]] = {}
    for item in items:
        summaries = groups.setdefault((item["date"], item["repo"]), [])
        if item["summary"] not in summaries:
            summaries.append(item["summary"])
    lines = []
    for (day, repo), summaries in sorted(groups.items(), key=lambda pair: pair[0][0], reverse=True):
        releases = [text.removeprefix("released ") for text in summaries if text.startswith("released ")]
        parts = [text for text in summaries if not text.startswith("released ")]
        if len(releases) == 1:
            parts.insert(0, f"released {releases[0]}")
        elif releases:
            parts.insert(0, f"{len(releases)} releases, up to {releases[0]}")
        lines.append({"date": day, "repo": repo, "summary": " · ".join(parts)})
    return lines[:limit]


def collect(config: dict[str, Any], token: str | None, offline: bool = False) -> dict[str, Any]:
    username = config["username"]
    data = copy.deepcopy(config["snapshot"])
    data["sources"] = {}
    data["refreshed"] = date.today().isoformat()
    if offline:
        return data
    user = urllib.parse.quote(username)

    def attempt(name: str, fetch) -> None:
        try:
            fetch()
            data["sources"][name] = "live"
        except FAILURES as exc:
            print(f"warning: {name} unavailable, using snapshot ({exc})")

    def profile() -> None:
        info = request(f"/users/{user}", token)
        data["public_repos"] = int(info["public_repos"])
        data["followers"] = int(info["followers"])

    def repositories() -> None:
        repos = request(f"/users/{user}/repos?per_page=100&type=owner&sort=pushed", token)
        own = [repo for repo in repos if not repo.get("fork")]
        data["stars"] = sum(int(repo.get("stargazers_count", 0)) for repo in own)
        data["repos"] = {
            repo["name"]: {
                "stars": int(repo.get("stargazers_count", 0)),
                "pushed_at": repo.get("pushed_at") or repo.get("updated_at"),
                "language": repo.get("language"),
            }
            for repo in repos
        }
        counts: dict[str, int] = {}
        for repo in own:
            if repo.get("language"):
                counts[repo["language"]] = counts.get(repo["language"], 0) + 1
        data["languages"] = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    def events() -> None:
        found = []
        for event in request(f"/users/{user}/events/public?per_page=100", token):
            item = summarize(event, username)
            if item is not None:
                found.append(item)
        if found:
            data["activity"] = group_activity(found)

    def release() -> None:
        latest = request(f"/repos/{user}/{config['release_repo']}/releases/latest", token)
        data["release"] = {
            "tag": latest["tag_name"],
            "published_at": latest.get("published_at"),
            "url": latest.get("html_url"),
        }

    def calendar() -> None:
        if not token:
            raise ValueError("the GraphQL API needs a token")
        answer = request("/graphql", token, {"query": CALENDAR_QUERY, "variables": {"login": username}})
        cal = answer["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        days = [day for week in cal["weeks"] for day in week["contributionDays"]]
        data["calendar"] = {
            "total": int(cal["totalContributions"]),
            "start": days[0]["date"],
            "counts": [int(day["contributionCount"]) for day in days],
        }

    attempt("profile", profile)
    attempt("repositories", repositories)
    attempt("events", events)
    attempt("release", release)
    attempt("calendar", calendar)
    return data


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
