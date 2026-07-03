#!/usr/bin/env python3
"""Import existing dev.to articles into the local repository.

This script fetches the authenticated user's articles from the dev.to API and
stores each one as a local Markdown file under articles/<slug>/article.md with
JSON frontmatter.

Example:

    DEVTO_API_KEY=... python3 devto_import_articles.py \
      --force \
      --articles-dir articles \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY \
      --per-page 100

Use --force to overwrite existing local article files. The default behavior
skips articles that already exist locally so that imports can be repeated safely.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from devto_common import (
    DevtoError,
    JsonObject,
    article_path_for_slug,
    fail,
    request_json_value,
    require_api_key,
    validate_slug,
    write_article_document,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import existing dev.to articles into the local repository.")
    parser.add_argument("--force", action="store_true", help="overwrite existing local article files")
    parser.add_argument("--articles-dir", type=Path, default=Path("articles"), help="directory for article folders")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    parser.add_argument("--per-page", type=int, default=100, help="articles to fetch per page when importing all articles")
    return parser.parse_args()


def require_string(article: JsonObject, field: str) -> str:
    value = article.get(field)
    if not isinstance(value, str) or not value:
        raise DevtoError(f"dev.to article is missing required string field: {field}")
    return value


def optional_string(article: JsonObject, field: str) -> str | None:
    value = article.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise DevtoError(f"dev.to article field must be a string or null: {field}")
    return value


def require_int(article: JsonObject, field: str) -> int:
    value = article.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise DevtoError(f"dev.to article is missing required integer field: {field}")
    return value


def normalize_tags(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return ", ".join(value)
    if isinstance(value, str):
        return ", ".join(tag.strip() for tag in value.split(",") if tag.strip())
    raise DevtoError("dev.to article field must be a list of strings or comma-separated string: tags")


def user_articles_endpoint(api_base_url: str, page: int, per_page: int) -> str:
    base = api_base_url.rstrip("/")
    return f"{base}/articles/me/all?{urlencode({'page': page, 'per_page': per_page})}"


def fetch_articles(api_base_url: str, api_key: str, per_page: int) -> list[JsonObject]:
    articles: list[JsonObject] = []
    page = 1
    while True:
        data = request_json_value("GET", user_articles_endpoint(api_base_url, page, per_page), api_key)
        if not isinstance(data, list):
            raise DevtoError("dev.to article list response was not an array")
        if not data:
            return articles

        for item in data:
            if not isinstance(item, dict):
                raise DevtoError("dev.to article list response contained a non-object item")
            articles.append(item)

        if len(data) < per_page:
            return articles
        page += 1


def build_frontmatter(article: JsonObject) -> JsonObject:
    return {
        "canonical_url": optional_string(article, "canonical_url"),
        "description": optional_string(article, "description") or "",
        "devto_id": require_int(article, "id"),
        "main_image": optional_string(article, "cover_image"),
        "published": article.get("published_at") is not None or article.get("published_timestamp") is not None,
        "series": optional_string(article, "series"),
        "tags": normalize_tags(article.get("tags")),
        "title": require_string(article, "title"),
    }


def import_article(article: JsonObject, articles_dir: Path, *, force: bool) -> str:
    slug = validate_slug(require_string(article, "slug"))
    body_markdown = require_string(article, "body_markdown")
    article_path = article_path_for_slug(slug, articles_dir)

    if not force and article_path.exists():
        print(f"skipped existing article: {slug}")
        return "skipped"

    write_article_document(article_path, build_frontmatter(article), body_markdown)
    print(f"imported article: {slug}")
    return "imported"


def main() -> None:
    args = parse_args()
    if args.per_page < 1 or args.per_page > 1000:
        raise DevtoError("--per-page must be between 1 and 1000")

    api_key = require_api_key(args.api_key_env)
    articles = fetch_articles(args.api_base_url, api_key, args.per_page)

    imported = 0
    skipped = 0
    for article in articles:
        result = import_article(article, args.articles_dir, force=args.force)
        if result == "imported":
            imported += 1
        else:
            skipped += 1

    print(f"import complete: {imported} imported, {skipped} skipped")


if __name__ == "__main__":
    try:
        main()
    except DevtoError as error:
        fail(str(error))
