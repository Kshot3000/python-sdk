# Publication Runbook

This runbook covers every step from a clean repository to a published PyPI release.

Repository:

- GitHub: `https://github.com/octaspace/python-sdk`
- SSH remote: `git@github.com:octaspace/python-sdk.git`

## Prerequisites

- A working virtualenv at `.venv/` with dev dependencies installed (see `README.md#local-development-setup`)
- `twine` and `build` available in the venv:
  ```bash
  .venv/bin/pip install twine build
  ```
- PyPI account at https://pypi.org with 2FA enabled
- TestPyPI account at https://test.pypi.org with 2FA enabled
- API tokens created at both registries (instructions in Step 0 below)
- GitHub repository created at `octaspace/python-sdk`

Initial repository push:

```bash
git remote add origin git@github.com:octaspace/python-sdk.git
git branch -M main
git push -u origin main
```

---

## Step 0 — Create API Tokens

You need tokens for both TestPyPI and PyPI. Do this once before the first upload.

**TestPyPI token:**

1. Log in at https://test.pypi.org
2. Go to Account Settings → API tokens → Add API token
3. Name: `python-sdk` (or any name you like)
4. Scope: `Entire account` (for the first upload; switch to project-scoped after the project exists)
5. Copy the token — it starts with `pypi-` and is shown only once

**PyPI token:**

1. Log in at https://pypi.org
2. Same flow: Account Settings → API tokens → Add API token
3. Name: `python-sdk`
4. Scope: `Entire account` (switch to project-scoped after first upload)
5. Copy the token

**Store tokens in `~/.pypirc`** (create the file if it does not exist):

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-<your-pypi-token>

[testpypi]
username = __token__
password = pypi-<your-testpypi-token>
```

Set restrictive permissions on the file:

```bash
chmod 600 ~/.pypirc
```

After the first successful upload you can go back to PyPI/TestPyPI, delete the account-scoped tokens, and create new project-scoped tokens for `octaspace`. Update `~/.pypirc` with the new tokens.

---

## Step 1 — Quality Gate

All checks must be green before building anything.

```bash
.venv/bin/ruff check src tests examples playground
.venv/bin/mypy src/octaspace playground
.venv/bin/pytest
```

Expected outcome:

- ruff: `All checks passed!`
- mypy: `Success: no issues found in N source files`
- pytest: all tests passing, 0 failed

If any check fails, fix it before proceeding.

---

## Step 2 — Verify Version

Open `src/octaspace/__about__.py` and confirm the version matches the intended release:

```python
__version__ = "0.1.0"
```

Version scheme: `MAJOR.MINOR.PATCH` (SemVer).

Bump rules:

| Change type | Example | Bump |
| --- | --- | --- |
| Backwards-compatible fixes | bug fix, doc update | PATCH |
| New backwards-compatible features | new resource method | MINOR |
| Breaking API changes | rename method, remove param | MAJOR |

Also update `CHANGELOG.md`: add a section `## [X.Y.Z] - YYYY-MM-DD` with a short summary of changes.

---

## Step 3 — Build

Delete any stale artifacts and build fresh:

```bash
rm -rf dist/
.venv/bin/python -m build
```

Expected output:

```
Successfully built octaspace-X.Y.Z.tar.gz and octaspace-X.Y.Z-py3-none-any.whl
```

Verify the wheel contains only the SDK package (no `playground/`, no `tests/`):

```bash
python3 -m zipfile -l dist/octaspace-*.whl
```

Every file entry must start with `octaspace/` or `octaspace-*.dist-info/`. If `playground/` or `tests/` appear, check `[tool.hatch.build.targets.wheel]` in `pyproject.toml`.

Check the `py.typed` marker is present (required for PEP 561 typed packages):

```bash
python3 -m zipfile -l dist/octaspace-*.whl | grep py.typed
```

---

## Step 4 — Wheel Smoke Test

Install the wheel in a clean throwaway environment and verify the public API works without any dev dependencies:

```bash
python3 -m venv /tmp/octaspace-wheel-test
/tmp/octaspace-wheel-test/bin/python -m pip install dist/octaspace-*.whl

/tmp/octaspace-wheel-test/bin/python - <<'EOF'
from octaspace import OctaSpaceClient, __version__
print("version:", __version__)
with OctaSpaceClient() as client:
    data = client.network.info().data
    print("network.info:", type(data))
print("smoke: ok")
EOF
```

