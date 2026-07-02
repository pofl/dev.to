#!/usr/bin/env python3
"""Create a local article scaffold for the sync workflow.

This script creates a new article directory at articles/<slug>/article.md with
JSON frontmatter and safe draft defaults.

Example:

    python3 scripts/devto_scaffold.py architecture-vs-simplicity \
      --title "Architecture vs simplicity" \
      --description "A short summary for dev.to" \
      --tags "architecture, software" \
      --articles-dir articles \
      --canonical-url https://example.com/architecture-vs-simplicity \      --main-image https://example.com/cover.png \
      --series "Software Design"

The article slug is a stable identifier that is used for future sync operations.
The script refuses to overwrite an existing article file so that accidental data
loss is avoided.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from devto_common import (
    article_path_for_slug,
    fail,
    validate_slug,
    write_article_document,
)


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").capitalize()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local dev.to article file and metadata entry.")
    parser.add_argument("slug", help="stable article slug, also used as the directory name")
    parser.add_argument("--title", help="article title; defaults to a title derived from the slug")
    parser.add_argument("--articles-dir", type=Path, default=Path("articles"), help="directory for article folders")
    parser.add_argument("--description", default="", help="dev.to article description")
    parser.add_argument("--tags", default="", help="dev.to tags as a comma-separated string")
    parser.add_argument("--canonical-url", default=None, help="canonical URL for the article")
    parser.add_argument("--main-image", default=None, help="main image URL for the article")
    parser.add_argument("--organization-id", type=int, default=None, help="dev.to organization ID")
    parser.add_argument("--series", default=None, help="dev.to series name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    slug = validate_slug(args.slug)

    article_path = article_path_for_slug(slug, args.articles_dir)
    if article_path.exists():
        fail(f"article file already exists: {article_path}")

    title = args.title or title_from_slug(slug)
    frontmatter = {
        "canonical_url": args.canonical_url,
        "description": args.description,
        "devto_id": None,
        "main_image": args.main_image,
        "organization_id": args.organization_id,
        "published": False,
        "series": args.series,
        "tags": args.tags,
        "title": title,
    }

    write_article_document(article_path, frontmatter, f"# {title}\n\n")
    print(f"created {article_path}")


if __name__ == "__main__":
    main()
