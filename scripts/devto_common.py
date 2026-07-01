#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, NoReturn

JsonObject = dict[str, Any]
JsonValue = JsonObject | list[Any]
Metadata = dict[str, JsonObject]
DOTENV_PATH = Path(".env")
FOREM_API_ACCEPT = "application/vnd.forem.api-v1+json"
USER_AGENT = "dev-to-markdown-sync/1.0"


def fail(message: str) -> NoReturn:
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


def parse_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("export "):
            stripped = stripped.removeprefix("export ").lstrip()

        key, separator, value = stripped.partition("=")
        key = key.strip()
        if not separator or not key:
            fail(f"{path}:{line_number}: expected KEY=value")

        values[key] = value.strip().strip('"\'')

    return values


def require_api_key(env_name: str) -> str:
    api_key = os.environ.get(env_name)
    if not api_key:
        api_key = parse_dotenv(DOTENV_PATH).get(env_name)
    if not api_key:
        fail(f"missing dev.to API key in ${env_name} or {DOTENV_PATH}")
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

    for field in ("description", "canonical_url", "series"):
        value = entry.get(field)
        if value is not None:
            if not isinstance(value, str):
                fail(f"metadata field must be a string or null: {field}")
            payload[field] = value

    cover_image = entry.get("cover_image")
    if cover_image is not None:
        if not isinstance(cover_image, str):
            fail("metadata field must be a string or null: cover_image")
        payload["main_image"] = cover_image

    tags = entry.get("tags", [])
    if tags is not None:
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            fail("metadata field must be a list of strings: tags")
        payload["tags"] = ", ".join(tags)

    return payload


def request_json_value(method: str, url: str, api_key: str, payload: JsonObject | None = None) -> JsonValue:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": FOREM_API_ACCEPT,
        "User-Agent": USER_AGENT,
        "api-key": api_key,
    }
    if body is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers=headers,
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        reason = getattr(error, "reason", None) or error.msg
        message = f"{method} {url} failed with HTTP {error.code} {reason}"
        if error_body:
            message = f"{message}: {error_body}"
        else:
            message = f"{message} (empty response body)"
        fail(message)
    except urllib.error.URLError as error:
        fail(f"{method} {url} failed: {error.reason}")

    if not response_body:
        return {}

    try:
        data = json.loads(response_body)
    except json.JSONDecodeError as error:
        fail(f"{method} {url} returned invalid JSON: {error}")

    if not isinstance(data, dict) and not isinstance(data, list):
        fail(f"{method} {url} returned JSON that is not an object or array")
    return data


def request_json(method: str, url: str, api_key: str, payload: JsonObject | None = None) -> JsonObject:
    data = request_json_value(method, url, api_key, payload)
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
