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

## Repository shape

```text
.github/
  workflows/
    sync.yml
articles/
  my-article/
    article.md
    assets/
      cover.png
devto/
  articles.json
scripts/
  devto_common.py
  devto_scaffold.py
  devto_import_articles.py
  devto_create_draft.py
  devto_put_article.py
  devto_sync_changed.py
```

- `articles/**/article.md` contains only the article body.
- `articles/**/assets/` contains images referenced by the article.
- `devto/articles.json` stores article metadata, source paths, remote dev.to article IDs, and other sync state.
- `scripts/*.py` contains small typed Python entrypoints for local and CI use.

## Script usage

The scripts use only the Python standard library and should be run from the repository root.

### Scaffold a local article

```sh
python3 scripts/devto_scaffold.py architecture-vs-simplicity \
  --title "Architecture vs simplicity" \
  --description "A short summary for dev.to" \
  --tag architecture \
  --tag software
```

This creates `articles/architecture-vs-simplicity/article.md` and adds a draft metadata entry to `devto/articles.json`. The script refuses to overwrite an existing article key or article file.

### Import existing dev.to articles

```sh
DEVTO_API_KEY=... python3 scripts/devto_import_articles.py
```

This imports all authenticated user's dev.to articles into `articles/<slug>/article.md` and `devto/articles.json`. Existing local articles are skipped by default. Use `--force` to overwrite existing local files and metadata entries.

### Create a dev.to draft

```sh
DEVTO_API_KEY=... python3 scripts/devto_create_draft.py architecture-vs-simplicity
```

This reads the local Markdown body and metadata, posts a draft to `https://dev.to/api/articles`, and stores the returned `devto_id` in `devto/articles.json`. It refuses to create a second remote article when `devto_id` is already present.

### Update an existing dev.to article

```sh
DEVTO_API_KEY=... python3 scripts/devto_put_article.py architecture-vs-simplicity
```

This requires an existing `devto_id`, reads the local Markdown body and metadata, and sends a `PUT` request to `https://dev.to/api/articles/<devto_id>`.

### Sync changed articles

```sh
DEVTO_API_KEY=... python3 scripts/devto_sync_changed.py articles/foo/article.md articles/bar/article.md
```

For each file, the script looks up the matching entry in `devto/articles.json` by its `source` field. If the entry has a `devto_id`, it sends a `PUT` request to dev.to. Files without a matching metadata entry or without a `devto_id` are reported on stderr and skipped. This is the same script the GitHub Action calls automatically on push to `main`.

### CI setup

Add a `DEVTO_API_KEY` secret to the repository (Settings → Secrets and variables → Actions). The `sync` workflow reads this secret and calls `devto_sync_changed.py` for every `articles/**/*.md` file changed by the push.

All API scripts read the API key from `DEVTO_API_KEY` by default. If the environment variable is not set, they also look for the same key in a gitignored `.env` file in the repository root:

```sh
DEVTO_API_KEY=...
```

Use `--api-key-env` or `--api-base-url` when a different environment variable or API host is needed.

Requests use the Forem v1 media type in the `Accept` header and send the API key through the `api-key` header. Local `cover_image` metadata is translated to the v1 article request field `main_image`.

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

## API version tradeoff

### v0 convenience

- v0 can accept Markdown with frontmatter-style metadata.
- This is convenient because the article body and metadata can be submitted together.
- The risk is coupling the project to behavior that may be older or less future-proof.
- Using JSON metadata means the project does not depend on this v0-specific convenience.

### v1 future-proofness

- v1 appears to prefer explicit API fields instead of relying on frontmatter.
- This is a better long-term boundary: repository Markdown is our authoring format, and API JSON is the transport format.
- The sync tool can build the API payload directly from `devto/articles.json` plus the Markdown body.

### Recommendation

Keep metadata in `devto/articles.json` and build the API payload directly from `devto/articles.json` plus the Markdown body:

1. Load each changed article's body from the Markdown file referenced by `source`.
2. Load that article's metadata from `devto/articles.json`.
3. Keep API-version-specific behaviour isolated behind a small client boundary.

