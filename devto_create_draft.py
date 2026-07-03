#!/usr/bin/env python3
"""Create a dev.to draft for an existing local article.

This script reads an article from an article directory, posts a new draft
article to the dev.to API, and stores the returned devto_id in the file's JSON
frontmatter so the article can later be updated from the local source.

Example:

        DEVTO_API_KEY=... python3 devto_create_draft.py articles/architecture-vs-simplicity \
      --api-base-url https://dev.to/api \
      --api-key-env DEVTO_API_KEY

The script refuses to create a second remote article when a devto_id is already
present.
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
    update_article_devto_id,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a dev.to draft for a local article and store its dev.to ID.")
    parser.add_argument("article_dir", type=Path, help="article directory containing article.md")
    parser.add_argument("--api-base-url", default="https://dev.to/api", help="dev.to API base URL")
    parser.add_argument("--api-key-env", default="DEVTO_API_KEY", help="environment variable containing the API key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    document = read_article_document(article_path_from_dir(args.article_dir))
    if document.frontmatter.get("devto_id") is not None:
        raise DevtoError(f"article already has a dev.to ID: {document.frontmatter['devto_id']}")

    api_key = require_api_key(args.api_key_env)
    response = request_json(
        "POST",
        article_endpoint(args.api_base_url),
        api_key,
        {"article": build_article_payload(document, published=False)},
    )

    devto_id = response.get("id")
    if not isinstance(devto_id, int) or isinstance(devto_id, bool):
        raise DevtoError("dev.to create response did not include an integer id")

    update_article_devto_id(document, devto_id)
    print(f"created dev.to draft for {document.slug}: {devto_id}")
    print(f"added article ID to article frontmatter: {document.path}")


if __name__ == "__main__":
    try:
        main()
    except DevtoError as error:
        fail(str(error))