Expected:

```
version: X.Y.Z
network.info: <class 'dict'>
smoke: ok
```

Also verify that `playground` is not importable from the wheel:

```bash
/tmp/octaspace-wheel-test/bin/python -c "import playground" 2>&1 | grep -q "No module named" && echo "playground not in wheel: ok"
```

Cleanup:

```bash
rm -rf /tmp/octaspace-wheel-test
```

---

## Step 5 — TestPyPI

Upload to TestPyPI first. This catches metadata problems without affecting real users.

```bash
.venv/bin/twine upload --repository testpypi dist/*
```

If `~/.pypirc` is configured (see Step 0), no credentials prompt appears.

After upload, open the release page on TestPyPI and confirm:

- version matches
- description (README) renders correctly
- classifiers and links are present

Install from TestPyPI and smoke test:

```bash
python3 -m venv /tmp/octaspace-testpypi
/tmp/octaspace-testpypi/bin/python -m pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    octaspace

/tmp/octaspace-testpypi/bin/python -c "
from octaspace import OctaSpaceClient, __version__
print('installed version:', __version__)
print('network.info:', OctaSpaceClient().network.info().data)
"

rm -rf /tmp/octaspace-testpypi
```

`--extra-index-url https://pypi.org/simple/` is required because `httpx` (the only runtime dependency) is on real PyPI, not TestPyPI.

---

## Step 6 — Push To GitHub And Tag

Commit the release and push to GitHub:

```bash
git add -p
git commit -m "Release 0.1.0"
git push origin main
```

Wait for CI to pass at `https://github.com/octaspace/python-sdk/actions`.

Create and push the release tag:

```bash
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

Optionally create a GitHub release for the tag (UI or CLI):

```bash
gh release create v0.1.0 --title "v0.1.0" --notes "Initial public release."
```

---

## Step 7 — Publish To PyPI

Upload the same artifacts (already built in Step 3) directly to real PyPI:

```bash
.venv/bin/twine upload dist/*
```

If `~/.pypirc` is configured, no credentials prompt appears.

After upload, verify the release page at https://pypi.org/project/octaspace/.

Final install check from real PyPI:

```bash
python3 -m venv /tmp/octaspace-final
/tmp/octaspace-final/bin/python -m pip install octaspace
/tmp/octaspace-final/bin/python -c "from octaspace import OctaSpaceClient; print(OctaSpaceClient().network.info().data)"
rm -rf /tmp/octaspace-final
```

---

## Step 8 — Post-Release

After a successful PyPI upload:

1. **Bump the dev version** in `src/octaspace/__about__.py` to the next development marker, e.g.:

   ```python
   __version__ = "0.2.0.dev0"
   ```

   This ensures any builds from `main` after the release are clearly distinguishable from the published version.

2. **Push the post-release bump**:

   ```bash
   git commit -am "Start 0.2.0 development"
   git push origin main
   ```

3. **Rotate tokens** (optional but recommended): go back to PyPI and TestPyPI, delete the account-scoped tokens created in Step 0, and create new project-scoped tokens for `octaspace`. Update `~/.pypirc`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `403 Forbidden` on upload | Wrong token or scope | Re-check `~/.pypirc`; create a new token at pypi.org/manage/account/token/ |
| `File already exists` on upload | Re-uploading the same version | Bump the version — PyPI does not allow replacing existing files |
| `playground` appears in wheel | `packages` in `pyproject.toml` too broad | Confirm `packages = ["src/octaspace"]` under `[tool.hatch.build.targets.wheel]` |
| README renders as raw text on PyPI | Wrong or missing `readme = "README.md"` | Confirm the `[project]` table in `pyproject.toml` has `readme = "README.md"` |
| Dependency resolution fails | Pinned dep conflicts with user environment | Widen `httpx` version range in `dependencies` |

---

## Quick Reference

```bash
# Full quality gate
.venv/bin/ruff check src tests examples playground && \
.venv/bin/mypy src/octaspace playground && \
.venv/bin/pytest && \
echo "gate: ok"

# Build
rm -rf dist/
.venv/bin/python -m build

# TestPyPI
.venv/bin/twine upload --repository testpypi dist/*

# Push + tag
git push origin main
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin vX.Y.Z

# Publish to real PyPI
.venv/bin/twine upload dist/*
```
