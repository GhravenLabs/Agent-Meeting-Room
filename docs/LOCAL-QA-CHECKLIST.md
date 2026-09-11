# Local QA Checklist

Run this checklist before publishing visible Agent Meeting Room changes.

## Setup

- Create or update `.env` from `.env.example`.
- Confirm no secrets are staged.
- Confirm the default local models are realistic for modest hardware.

## App behavior

- Home page loads without a server error.
- Mention routing responds only for selected agents.
- Debate mode returns a structured multi-round response.
- Transcript export produces Markdown.
- Memory save/search paths handle missing optional backends gracefully.

## Verification

```bash
python -m pytest
git diff --check
```

For UI-only edits, capture a browser smoke check and mention what was inspected in the commit or pull-request notes.

