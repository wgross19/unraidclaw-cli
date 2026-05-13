# AGENTS.md — UnraidClaw CLI

Python command-line interface for the UnraidClaw API gateway.

- **This repo:** `https://github.com/wgross19/unraidclaw-cli`
- **Upstream API dep:** [UnraidClaw plugin](https://github.com/emaspa/unraidclaw) (Unraid 7.0+, port 9876)

## Project identity

- **Package:** `unraidclaw`
- **Entry point:** `unraidclaw.__main__:main`
- **Python:** ≥3.10
- **Dependencies:** zero. Stdlib only (`urllib`, `ssl`, `json`, `argparse`). No `requests`, no `click`, no `httpx`.

## Layout

```
/artifacts/repos/unraidclaw-cli/
├── pyproject.toml           # flit build, project metadata
├── README.md                # user-facing reference
├── AGENTS.md                # this file
└── unraidclaw/
    ├── __init__.py          # __version__
    ├── client.py            # REST client for UnraidClaw API
    ├── output.py            # table + JSON formatting
    └── __main__.py          # argparse CLI with all subcommands
```

## How to run (without pip install)

```bash
cd /artifacts/repos/unraidclaw-cli
PYTHONPATH=. python3 -m unraidclaw <command>
```

## How to install

```bash
# Direct from GitHub (recommended)
pip install git+https://github.com/wgross19/unraidclaw-cli.git

# Or clone and install locally
git clone https://github.com/wgross19/unraidclaw-cli.git
cd unraidclaw-cli
pip install -e .
# Then: unraidclaw health
```

## Environment config

```bash
UNRAIDCLAW_URL=https://tower:9876
UNRAIDCLAW_KEY=your-api-key
UNRAIDCLAW_TLS_SKIP=1        # "1", "true", or "yes" to skip TLS verify
```

## Conventions

- **No external deps.** If a feature can't be done with stdlib, it doesn't go in. The CLI is designed to work on bare Unraid systems and minimal Python environments.
- **Commands match API routes 1:1.** Each UnraidClaw API endpoint maps to a subcommand. Route tree is in `__main__.py` organized by resource category.
- **Output defaults to table.** `--output json` for machine-readable. Tables are auto-aligned for lists of dicts.
- **Destructive commands require confirmation.** `system reboot`, `system shutdown` require `--yes`. `docker rm` requires `--force` to force-kill.
- **API envelope is transparent.** `client.py` unwraps `{ok: true, data: ...}` and surfaces `{ok: false, error: ...}` as `UnraidAPIError`.
- **Config override order:** CLI flags (`--url`, `--key`, `--tls-skip`) > environment variables. Both are checked at request time, not parse time.

## Upstream API

The API is defined by UnraidClaw's Fastify server (`emaspa/unraidclaw`, `packages/unraid-plugin/server/src/routes/`). This CLI targets the REST surface, not the OpenClaw plugin tools. When the upstream API changes, update `client.py` paths and `__main__.py` subcommands.

## Testing against a live server

Set the env vars, then:

```bash
unraidclaw health
unraidclaw docker list
unraidclaw array status
```

No test suite exists yet — smoke against a real UnraidClaw instance.

## Memory

- The upstream UnraidClaw monorepo clone is at `/artifacts/repos/unraidclaw-cli` but this directory IS the CLI project, not the monorepo. The monorepo source was read for API reference during CLI generation and should not be edited here.
- Do not add `node_modules`, TypeScript, or the Unraid plugin code to this repo. It is Python-only.
