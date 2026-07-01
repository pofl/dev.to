#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]
Metadata = dict[str, JsonObject]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def load_metadata(path: Path) -> Metadata:
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"{path}: invalid JSON: {error}")

    if not isinstance(data, dict):
        fail(f"{path}: expected a JSON object")

    metadata: Metadata = {}
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            fail(f"{path}: expected object entries keyed by article key")
        metadata[key] = value
    return metadata


def save_metadata(path: Path, metadata: Metadata) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_entry(metadata: Metadata, key: str) -> JsonObject:
    entry = metadata.get(key)
    if entry is None:
        fail(f"unknown article key: {key}")
    return entry


def require_api_key(env_name: str) -> str:
    api_key = os.environ.get(env_name)
    if not api_key:
        fail(f"missing dev.to API key in ${env_name}")
    return api_key


def read_article_body(entry: JsonObject, metadata_path: Path) -> str:
    source = entry.get("source")
    if not isinstance(source, str) or not source:
        fail("metadata entry is missing required string field: source")

    source_path = (metadata_path.parent.parent / source).resolve()
    if not source_path.is_file():
        fail(f"article source does not exist: {source}")
    return source_path.read_text(encoding="utf-8")


def build_article_payload(entry: JsonObject, body_markdown: str, *, published: bool | None = None) -> JsonObject:
    title = entry.get("title")
    if not isinstance(title, str) or not title:
        fail("metadata entry is missing required string field: title")

    payload: JsonObject = {
        "title": title,
        "body_markdown": body_markdown,
        "published": bool(entry.get("published", False)) if published is None else published,
    }

    for field in ("description", "canonical_url", "cover_image", "series"):
        value = entry.get(field)
        if value is not None:
            if not isinstance(value, str):
                fail(f"metadata field must be a string or null: {field}")
            payload[field] = value

    tags = entry.get("tags", [])
    if tags is not None:
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            fail("metadata field must be a list of strings: tags")
        payload["tags"] = tags

    return payload


def request_json(method: str, url: str, api_key: str, payload: JsonObject) -> JsonObject:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "api-key": api_key,
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        fail(f"{method} {url} failed with HTTP {error.code}")
    except urllib.error.URLError as error:
        fail(f"{method} {url} failed: {error.reason}")

    if not response_body:
        return {}

    try:
        data = json.loads(response_body)
    except json.JSONDecodeError as error:
        fail(f"{method} {url} returned invalid JSON: {error}")

    if not isinstance(data, dict):
        fail(f"{method} {url} returned JSON that is not an object")
    return data


def article_endpoint(api_base_url: str, article_id: int | None = None) -> str:
    base = api_base_url.rstrip("/")
    if article_id is None:
        return f"{base}/articles"
    return f"{base}/articles/{article_id}"


def require_devto_id(entry: JsonObject) -> int:
    devto_id = entry.get("devto_id")
    if not isinstance(devto_id, int) or isinstance(devto_id, bool):
        fail("metadata entry is missing required integer field: devto_id")
    return devto_id
