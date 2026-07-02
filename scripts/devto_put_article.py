#!/usr/bin/env python3
"""Update an existing dev.to article from the local Markdown source.

This script reads the article body from the repository and sends a PUT request
for the existing remote article identified by the metadata entry's devto_id.
It is intended for publishing updates from local Markdown changes back to dev.to.

Example:

    DEVTO_API_KEY=... python3 scripts/devto_put_article.py architecture-vs-simplicity \
      --metadata devto/articles.json \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY

The script requires that the metadata entry already has a devto_id, because it
updates an existing remote article rather than creating a new one.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from devto_common import (
    article_endpoint,
    build_article_payload,
    load_metadata,
    read_article_body,
    request_json,
    require_api_key,
    require_devto_id,
    require_entry,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update an existing dev.to article from local Markdown and metadata.")
    parser.add_argument("key", help="stable article key from devto/articles.json")
    parser.add_argument("--metadata", type=Path, default=Path("devto/articles.json"), help="metadata JSON path")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = load_metadata(args.metadata)
    entry = require_entry(metadata, args.key)
    devto_id = require_devto_id(entry)
    body_markdown = read_article_body(entry, args.metadata)
    api_key = require_api_key(args.api_key_env)

    request_json(
        "PUT",
        article_endpoint(args.api_base_url, devto_id),
        api_key,
        {"article": build_article_payload(entry, body_markdown)},
    )
    print(f"updated dev.to article for {args.key}: {devto_id}")


if __name__ == "__main__":
    main()
