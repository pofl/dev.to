#!/usr/bin/env python3
"""Sync changed article files to dev.to.

For each file passed on the command line, it looks up the matching metadata entry
in devto/articles.json and uploads the article to dev.to when a devto_id is
available.

Example:

    DEVTO_API_KEY=... python3 scripts/devto_sync_changed.py \
      articles/foo/article.md articles/bar/article.md \
      --metadata devto/articles.json \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY

Files without a metadata entry or without a devto_id are reported and skippeds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from devto_common import (
    article_endpoint,
    build_article_payload,
    load_metadata,
    read_article_body,
    request_json,
    require_api_key,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync changed article files to dev.to.")
    parser.add_argument("files", nargs="+", help="changed article file paths (relative to repository root)")
    parser.add_argument("--metadata", type=Path, default=Path("devto/articles.json"), help="metadata JSON path")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = load_metadata(args.metadata)

    # Build a reverse index: source path -> article key
    source_to_key: dict[str, str] = {
        entry["source"]: key
        for key, entry in metadata.items()
        if isinstance(entry.get("source"), str) and entry["source"]
    }

    api_key = require_api_key(args.api_key_env)
    synced = 0
    skipped = 0

    for file_path in args.files:
        normalized = str(Path(file_path))
        key = source_to_key.get(normalized)
        if key is None:
            print(f"no metadata entry for {file_path}, skipping", file=sys.stderr)
            skipped += 1
            continue

        entry = metadata[key]
        devto_id = entry.get("devto_id")
        if not isinstance(devto_id, int) or isinstance(devto_id, bool):
            print(f"{key}: no devto_id, skipping (run devto_create_draft.py first)", file=sys.stderr)
            skipped += 1
            continue

        body_markdown = read_article_body(entry, args.metadata)
        request_json(
            "PUT",
            article_endpoint(args.api_base_url, devto_id),
            api_key,
            {"article": build_article_payload(entry, body_markdown)},
        )
        print(f"updated dev.to article for {key}: {devto_id}")
        synced += 1

    print(f"done: {synced} updated, {skipped} skipped")


if __name__ == "__main__":
    main()
