# Contributing

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

## Checks

```bash
ruff check . && ruff format --check .
mypy
pytest -m "not integration"
python -m build && twine check dist/*
```

## Workflow

- Work on a descriptive feature branch, never on `main` or `develop`.
- Make small, atomic commits following [Conventional Commits](https://www.conventionalcommits.org/).
- Every endpoint gets a unit test in `tests/unit/` that asserts the request (method, path,
  query, body) and the parsed result. HTTP is mocked with `responses`; sample payloads live
  in `tests/fixtures/`.
- Docstrings are Google style.

## Unverified features

Calls decorated with `@unverified` (`src/sysaid/_unverified.py`) raise
`UnverifiedFeatureError` for library users. The test suite switches that off, so their unit
and integration tests still run. To enable a call, verify it with a live test and remove
the decorator, its entry in `tests/unit/test_unverified.py` and its README row.

## Integration tests

Live tests are marked `integration` and skipped unless these variables are set:

| Variable | Meaning |
|---|---|
| `SYSAID_URL` | Base URL of a **test** instance |
| `SYSAID_USERNAME` / `SYSAID_PASSWORD` | Administrator with mobile-app permission |
| `SYSAID_ACCOUNT_ID` | Optional account id |
| `SYSAID_ALLOW_WRITES=1` | Also run tests marked `destructive` (create/update/delete) |

```bash
pytest -m integration
SYSAID_ALLOW_WRITES=1 pytest -m "integration and destructive"
```

Never point them at a production instance.
