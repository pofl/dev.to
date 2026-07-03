#!/usr/bin/env python3
"""Sync changed article directories to dev.to.

For each directory passed on the command line, it uploads articles/<slug>/article.md
to dev.to when a devto_id is available in JSON frontmatter.

Example:

    DEVTO_API_KEY=... python3 scripts/devto_sync_changed.py \
      articles/foo articles/bar \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY

Directories that do not contain article files or do not have a devto_id are reported and skipped.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from devto_common import (
    DevtoError,
    article_endpoint,
    article_path_from_dir,
    build_article_payload,
    fail,
    read_article_document,
    request_json,
    require_api_key,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync changed article directories to dev.to.")
    parser.add_argument("article_dirs", nargs="+", type=Path, help="changed article directories containing article.md")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = require_api_key(args.api_key_env)
    synced = 0
    skipped = 0

    for article_dir in args.article_dirs:
        path = article_path_from_dir(article_dir)
        if not path.exists():
            print(f"article file no longer exists: {path}, skipping", file=sys.stderr)
            skipped += 1
            continue

        document = read_article_document(path)
        devto_id = document.frontmatter.get("devto_id")
        if not isinstance(devto_id, int) or isinstance(devto_id, bool):
            print(f"{document.slug}: no devto_id, skipping (run devto_create_draft.py {article_dir} first)", file=sys.stderr)
            skipped += 1
            continue

        request_json(
            "PUT",
            article_endpoint(args.api_base_url, devto_id),
            api_key,
            {"article": build_article_payload(document)},
        )
        print(f"updated dev.to article for {document.slug}: {devto_id}")
        synced += 1

    print(f"done: {synced} updated, {skipped} skipped")


if __name__ == "__main__":
    try:
        main()
    except DevtoError as error:
        fail(str(error))
