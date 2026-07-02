#!/usr/bin/env python3
"""Sync changed article files to dev.to.

For each file passed on the command line, it uploads articles/<slug>/article.md
to dev.to when a devto_id is available in JSON frontmatter.

Example:

    DEVTO_API_KEY=... python3 scripts/devto_sync_changed.py \
      articles/foo/article.md articles/bar/article.md \
      --articles-dir articles \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY

Files that are not article files or do not have a devto_id are reported and skipped.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from devto_common import (
    article_endpoint,
    build_article_payload,
    read_article_document,
    request_json,
    require_api_key,
    slug_from_article_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync changed article files to dev.to.")
    parser.add_argument("files", nargs="+", help="changed article file paths (relative to repository root)")
    parser.add_argument("--articles-dir", type=Path, default=Path("articles"), help="directory for article folders")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = require_api_key(args.api_key_env)
    synced = 0
    skipped = 0

    for file_path in args.files:
        path = Path(file_path)
        slug = slug_from_article_path(path, args.articles_dir)
        if slug is None:
            print(f"not an article file: {file_path}, skipping", file=sys.stderr)
            skipped += 1
            continue
        if not path.exists():
            print(f"article file no longer exists: {file_path}, skipping", file=sys.stderr)
            skipped += 1
            continue

        document = read_article_document(path, args.articles_dir)
        devto_id = document.frontmatter.get("devto_id")
        if not isinstance(devto_id, int) or isinstance(devto_id, bool):
            print(f"{slug}: no devto_id, skipping (run devto_create_draft.py first)", file=sys.stderr)
            skipped += 1
            continue

        request_json(
            "PUT",
            article_endpoint(args.api_base_url, devto_id),
            api_key,
            {"article": build_article_payload(document)},
        )
        print(f"updated dev.to article for {slug}: {devto_id}")
        synced += 1

    print(f"done: {synced} updated, {skipped} skipped")


if __name__ == "__main__":
    main()
