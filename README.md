# dev.to markdown publishing plan

This repository is currently a planning document for a future workflow that keeps dev.to articles in git and syncs changed Markdown files to dev.to after they are merged to `main`.

No publishing code, GitHub Action, or dev.to API client has been chosen yet.

## Goals

- Store each article as a Markdown file in this repository.
- Treat the repository as the source of truth for article content and editable metadata.
- On merge to `main`, sync only the articles changed by that merge to dev.to.
- Support creating new dev.to articles and updating existing ones.
- Keep the design compatible with the current Forem/dev.to API while avoiding a design that depends on deprecated behavior.

## Proposed repository shape

```text
articles/
  my-article/
    article.md
    assets/
      cover.png
devto/
  articles.json
```

- `articles/**/article.md` contains the article body and author-facing metadata.
- `articles/**/assets/` contains images referenced by the article.
- `devto/articles.json` maps stable local article keys to remote dev.to article IDs and other sync state that should not be hand-edited during normal writing.

## Metadata approach

Use YAML frontmatter in each Markdown file as the authoring format, but do not couple the sync implementation to the v0 API's frontmatter behavior.

Example:

```markdown
---
devto_key: architecture-vs-simplicity
title: Architecture vs simplicity
published: false
description: A short summary for dev.to
tags:
  - architecture
  - software
canonical_url:
cover_image:
series:
---

Article body starts here.
```

The future sync tool should parse this frontmatter itself and translate it into the request body expected by the selected API version. This keeps the writing experience convenient while leaving room to use v1 if v0 frontmatter publishing becomes undesirable or unsupported.

## API version tradeoff

### v0 convenience

- v0 can accept Markdown with frontmatter-style metadata.
- This is convenient because the article body and metadata can be submitted together.
- The risk is coupling the project to behavior that may be older or less future-proof.

### v1 future-proofness

- v1 appears to prefer explicit API fields instead of relying on frontmatter.
- This is a better long-term boundary: repository Markdown is our authoring format, and API JSON is the transport format.
- The sync tool has to do slightly more work by parsing frontmatter and building the API payload.

### Recommendation

Author with frontmatter, but implement the sync tool as an adapter:

1. Parse Markdown into an internal article model.
2. Convert that model to the selected dev.to API request.
3. Keep API-version-specific behavior isolated behind a small client boundary.

This gives writers the convenience of frontmatter without making the repository format depend on v0.

## Mapping Markdown files to dev.to articles

The sync tool needs a stable identity that survives file moves and title changes.

Recommended mapping:

1. Each article frontmatter includes a required `devto_key`.
2. `devto/articles.json` maps `devto_key` to the remote dev.to article ID.
3. New articles have a `devto_key` but no remote ID yet.
4. After creating a new article through the API, the sync tool records the new remote ID in `devto/articles.json`.

Example mapping file:

```json
{
  "architecture-vs-simplicity": {
    "devto_id": 1234567,
    "source": "articles/architecture-vs-simplicity/article.md"
  }
}
```

Why this shape:

- The key is stable across path changes.
- The remote dev.to ID is kept out of the article content.
- The mapping can be reviewed in git.
- The sync tool can detect accidental key reuse before publishing.

Path-only mapping is simpler, but it breaks down when files are renamed. Looking up articles remotely by title, slug, or canonical URL is not reliable enough because those values can change and may not be unique.

## Merge-to-main sync flow

1. A pull request changes one or more `articles/**/*.md` files.
2. After the PR is merged, a GitHub Action on `main` computes the changed Markdown files for the merge.
3. For each changed file, the sync tool:
   - parses the Markdown and frontmatter,
   - validates required metadata,
   - reads `devto_key`,
   - looks up the remote article ID in `devto/articles.json`,
   - creates the article if there is no remote ID,
   - updates the article if a remote ID exists,
   - updates `devto/articles.json` if a new remote ID was created.
4. The workflow fails loudly if metadata is invalid or a mapping is ambiguous.

## Open design questions

- Should new articles be created as drafts by default even when frontmatter says `published: true`?
- Should the workflow commit `devto/articles.json` updates back to `main`, or should new article creation require a separate manual bootstrap step?
- Should asset uploads be handled by the tool, or should image URLs point to raw GitHub-hosted files?
- Should deleted Markdown files ever unpublish dev.to articles, or should remote deletion always be manual?
