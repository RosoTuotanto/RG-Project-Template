"""
Makes the repository's issue labels match .github/labels.json.

Labels in the file are created, or updated in place when one with the same name (in any letter case)
already exists, so issues keep the labels they carry. Labels not in the file are deleted, which also
removes them from every issue that had them. Standard library only.

Usage: GITHUB_REPOSITORY=owner/repo GITHUB_TOKEN=... python3 sync_labels.py
"""

import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import quote

LABELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labels.json")


class SyncError(Exception):
    """A GitHub API refusal, reported as a single Error: line."""


class GitHubApi:
    def __init__(self, base_url: str, repository: str, token: str) -> None:
        self.labels_url = f"{base_url.rstrip('/')}/repos/{repository}/labels"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def request(self, method: str, url: str, payload: dict | None = None) -> tuple[object, str]:
        """Send one request and return the decoded JSON body (or None) and the Link header."""
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, method=method, headers=self.headers)

        if data is not None:
            request.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(request) as response:
                body = response.read()
                return (json.loads(body) if body else None), response.headers.get("Link", "")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise SyncError(f"GitHub answered {error.code} to {method} {url}: {detail}")

    def list_labels(self) -> list[dict]:
        labels = []
        url = f"{self.labels_url}?per_page=100"

        while url:
            page, link = self.request("GET", url)
            labels.extend(page)
            url = next_page(link)

        return labels

    def label_url(self, name: str) -> str:
        return f"{self.labels_url}/{quote(name, safe='')}"


def next_page(link_header: str) -> str:
    for part in link_header.split(","):
        url, _, rel = part.partition(";")

        if rel.strip() == 'rel="next"':
            return url.strip().strip("<>")

    return ""


def normalize(label: dict) -> dict:
    return {
        "name": label["name"],
        "color": label.get("color", "ffffff").lstrip("#").lower(),
        "description": label.get("description") or "",
    }


def sync_labels(api: GitHubApi, wanted_labels: list[dict]) -> list[str]:
    """Bring the repository's labels in line with wanted_labels and return one line per change."""
    existing = {label["name"].casefold(): normalize(label) for label in api.list_labels()}
    wanted = {label["name"].casefold(): normalize(label) for label in wanted_labels}
    changes = []

    for key, label in wanted.items():
        current = existing.get(key)

        if current is None:
            api.request("POST", api.labels_url, label)
            changes.append(f"created `{label['name']}`")
        elif current != label:
            payload = {"new_name": label["name"], "color": label["color"], "description": label["description"]}
            api.request("PATCH", api.label_url(current["name"]), payload)
            changes.append(f"updated `{label['name']}`")
        else:
            changes.append(f"unchanged `{label['name']}`")

    for key, current in existing.items():
        if key not in wanted:
            api.request("DELETE", api.label_url(current["name"]))
            changes.append(f"deleted `{current['name']}`")

    return changes


def main() -> None:
    repository = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    base_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    with open(LABELS_FILE, "r", encoding="utf-8") as file:
        wanted_labels = json.load(file)

    try:
        changes = sync_labels(GitHubApi(base_url, repository, token), wanted_labels)
    except SyncError as error:
        print(f"Error: {error}")
        sys.exit(1)

    for change in changes:
        print(f"- {change}")


if __name__ == "__main__":
    main()
