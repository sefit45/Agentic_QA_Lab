# Step 01 Source preparation

Status: Offline foundation; not an AI agent or live integration.

Copy the archive's contents into C:\Users\sefit\Agentic_QA_Lab.
Do not replace your existing .gitignore or __init__.py files.
The archive adds five new files and requires no package installation.
If any destination file already exists, compare it before replacing it.

From the project root, with your existing virtual environment active:

```powershell
python -m unittest discover -s tests -p "test_source_loader.py" -v
python src\agentic_qa\source_loader.py --output outputs\source_context.json
git status --short --untracked-files=all
```

Add `outputs/` on a separate line to the existing .gitignore before
staging files. Generated context can contain sensitive source content
when live integrations are introduced. This exercise only accepts
synthetic fixtures and makes no network requests.

Expected: 10 passing unit tests, 10 normalized requirements and 3
Confluence sections. This proves structure and provenance preservation,
not semantic correctness, telecom integration or AI capability.

## Why JSON instead of Markdown here

JSON represents structured input records. These are our fixture contracts,
not the exact REST payloads of Jira or Confluence. Live adapters will map
their environment-specific fields into this contract. Files with .md
remain documentation. Neither file format is an agent.

## What the Python code does

- `load_object`: read UTF-8 JSON; reject invalid files and non-object roots.
- `required_text`: require non-empty text values.
- `provenance`: validate source metadata and preserve identifiers,
  URL, version, timestamp and a precise fixture locator.
- `normalize_sources`: verify the issue-to-page link, reject duplicate
  IDs and keep requirements separate from supporting context.
- `main`: parse command-line arguments and write a normalized JSON file.

The CLI locates its fixtures relative to its code, not a hard-coded
Windows user directory. The explicit --output path is relative to the
working directory. Running from the project root keeps outputs together.

## Important limits

- No LLM, RAG, embeddings, orchestration, SQL or external calls yet.
- No automatic conflict detection or semantic validation.
- Source text stays untrusted. A warning alone is not injection protection.
- Source URLs are metadata only and are never fetched.
- The synthetic billing rules are lab choices, not operator specifications.
- Actual Amdocs table fields and joins remain unknown.
- Credentials, write operations and arbitrary SQL are not implemented.

Next: define structured AI Test Architect output, then connect one model.
