#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

JsonObject = dict[str, Any]
JsonValue = JsonObject | list[Any]
DOTENV_PATH = Path(".env")
FOREM_API_ACCEPT = "application/vnd.forem.api-v1+json"
USER_AGENT = "dev-to-markdown-sync/1.0"
ARTICLE_FILENAME = "article.md"
FRONTMATTER_DELIMITER = "---"
SLUG_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")
FRONTMATTER_FIELD_ORDER = (
    "devto_id",
    "title",
    "published",
    "description",
    "tags",
    "canonical_url",
    "main_image",
    "series",
    "organization_id",
)


@dataclass
class ArticleDocument:
    path: Path
    slug: str
    frontmatter: JsonObject
    body_markdown: str


class DevtoError(Exception):
    pass


def fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def validate_slug(slug: str) -> str:
    if not SLUG_PATTERN.fullmatch(slug):
        raise DevtoError("article slug must contain only lowercase letters, numbers, and hyphens")
    return slug


def article_path_for_slug(slug: str, articles_dir: Path = Path("articles")) -> Path:
    return articles_dir / validate_slug(slug) / ARTICLE_FILENAME


def article_path_from_dir(article_dir: Path) -> Path:
    return Path(article_dir) / ARTICLE_FILENAME


def slug_from_article_path(path: Path) -> str | None:
    article_path = Path(path)
    if article_path.name != ARTICLE_FILENAME:
        return None

    slug = article_path.parent.name
    return slug if SLUG_PATTERN.fullmatch(slug) else None


def ordered_frontmatter(frontmatter: JsonObject) -> JsonObject:
    ordered: JsonObject = {}
    for field in FRONTMATTER_FIELD_ORDER:
        if field in frontmatter:
            ordered[field] = frontmatter[field]
    for field in sorted(frontmatter):
        if field not in ordered:
            ordered[field] = frontmatter[field]
    return ordered


def split_frontmatter(path: Path, text: str) -> tuple[JsonObject, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise DevtoError(f"{path}: expected JSON frontmatter starting with {FRONTMATTER_DELIMITER}")

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            end_index = index
            break
    if end_index is None:
        raise DevtoError(f"{path}: missing closing JSON frontmatter delimiter")

    try:
        frontmatter = json.loads("".join(lines[1:end_index]))
    except json.JSONDecodeError as error:
        raise DevtoError(f"{path}: invalid JSON frontmatter: {error}") from error
    if not isinstance(frontmatter, dict):
        raise DevtoError(f"{path}: JSON frontmatter must be an object")

    return frontmatter, "".join(lines[end_index + 1 :])


def render_article_document(frontmatter: JsonObject, body_markdown: str) -> str:
    rendered_frontmatter = json.dumps(ordered_frontmatter(frontmatter), indent=2) + "\n"
    return f"{FRONTMATTER_DELIMITER}\n{rendered_frontmatter}{FRONTMATTER_DELIMITER}\n{body_markdown}"


def read_article_document(path: Path) -> ArticleDocument:
    slug = slug_from_article_path(path)
    if slug is None:
        raise DevtoError(f"article path must end with <slug>/{ARTICLE_FILENAME}: {path}")
    if not path.is_file():
        raise DevtoError(f"article file does not exist: {path}")

    frontmatter, body_markdown = split_frontmatter(path, path.read_text(encoding="utf-8"))
    return ArticleDocument(path=path, slug=slug, frontmatter=frontmatter, body_markdown=body_markdown)


def write_article_document(path: Path, frontmatter: JsonObject, body_markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_article_document(frontmatter, body_markdown), encoding="utf-8")


def update_article_devto_id(document: ArticleDocument, devto_id: int) -> None:
    if not isinstance(devto_id, int) or isinstance(devto_id, bool):
        raise DevtoError("dev.to ID must be an integer")
    document.frontmatter["devto_id"] = devto_id
    write_article_document(document.path, document.frontmatter, document.body_markdown)


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
            raise DevtoError(f"{path}:{line_number}: expected KEY=value")

        values[key] = value.strip().strip('"\'')

    return values


def require_api_key(env_name: str) -> str:
    api_key = os.environ.get(env_name)
    if not api_key:
        api_key = parse_dotenv(DOTENV_PATH).get(env_name)
    if not api_key:
        raise DevtoError(f"missing dev.to API key in ${env_name} or {DOTENV_PATH}")
    return api_key


def build_article_payload(document: ArticleDocument, *, published: bool | None = None) -> JsonObject:
    frontmatter = document.frontmatter
    title = frontmatter.get("title")
    if not isinstance(title, str) or not title:
        raise DevtoError(f"{document.path}: JSON frontmatter is missing required string field: title")

    frontmatter_published = frontmatter.get("published", False)
    if not isinstance(frontmatter_published, bool):
        raise DevtoError(f"{document.path}: JSON frontmatter field must be a boolean: published")

    payload: JsonObject = {
        "title": title,
        "body_markdown": document.body_markdown,
        "published": frontmatter_published if published is None else published,
    }

    for field in ("description", "canonical_url", "main_image", "series"):
        value = frontmatter.get(field)
        if value is not None:
            if not isinstance(value, str):
                raise DevtoError(f"{document.path}: JSON frontmatter field must be a string or null: {field}")
            payload[field] = value

    tags = frontmatter.get("tags", "")
    if tags is not None:
        if not isinstance(tags, str):
            raise DevtoError(f"{document.path}: JSON frontmatter field must be a string or null: tags")
        payload["tags"] = tags

    organization_id = frontmatter.get("organization_id")
    if organization_id is not None:
        if not isinstance(organization_id, int) or isinstance(organization_id, bool):
            raise DevtoError(f"{document.path}: JSON frontmatter field must be an integer or null: organization_id")
        payload["organization_id"] = organization_id

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
        raise DevtoError(message) from error
    except urllib.error.URLError as error:
        raise DevtoError(f"{method} {url} failed: {error.reason}") from error

    if not response_body:
        return {}

    try:
        data = json.loads(response_body)
    except json.JSONDecodeError as error:
        raise DevtoError(f"{method} {url} returned invalid JSON: {error}") from error

    if not isinstance(data, dict) and not isinstance(data, list):
        raise DevtoError(f"{method} {url} returned JSON that is not an object or array")
    return data


def request_json(method: str, url: str, api_key: str, payload: JsonObject | None = None) -> JsonObject:
    data = request_json_value(method, url, api_key, payload)
    if not isinstance(data, dict):
        raise DevtoError(f"{method} {url} returned JSON that is not an object")
    return data


def article_endpoint(api_base_url: str, article_id: int | None = None) -> str:
    base = api_base_url.rstrip("/")
    if article_id is None:
        return f"{base}/articles"
    return f"{base}/articles/{article_id}"


def require_devto_id(document: ArticleDocument) -> int:
    devto_id = document.frontmatter.get("devto_id")
    if not isinstance(devto_id, int) or isinstance(devto_id, bool):
        raise DevtoError(f"{document.path}: JSON frontmatter is missing required integer field: devto_id")
    return devto_id
