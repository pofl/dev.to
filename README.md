# dev.to markdown publishing

This repository keeps dev.to articles in git and provides small Python scripts for creating local article files, creating dev.to drafts, and updating existing dev.to articles from Markdown. A GitHub Action syncs changed articles to dev.to automatically on every push to `main`.

## Goals

- Store each article as a Markdown file in this repository.
- Treat the repository as the source of truth for article content and editable metadata.
- On merge to `main`, sync only the articles changed by that merge to dev.to.
- Support creating new dev.to articles and updating existing ones.
- Keep the design compatible with the current Forem/dev.to API while avoiding a design that depends on deprecated behavior.
- Prefer simple repository formats and avoid unnecessary dependencies.
- Make the same publishing operations available both locally and in CI.

## Metadata approach

Use a single JSON file for article metadata instead of Markdown frontmatter. This keeps the Markdown files clean, avoids adding a frontmatter parser dependency, and makes the sync format close to the explicit JSON payload expected by newer Forem/dev.to API endpoints.

Example article body:

```markdown
Article body starts here.
```

Example metadata in `devto/articles.json`:

```json
{
  "architecture-vs-simplicity": {
    "devto_id": 1234567,
    "source": "articles/architecture-vs-simplicity/article.md",
    "title": "Architecture vs simplicity",
    "published": false,
    "description": "A short summary for dev.to",
    "tags": ["architecture", "software"],
    "canonical_url": null,
    "cover_image": null,
    "series": null
  }
}
```

The sync script reads the Markdown body from `source`, reads metadata from `devto/articles.json`, and translates both into the request body expected by the API.

## Tooling approach

The workflow is implemented as small composable Python scripts using only the
Python standard library. Type annotations. Unix philosophy. CI calls the same
scripts that can be run locally.

## Mapping Markdown files to dev.to articles

The sync tool needs a stable identity that survives file moves and title changes. The JSON object key is that stable identity.

Recommended mapping:

1. Each article entry in `devto/articles.json` has a stable key such as `architecture-vs-simplicity`.
2. The entry stores both `source` and `devto_id`.
3. New articles have an entry with a `source` but no remote ID yet.
4. After creating a new article through the API, the sync tool records the new remote ID in `devto/articles.json`.