This gives up the convenience of colocated frontmatter, but keeps the project simpler, avoids parsing Markdown metadata, and aligns better with explicit API payloads.

## Tooling approach

The workflow is implemented as small Python scripts using only the Python standard library. Each script does one job, accepts explicit command-line arguments, reads and writes plain files, and prints useful output for shell pipelines.

Principles:

- Use typed Python so the data shapes are clear even without third-party libraries.
- Keep scripts independent and composable instead of building a large framework.
- Use `argparse`, `json`, `pathlib`, `urllib.request`, and other standard-library modules.
- Read the dev.to API key from an environment variable such as `DEVTO_API_KEY`.
- Make CI call the same scripts that can be run locally.
- Fail with non-zero exits and clear stderr messages when validation or API calls fail.

Available scripts:

- `scripts/devto_scaffold.py`: add a new local article entry and create its Markdown file.
- `scripts/devto_import_articles.py`: import existing dev.to articles into local Markdown files and metadata.
- `scripts/devto_create_draft.py`: create a draft article on dev.to for an existing local entry and store the returned `devto_id`.
- `scripts/devto_put_article.py`: update an existing dev.to article from the local Markdown body and JSON metadata.
- `scripts/devto_sync_changed.py`: sync a list of changed article files to dev.to; called by the GitHub Action and usable locally.

This follows the Unix philosophy: simple tools, explicit inputs and outputs, and enough composition to support both local workflows and CI.

## Mapping Markdown files to dev.to articles

The sync tool needs a stable identity that survives file moves and title changes. The JSON object key is that stable identity.

Recommended mapping:

1. Each article entry in `devto/articles.json` has a stable key such as `architecture-vs-simplicity`.
2. The entry stores both `source` and `devto_id`.
3. New articles have an entry with a `source` but no remote ID yet.
4. After creating a new article through the API, the sync tool records the new remote ID in `devto/articles.json`.

Minimal mapping shape:

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
- The remote dev.to ID and editable metadata are kept out of the article body.
- The mapping and metadata can be reviewed in git.
- The sync tool can detect accidental key reuse before publishing.

Path-only mapping is simpler, but it breaks down when files are renamed. Looking up articles remotely by title, slug, or canonical URL is not reliable enough because those values can change and may not be unique.

## Merge-to-main sync flow

1. A pull request changes one or more `articles/**/*.md` files.
2. After the PR is merged, the `sync` GitHub Action on `main` computes the changed Markdown files for the merge using `git diff`.
3. For each changed file, `devto_sync_changed.py`:
   - finds the matching entry in `devto/articles.json` by `source`,
   - reads the Markdown body,
   - validates required metadata from the JSON entry,
   - PUTs the article if a `devto_id` exists,
   - skips the file with an error message if no `devto_id` is present (remote creation is a manual step).
4. The workflow fails loudly if metadata is invalid or an API call fails.

## Local use cases

### Scaffold a new article

Run the scaffold script with a stable article key. It should:

1. create `articles/<key>/article.md`,
2. add a matching entry to `devto/articles.json`,
3. populate required metadata with safe draft defaults,
4. refuse to overwrite an existing article key or file.

### Create the draft online

Run the create-draft script for an article key after local metadata exists. It should:

1. read the article body and metadata,
2. send a create request to dev.to with `published: false`,
3. store the returned `devto_id` in `devto/articles.json`,
4. refuse to create a second remote article if `devto_id` is already present.

### Import existing articles

Run the import script when dev.to already has articles that should become local repository entries. It should:

1. import all authenticated user's articles by default,
2. use the remote article slug as the local key and folder name,
3. skip existing local articles unless `--force` is set.

### PUT an article

Run the PUT script for an article key when the local article should update dev.to. It should:

1. require an existing `devto_id`,
2. read the local body and metadata,
3. send an update request to dev.to,
4. leave `devto/articles.json` unchanged unless sync state needs to change.

## Open design questions

- Should new articles be created as drafts by default even when `published` is `true` in `devto/articles.json`?
- Should asset uploads be handled by the tool, or should image URLs point to raw GitHub-hosted files?
- Should deleted Markdown files ever unpublish dev.to articles, or should remote deletion always be manual?
