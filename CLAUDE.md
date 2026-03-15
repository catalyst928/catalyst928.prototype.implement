# CLAUDE.md

## Project Overview

This file defines how Claude Code should behave in this project, including how to interpret
annotation tags in spec files.

---

## Spec Annotation System

When working with Markdown files in the `openspec/` directory, recognize and act on the following
HTML comment tags. After processing, **remove all handled annotation tags** from the file.
**Never modify content that has no annotation tags.**

### Annotation Tag Reference

| Tag | Action |
|-----|--------|
| `@claude: <instruction>` | Execute the instruction at that location |
| `@revise: <requirement>` | Rewrite the adjacent paragraph to meet the requirement |
| `@expand: <direction>` | Expand and elaborate on the adjacent content |
| `@delete` | Remove the annotated content block entirely |
| `@todo` | Mark as incomplete — ask me how to fill it in before proceeding |
| `@discuss: <question>` | Pause and analyze the question, present options before editing |
| `@keep` | Do not modify this content under any circumstance |
| `@note: <remark>` | Informational only — do not trigger any modification, preserve the comment |

### Tag Usage Examples

```markdown
<!-- @claude: Generate a TypeScript interface based on the fields described below -->
User object contains: id, name, email, created_at, role

<!-- @revise: Rewrite in technical language targeting backend engineers -->
The sync feature copies files from repo1 to repo2.

<!-- @expand: Add details about exclude rule configuration options -->
The tool supports excluding specific directories.

<!-- @delete -->
This section is outdated and should be removed.

<!-- @todo -->
Authentication flow details go here.

<!-- @discuss: Should we use REST or GraphQL for this endpoint? -->

<!-- @note: This section was reviewed on 2025-01-01, no changes needed -->
System supports both MySQL and PostgreSQL.

Some important constraint that must never change. <!-- @keep -->
```

### Processing Rules

1. Process all annotation tags in a single pass unless a `@discuss` or `@todo` tag is encountered.
2. On `@discuss` — stop, present analysis and options, wait for confirmation before editing.
3. On `@todo` — stop, ask how the section should be filled in, then proceed after response.
4. After processing, delete all handled tags (`@claude`, `@revise`, `@expand`, `@delete`).
5. Always preserve `@note` comments and `@keep` tags — never remove them.
6. Never touch content outside the scope of an annotation tag.

