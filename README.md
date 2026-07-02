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

Each article lives at `articles/{slug}/article.md`. The `{slug}` directory name
is the stable local identity for the article, replacing the old top-level key in
the metadata file.

Article files start with strict JSON frontmatter delimited by `---` lines. The
frontmatter stores the article attributes accepted by the Forem/dev.to article
create and update endpoints, plus the local `devto_id` used to update an
existing remote article. The Markdown after the closing delimiter is the article
body and is sent as `body_markdown`.

Example `articles/architecture-vs-simplicity/article.md`:

```markdown
---
{
  "devto_id": 1234567,
  "title": "Architecture vs simplicity",
  "published": false,
  "description": "A short summary for dev.to",
  "tags": "architecture, software",
  "canonical_url": null,
  "main_image": null,
  "series": null,
  "organization_id": null
}
---

Article body starts here.
```

Supported frontmatter fields:

- `devto_id`: remote dev.to article ID, or `null` before the draft is created.
- `title`: article title.
- `published`: whether the article should be published.
- `description`: dev.to article description.
- `tags`: comma-separated dev.to tag string.
- `canonical_url`: canonical article URL, or `null`.
- `main_image`: main image URL, or `null`.
- `series`: dev.to series name, or `null`.
- `organization_id`: optional dev.to organization ID, or `null`.

The scripts keep using only the Python standard library. The frontmatter is JSON,
not YAML, so no frontmatter parser dependency is required.

## Tooling approach

The workflow is implemented as small composable Python scripts using only the
Python standard library. Type annotations. Unix philosophy. CI calls the same
scripts that can be run locally.

## Mapping Markdown files to dev.to articles

1. Each article is stored at `articles/{slug}/article.md`, such as `articles/architecture-vs-simplicity/article.md`.
2. The slug must contain only lowercase letters, numbers, and hyphens.
3. New articles have `devto_id` set to `null`.
4. After creating a new article through the API, the draft script records the new remote ID in the article frontmatter.
5. The sync script updates only changed `articles/{slug}/article.md` files that already have a `devto_id`.
