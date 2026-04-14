# Console Verification Runbook

This runbook is for a new developer joining the repository and needing a deterministic way to verify the SDK from the console before thinking about browser QA, release work, or any push.

## Goal

Verify that:

- the package installs locally
- public and authenticated resource calls behave as expected
- transport diagnostics are visible
- mock mode and real API mode are both reproducible
- token handling is safe and explicit

## Prerequisites

- Python `3.10+`
- repository root opened at `python-sdk`
- a local virtualenv

Setup:

```bash
uv sync --group dev
```

If you prefer a plain `venv` + `pip` flow instead:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e . pytest pytest-cov respx mypy ruff hatchling fastapi jinja2 python-multipart uvicorn
```

Mandatory automated checks before manual console verification:

```bash
.venv/bin/python -m ruff check src tests examples playground
.venv/bin/python -m mypy src playground
.venv/bin/python -m pytest
```

## Token Safety

Do not paste tokens into committed files, screenshots, shell history, or example scripts.

Recommended for `zsh` / `bash`:

```bash
read -s OCTA_API_KEY
export OCTA_API_KEY
```

`read -s OCTA_API_KEY` waits for you to type the token without echoing it on screen. `export OCTA_API_KEY` makes that value visible to processes launched from the current shell, including `.venv/bin/python`.

After finishing:

```bash
unset OCTA_API_KEY OCTA_SESSION_UUID OCTA_ALLOW_STOP
```

Rules:

- prefer environment variables over inline command arguments
- do not save tokens in `.env` unless team policy explicitly allows it
- do not capture console screenshots with live tokens visible
- do not run destructive session commands unless you intentionally target a disposable session

## Scenario A: Mocked Console Verification

This is the fastest deterministic check and must work without any network access to the OctaSpace API.

Command:

```bash
.venv/bin/python examples/console_mock.py
```

What it verifies:

- SDK import path
- `MockTransport`
- resource calls for public and authenticated-style flows
- typed response access
- session proxy flow
- transport diagnostics in mock mode

Expected output should include:

- `transport_stats`
- `network`
- `profile`
- `balance`
- `nodes`
- `session_info`
- `session_stop`

If this script fails:

1. rerun `pytest`
2. inspect changed SDK modules
3. inspect any recent payload-shape changes

## Scenario B: Public Real API Verification

This verifies that the client can talk to the live API without requiring authentication for public endpoints.

Command:

```bash
.venv/bin/python -m octaspace
.venv/bin/octaspace-smoke
```

What it verifies:

- `ClientConfig.from_env()`
- default client startup
- live `network.info()`
- JSON output formatting for smoke mode

Expected result:

- printed JSON payload from `/network`

## Scenario C: Authenticated Real API Verification

Set the token first:

```bash
read -s OCTA_API_KEY
export OCTA_API_KEY
```

These two lines must be run in the shell before starting Python. They are not valid inside Python REPL.

Run:

```bash
.venv/bin/python examples/console_real.py
```

What it verifies:

- authenticated client startup
- `accounts.profile()`
- `accounts.balance()`
- `nodes.list()`
- `sessions.list()`
- transport diagnostics in real mode

Expected output should include:

- `transport_stats`
- `network`
- `profile`
- `balance`
- `nodes_count`
- `sessions_count`

If the token is missing, the script should still show public endpoint output and explicitly state that authenticated checks were skipped.

## Scenario D: Targeted Session Inspection With Real Data

If you have a known safe session UUID:

```bash
export OCTA_SESSION_UUID="session-uuid-here"
.venv/bin/python examples/console_real.py
```

Expected additional output:

- `session_info`
- `session_logs_preview`

This should remain read-only.

## Scenario E: Explicit Stop Command Against a Disposable Session

Only use this for an intentionally disposable session.

```bash
export OCTA_SESSION_UUID="session-uuid-here"
export OCTA_ALLOW_STOP=1
.venv/bin/python examples/console_real.py
```

Expected additional output:

- `session_stop`

Safety rule:

- never set `OCTA_ALLOW_STOP=1` against a production or user-critical session

## Suggested REPL Checks

For exploratory debugging:

```bash
.venv/bin/python
```

```python
import os
from octaspace import OctaSpaceClient

client = OctaSpaceClient(api_key=os.getenv("OCTA_API_KEY"), keep_alive=True, pool_size=10)
print(client.transport_stats())
print(client.network.info().data)
print(client.accounts.profile().data)
client.close()
```

If you are already inside Python REPL and forgot to export the token in the shell, set it in-process instead:

```python
import os, getpass
os.environ["OCTA_API_KEY"] = getpass.getpass("OCTA_API_KEY: ")
```

## Troubleshooting

### `ModuleNotFoundError`

The editable install was not done in the active virtualenv.

Fix:

```bash
.venv/bin/python -m pip install -e .
```

### `AuthenticationError`

- token is missing
- token is invalid
- wrong shell session exported the variable
- `read -s` / `export` was entered inside Python REPL instead of the shell

Check:

```bash
python3 - <<'PY'
import os
print("present" if os.getenv("OCTA_API_KEY") else "missing")
PY
```

### `APIConnectionError` / `APITimeoutError`

- temporary live API/network issue
- bad `base_url` / `base_urls`
- TLS verification problem in a custom environment

Check the current config and transport stats before changing code.

## Completion Criteria

Manual console verification is complete only when:

1. mock scenario passes
2. public real API scenario passes
3. authenticated real API scenario passes when a valid token is available
4. optional session inspection behaves as documented
5. browser playground runbook is ready to execute next
6. all automated checks remain green afterward
