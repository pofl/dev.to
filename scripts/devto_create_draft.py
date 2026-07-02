#!/usr/bin/env python3
"""Create a dev.to draft for an existing local article entry.

This script reads the article body and metadata from the repository, posts a
new draft article to the dev.to API, and stores the returned devto_id in
/devto/articles.json so the article can later be updated from the local source.

Example:

    DEVTO_API_KEY=... python3 scripts/devto_create_draft.py architecture-vs-simplicity \
      --metadata devto/articles.json \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY

The script requires a metadata entry for the given key and refuses to create a
second remote article when a devto_id is already present.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from devto_common import (
    article_endpoint,
    build_article_payload,
    fail,
    load_metadata,
    read_article_body,
    request_json,
    require_api_key,
    require_entry,
    save_metadata,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a dev.to draft for a local article and store its dev.to ID.")
    parser.add_argument("key", help="stable article key from devto/articles.json")
    parser.add_argument("--metadata", type=Path, default=Path("devto/articles.json"), help="metadata JSON path")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = load_metadata(args.metadata)
    entry = require_entry(metadata, args.key)
    if entry.get("devto_id") is not None:
        fail(f"article already has a dev.to ID: {entry['devto_id']}")

    body_markdown = read_article_body(entry, args.metadata)
    api_key = require_api_key(args.api_key_env)
    response = request_json(
        "POST",
        article_endpoint(args.api_base_url),
        api_key,
        {"article": build_article_payload(entry, body_markdown, published=False)},
    )

    devto_id = response.get("id")
    if not isinstance(devto_id, int) or isinstance(devto_id, bool):
        fail("dev.to create response did not include an integer id")

    entry["devto_id"] = devto_id
    save_metadata(args.metadata, metadata)
    print(f"created dev.to draft for {args.key}: {devto_id}")
    print(f"added article ID to article config: {args.metadata}")


if __name__ == "__main__":
    main()
