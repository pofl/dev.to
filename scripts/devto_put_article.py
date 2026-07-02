#!/usr/bin/env python3
"""Update an existing dev.to article from the local Markdown source.

This script reads an article from an article directory and sends a PUT
request for the existing remote article identified by the frontmatter devto_id.
It is intended for publishing updates from local Markdown changes back to dev.to.

Example:

        DEVTO_API_KEY=... python3 scripts/devto_put_article.py articles/architecture-vs-simplicity \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY

The script requires that the article frontmatter already has a devto_id, because
it updates an existing remote article rather than creating a new one.
"""
from __future__ import annotations

import argparse
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
    require_devto_id,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update an existing dev.to article from local Markdown and frontmatter.")
    parser.add_argument("article_dir", type=Path, help="article directory containing article.md")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    document = read_article_document(article_path_from_dir(args.article_dir))
    devto_id = require_devto_id(document)
    api_key = require_api_key(args.api_key_env)

    request_json(
        "PUT",
        article_endpoint(args.api_base_url, devto_id),
        api_key,
        {"article": build_article_payload(document)},
    )
    print(f"updated dev.to article for {document.slug}: {devto_id}")


if __name__ == "__main__":
    try:
        main()
    except DevtoError as error:
        fail(str(error))
