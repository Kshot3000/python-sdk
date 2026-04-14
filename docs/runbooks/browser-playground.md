# Browser Playground Runbook

This runbook is the browser-side QA companion to the console runbook. Use it only after lint, typecheck, tests, and console verification are already green.

## Goal

Verify that:

- the browser playground starts locally
- the page set and navigation match the Ruby dummy app closely
- fixture-backed mock QA works without live API access
- failure scenarios are visible and readable in the browser
- live mode works for public and authenticated endpoints
- diagnostics and the footer request log remain useful during manual testing

## Prerequisites

- repository root opened at `python-sdk`
- development dependencies installed
- automated checks already green

Recommended setup:

```bash
# With uv:
uv sync --group dev

# Or with pip + existing venv:
.venv/bin/python -m pip install -e ".[dev]" 2>/dev/null || \
  .venv/bin/python -m pip install -e . fastapi jinja2 python-multipart uvicorn pytest pytest-cov respx mypy ruff
```

Mandatory automated checks before browser QA:

```bash
.venv/bin/ruff check src tests examples playground
.venv/bin/mypy src/octaspace playground
.venv/bin/pytest
```

## Start The Playground

The playground lives in the repository root under `playground/`. It is a development tool and is **not** shipped in the PyPI wheel.

Start it from the repository root:

```bash
.venv/bin/uvicorn playground.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/playground/dashboard
```

## Token Safety

- paste tokens only into the local sidebar field when needed
- do not commit tokens, screenshots, or copied payloads with live secrets
- prefer disposable resources for any live mutation check
- clear the token field or close the browser when verification is finished

If you want the token ready in the shell first:

```bash
read -s OCTA_API_KEY
export OCTA_API_KEY
```

## Expected Page Set

The playground should expose the same core page set as the Ruby dummy app:

- `Dashboard`
- `Network`
- `Apps`
- `Nodes`
- `Sessions`
- `Services`
- `Idle Jobs`
- `Diagnostics`

Additional note:

- `/playground/account` exists and must work, but it is intentionally not present in the sidebar because the Ruby dummy app also omits it from navigation

## Scenario A: Fixtures Mode

The default state is `Real API`. For deterministic offline QA, switch `Transport` to `Fixtures` in the sidebar first.

Checklist:

1. Open `Dashboard`.
2. Confirm the mock badge shows `Fixtures`.
3. Confirm `Network`, `Account`, and `Balance` panels render payloads.
4. Open `Network` and confirm the transport/config panels render.
5. Open `Apps`, `Nodes`, `Sessions`, `Services`, and `Idle Jobs`.
6. Confirm all of them render fixture-backed payloads without live API access.

What this verifies:

- template rendering
- sidebar settings wiring
- fixture-backed SDK calls
- footer request logging
- route coverage for the full dummy-style page set

## Scenario B: Failure Scenarios

Cycle the sidebar `Transport` through:

- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `429 Rate Limited`
- `500 Server Error`
- `Slow (3s)`
- `Timeout`
- `Network Error`

Recommended checks:

1. In each scenario, open `Diagnostics`.
2. Run `octa_client.network.info` or another simple call.
3. Confirm the UI renders a readable error card instead of crashing.
4. Confirm the footer request log shows status or `ERR` with a duration.

What this verifies:

- typed error display
- timeout / connection handling
- readable failure UX for manual QA

## Scenario C: Live Public Verification

Switch `Transport` back to `Real API` and leave the API key empty.

Checklist:

1. Open `Dashboard`.
2. Confirm `Network` still renders.
3. Confirm authenticated panels show the locked state instead of crashing.
4. Open `Network` directly and confirm the response is live.

What this verifies:

- real transport startup
- public endpoint availability
- auth-gated UI behaviour

## Scenario D: Live Authenticated Verification

Enter a valid token in the sidebar.

Recommended checklist:

1. `Dashboard`: confirm `Account` and `Balance` now load.
2. `Account`: confirm profile and balance both render.
3. `Apps`: confirm app list renders.
4. `Nodes`: confirm list renders and detail panel opens.
5. `Sessions`: confirm current and recent tabs work.
6. `Services`: confirm MR, Render, and VPN tabs load.
7. `Idle Jobs`: test a known sample `node_id` / `job_id` if you have them.

What this verifies:

- authenticated transport flow
- multi-page parity with the Ruby dummy app
- repeated request behaviour with the real SDK transport

## Scenario E: Diagnostics And Smoke

Open `Diagnostics`.

Checklist:

1. Run one public call such as `octa_client.network.info`.
2. Run one authenticated read call such as `octa_client.accounts.profile`.
3. Run one payload-based call such as `octa_client.idle_jobs.find(node_id:, job_id:)`.
4. Run `Run SDK Smoke`.
5. Confirm the result panel and footer request log update after each run.

Important:

- diagnostics includes mutation-capable methods such as `services.mr.create`, `services.render.create`, `services.vpn.create`, and `services.session(uuid).stop`
- there is no separate mutation-guard toggle in the current UI
- in live mode, only run those calls against disposable targets and only when the team explicitly wants that check

## Scenario F: Footer Request Log

The request log is part of the shared page footer, matching the Ruby dummy layout style. It is not a standalone page.

Checklist:

1. Trigger several calls across different pages.
2. Confirm the footer log records method, path, status, duration, and time.
3. Use `Clear`.
4. Confirm the footer resets to `No requests yet`.

## Completion Criteria

Browser playground verification is complete only when:

1. the expected page set is present
2. fixtures mode works
3. failure scenarios render cleanly
4. live public verification works
5. live authenticated verification works when a valid token is available
6. diagnostics and smoke run correctly
7. footer request logging remains readable and resettable
8. automated checks are still green afterward
