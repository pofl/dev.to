#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from devto_common import fail, load_metadata, save_metadata


KEY_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")


def title_from_key(key: str) -> str:
    return key.replace("-", " ").capitalize()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local dev.to article file and metadata entry.")
    parser.add_argument("key", help="stable article key, also used as the default directory name")
    parser.add_argument("--title", help="article title; defaults to a title derived from the key")
    parser.add_argument("--metadata", type=Path, default=Path("devto/articles.json"), help="metadata JSON path")
    parser.add_argument("--articles-dir", type=Path, default=Path("articles"), help="directory for article folders")
    parser.add_argument("--description", default="", help="dev.to article description")
    parser.add_argument("--tag", action="append", default=[], dest="tags", help="dev.to tag; can be repeated")
    parser.add_argument("--canonical-url", default=None, help="canonical URL for the article")
    parser.add_argument("--cover-image", default=None, help="cover image URL for the article")
    parser.add_argument("--series", default=None, help="dev.to series name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    key = args.key
    if not KEY_PATTERN.fullmatch(key):
        fail("article key must contain only lowercase letters, numbers, and hyphens")

    metadata = load_metadata(args.metadata)
    if key in metadata:
        fail(f"article key already exists: {key}")

    article_path = args.articles_dir / key / "article.md"
    if article_path.exists():
        fail(f"article file already exists: {article_path}")

    title = args.title or title_from_key(key)
    metadata[key] = {
        "canonical_url": args.canonical_url,
        "cover_image": args.cover_image,
        "description": args.description,
        "devto_id": None,
        "published": False,
        "series": args.series,
        "source": article_path.as_posix(),
        "tags": args.tags,
        "title": title,
    }

    article_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.write_text(f"# {title}\n\n", encoding="utf-8")
    save_metadata(args.metadata, metadata)
    print(f"created {article_path} and metadata entry {key}")


if __name__ == "__main__":
    main()
