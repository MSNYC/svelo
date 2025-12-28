# AGENTS

This repo contains `svelo`, a lightweight CLI that tries common decoders on an input string.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

Run:

```bash
svelo "SGVsbG8gV29ybGQh"
```

List decoders:

```bash
svelo --list
```

## Development notes

- Source lives in `src/svelo`.
- Entry point is `svelo.cli:main`.
- Keep dependencies stdlib-only unless a strong need arises.
- Run tests with the venv's explicit pytest path: `./.venv/bin/pytest`.
