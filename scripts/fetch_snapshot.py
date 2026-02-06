#!/usr/bin/env python3
"""Fetch weekly LeRobot ecosystem metrics and store snapshot CSV rows."""

from __future__ import annotations

import csv
import datetime as dt
import os
import sys
from pathlib import Path
from typing import Any

import requests

DATA_PATH = Path("data/weekly_snapshots.csv")
GITHUB_API_BASE = "https://api.github.com"
HF_DATASETS_API = "https://huggingface.co/api/datasets"
TARGET_REPO = "huggingface/lerobot"
TIMEOUT_SECONDS = 30

CSV_HEADERS = [
    "snapshot_date",
    "snapshot_timestamp_utc",
    "lerobot_github_stars",
    "hf_lerobot_dataset_count",
    "hf_unique_dataset_uploaders",
    "github_topic_robotics_repo_count",
    "github_topic_lerobot_repo_count",
]


class MetricsError(RuntimeError):
    """Raised when one or more metrics cannot be fetched."""


def _github_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_get_json(path_or_url: str, token: str | None) -> dict[str, Any]:
    url = path_or_url if path_or_url.startswith("http") else f"{GITHUB_API_BASE}{path_or_url}"
    response = requests.get(url, headers=_github_headers(token), timeout=TIMEOUT_SECONDS)
    if response.status_code >= 400:
        raise MetricsError(f"GitHub API error ({response.status_code}) for {url}: {response.text[:200]}")
    return response.json()


def hf_get_datasets(token: str | None) -> list[dict[str, Any]]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "search": "lerobot",
        "limit": "1000",
        "full": "true",
    }
    response = requests.get(HF_DATASETS_API, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
    if response.status_code >= 400:
        raise MetricsError(
            f"Hugging Face API error ({response.status_code}) for {response.url}: {response.text[:200]}"
        )

    payload = response.json()
    if not isinstance(payload, list):
        raise MetricsError("Unexpected Hugging Face API response format for dataset listing")

    return payload


def fetch_lerobot_stars(github_token: str | None) -> int:
    payload = github_get_json(f"/repos/{TARGET_REPO}", github_token)
    stars = payload.get("stargazers_count")
    if not isinstance(stars, int):
        raise MetricsError("Missing stargazers_count in GitHub repo response")
    return stars


def fetch_topic_repo_count(topic: str, github_token: str | None) -> int:
    payload = github_get_json(f"/search/repositories?q=topic:{topic}&per_page=1", github_token)
    total_count = payload.get("total_count")
    if not isinstance(total_count, int):
        raise MetricsError(f"Missing total_count in GitHub topic search response for topic:{topic}")
    return total_count


def _is_lerobot_dataset(dataset: dict[str, Any]) -> bool:
    dataset_id = str(dataset.get("id", "")).lower()
    if "lerobot" in dataset_id:
        return True

    tags = dataset.get("tags") or []
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str) and "lerobot" in tag.lower():
                return True
    return False


def _extract_uploader(dataset: dict[str, Any]) -> str | None:
    author = dataset.get("author")
    if isinstance(author, str) and author.strip():
        return author.strip().lower()

    dataset_id = dataset.get("id")
    if isinstance(dataset_id, str) and "/" in dataset_id:
        owner = dataset_id.split("/", 1)[0].strip()
        if owner:
            return owner.lower()

    return None


def fetch_hf_dataset_metrics(hf_token: str | None) -> tuple[int, int]:
    raw_datasets = hf_get_datasets(hf_token)
    lerobot_datasets = [dataset for dataset in raw_datasets if _is_lerobot_dataset(dataset)]

    uploaders: set[str] = set()
    for dataset in lerobot_datasets:
        uploader = _extract_uploader(dataset)
        if uploader:
            uploaders.add(uploader)

    return len(lerobot_datasets), len(uploaders)


def _ensure_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()


def append_snapshot(path: Path, row: dict[str, Any]) -> None:
    _ensure_csv(path)
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writerow(row)


def build_snapshot(github_token: str | None, hf_token: str | None) -> dict[str, Any]:
    now = dt.datetime.now(tz=dt.timezone.utc)

    lerobot_stars = fetch_lerobot_stars(github_token)
    robotics_topic_count = fetch_topic_repo_count("robotics", github_token)
    lerobot_topic_count = fetch_topic_repo_count("lerobot", github_token)
    hf_dataset_count, hf_unique_uploaders = fetch_hf_dataset_metrics(hf_token)

    return {
        "snapshot_date": now.date().isoformat(),
        "snapshot_timestamp_utc": now.replace(microsecond=0).isoformat(),
        "lerobot_github_stars": lerobot_stars,
        "hf_lerobot_dataset_count": hf_dataset_count,
        "hf_unique_dataset_uploaders": hf_unique_uploaders,
        "github_topic_robotics_repo_count": robotics_topic_count,
        "github_topic_lerobot_repo_count": lerobot_topic_count,
    }


def main() -> int:
    github_token = os.getenv("GITHUB_TOKEN")
    hf_token = os.getenv("HF_TOKEN")

    try:
        snapshot = build_snapshot(github_token=github_token, hf_token=hf_token)
        append_snapshot(DATA_PATH, snapshot)
    except MetricsError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    except requests.RequestException as error:
        print(f"[ERROR] Network issue while fetching metrics: {error}", file=sys.stderr)
        return 1

    print("Snapshot saved:")
    for key in CSV_HEADERS:
        print(f"  {key}: {snapshot[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
