# python-sysaid — Implementation Plan

A Python wrapper for the SysAid REST API (`/api/v1`), to be published on PyPI.
Endpoint reference: [ANOTATIONS.md](ANOTATIONS.md) (61 endpoints, 12 resource areas, SysAid 15.4+).

Status: **phases 0–8 implemented (PRs open, merge in order); phases 9–10 pending.**

| Phase | State | PR |
|---|---|---|
| 0 Scaffolding | Done | #1 |
| 1 Core client | Done | #2 |
| 2 Users, filters, lists | Done | #3 |
| 3 Service requests | Done | #4 |
| 4 Action items, assets | Done | #5 |
| 5 CIs | Done | #6 |
| 6 Add-ons, RB, password services, reports | Done | #7 |
| 7 OAuth 1.0 | Done (unverified without a consumer key) | #8 |
| 8 Documentation | Done | #9 |
| 9 Live validation | **Pending** — needs the homologation instance | — |
| 10 Release | **Pending** — after phase 9 | — |

**Pending before 0.1.0**
- The mocked unit suite (95 tests) is written but has **never been executed**; the gate so far
  is compile + lint + type-check + `pytest --collect-only` + build. Run it first (Phase 9, step 1).
- Run read-only, then destructive, integration tests against homologation; settle every row of
  the doc-gap table (§5) and replace doc-sample fixtures with sanitized real payloads.
- Enable the disabled `test` job in `.github/workflows/ci.yml`.
- Confirm the MIT license and copyright holder (A8) and the PyPI name `python-sysaid` (A1).
- Decide whether OAuth (Phase 7) ships in 0.1.0.
- Release: `release.yml` with Trusted Publishing, TestPyPI dry run, tag `v0.1.0`.

---

## 1. Assumptions (veto any of these before Phase 0)

| # | Decision | Default chosen | Why |
|---|---|---|---|
| A1 | Distribution / import name | `python-sysaid` / `import sysaid` | Matches the repo; same convention as `python-gitlab`. PyPI availability must be checked before the first release. |
| A2 | Python support | 3.10+ | All currently supported CPython versions; allows `X \| Y` typing. |
| A3 | HTTP library | `requests` | Sync, cookie-session friendly, de-facto standard for wrappers of this kind. |
| A4 | Sync vs async | Sync only | Nothing asks for async; adding it later doubles the surface. |
| A5 | Models | Small stdlib `dataclass`es, no pydantic | SysAid fields are dynamic (`info[]` key/value); strict schemas would fight the API. |
| A6 | OAuth 1.0 | Optional extra `python-sysaid[oauth]` using `requests-oauthlib` | Session login is the main path; consumer-key creation is undocumented. |
| A7 | Build / tooling | `hatchling`, `src/` layout, `ruff` (lint + format), `mypy --strict`, `pytest` + `responses` | Current defaults for typed PyPI libraries. |
| A8 | License | MIT | No LICENSE file exists yet — **needs your confirmation**. |
| A9 | CI | GitHub Actions: lint, type-check, test matrix 3.10–3.13 | Repo is on GitHub. |
| A10 | Versioning | SemVer, starting at `0.1.0`; `CHANGELOG.md` in Keep a Changelog format | Standard. |

Out of scope: async client, CLI, caching, automatic retries, endpoints not in ANOTATIONS.md.

---

## 2. Target design

### 2.1 Public API

```python
from sysaid import SysAid

with SysAid("https://host", username="sysaid", password="...") as client:
    sr = client.service_requests.get(273, fields=["title", "status"])
    sr["title"]                      # raw value
    sr.caption("status")             # display value

    for sr in client.service_requests.iter(type="incident", status=[4, 5]):
        ...                          # transparent offset/limit pagination

    client.service_requests.update(273, status=2, responsibility=66)
    client.service_requests.close(273, solution="restarted")
```

### 2.2 Package layout

```
src/sysaid/
  __init__.py            # SysAid, exceptions, __version__
  py.typed
  client.py              # SysAid: session, base URL, request(), login/logout, resource attributes
  auth.py                # session-cookie login; OAuth1 helper (optional extra)
  exceptions.py          # SysAidError > SysAidHTTPError > Auth / NotFound / BadRequest ...
  models.py              # Record (id + info[] accessors), Field, small typed results
  _params.py             # list->CSV, bool->"true"/"false", datetime->ms, date ranges, filters
  resources/
    _base.py             # Resource base: holds client, shared list/iter/get helpers
    users.py  filters.py  lists.py
    service_requests.py  action_items.py  assets.py  cis.py
    addons.py  resource_bundle.py  password_services.py  reports.py
tests/
  conftest.py            # client fixture, `responses` mock, JSON fixture loader
  fixtures/              # sample payloads taken from ANOTATIONS.md
  unit/                  # one test module per source module (mocked HTTP)
  integration/           # live tests, skipped unless env vars are set
```

### 2.3 Cross-cutting rules

- **One request path.** Every resource goes through `SysAid.request()`: URL building, param encoding, error mapping, JSON decoding.
- **`Record`** wraps `{id, info[]}`: `record["key"]` → `value`, `record.caption("key")` → `valueCaption`, `record.raw` → original dict. Accepts both `keyCaption` and `key_caption` (doc gap #16).
- **Writes** take `**fields` and build `info: [{key, value}]`; `datetime` values become ms-epoch UTC.
- **Pagination:** `list()` returns one page; `iter()` yields across pages until a page is shorter than `limit`.
- **Filters** are passed as extra keyword arguments; sequences become comma-separated; `(from, to)` tuples of datetimes become ms ranges (`0` for an open end).
- **Errors:** non-2xx → typed exception carrying `status_code`, `message` (parsed from `{"status","message"}` when present), and the response.
- **No secrets in logs or `repr`.**

---

## 3. Testing strategy

| Layer | Tooling | When it runs |
|---|---|---|
| Unit | `pytest` + `responses` (mocked HTTP), fixtures from the doc samples | Written in every phase, **not executed until you approve** (Phase 9). |
| Integration | `pytest -m integration` against the homologation instance; configured by `SYSAID_URL`, `SYSAID_USERNAME`, `SYSAID_PASSWORD`, `SYSAID_ACCOUNT_ID` | Phase 9 only. Auto-skipped when the variables are missing. |
| Destructive integration | Extra marker `destructive`, needs `SYSAID_ALLOW_WRITES=1` | Phase 9, opt-in. Covers create/update/delete SR, messages, add-on updates, CI relations, password services. |

Each unit test asserts the **request** (method, path, query, body) and the **parsed result**, so the tests stay meaningful without a server.

### "It compiles" gate — required at the end of every phase

No test is executed; everything is still imported, parsed and type-checked:

```bash
python -m compileall -q src tests      # byte-compiles all sources
ruff check . && ruff format --check .  # lint + format
mypy src tests                         # strict type check
pytest --collect-only -q               # imports every test module without running tests
python -m build && twine check dist/*  # package builds (Phase 0 onwards)
```

---

## 4. Phases

Each phase = one feature branch off `develop` (`feat/<phase-topic>`), many small Conventional Commits, merged by PR. Tests are written in the same phase as the code they cover.

### Phase 0 — Project scaffolding
Branch: `chore/project-scaffolding`

- `pyproject.toml` (metadata, deps, extras `oauth` / `dev`, ruff, mypy, pytest markers), `src/sysaid/__init__.py`, `py.typed`
- `.gitignore`, `LICENSE`, `README.md` skeleton, `CHANGELOG.md`
- `.github/workflows/ci.yml` (lint, type-check, build; test job added but disabled until Phase 9)
- `tests/conftest.py` with the integration-skip logic and markers

Done when: gate passes; `pip install -e ".[dev]"` works; `import sysaid` works.

### Phase 1 — Core client
Branch: `feat/core-client`

- `exceptions.py`, `_params.py`, `models.py` (`Record`, `Field`)
- `client.py`: `SysAid(base_url, username=, password=, account_id=, timeout=, verify=, session=)`, `request()`, context manager
- `auth.py`: `POST /login` (JSON body — doc gap #1), `JSESSIONID` kept by the `requests.Session`; `LoginResult` model
- `resources/_base.py`: shared `_list` / `_iter` / `_get`

Tests: param encoding (CSV, bools, date ranges), `Record` accessors (both caption spellings), error mapping, login success/failure, pagination stop condition.

### Phase 2 — Read-only reference data
Branch: `feat/users-filters-lists`

- **Users** (7): list, get, search, get/upload photo, permissions, single permission
- **Filters** (2): list, get
- **Lists** (2): list, get (`entity`, `entityId`, `entityType`, `key`)

These come first because SRs, CIs and action items depend on their ids. Photo upload validates the 500 KB limit client-side.

### Phase 3 — Service Requests
Branch: `feat/service-requests` (largest area — 16 endpoints, split into three PRs if it grows)

1. Read: list, iter, get, search, count, template
2. Write: create, update, close, delete
3. Sub-resources: links, attachments, activities, send message (multipart with JSON `message` part)

Helpers for the special fields: `notes` (list of `{userName, createDate, text}`), `due_date`, `problem_type` (`"A_B_C"` from up to three category levels).

### Phase 4 — Action Items and Assets
Branch: `feat/action-items-assets`

- **Action items** (6): list, count, approve, reject, complete, reopen
- **Assets** (3): list, get, search — ids containing `:` are URL-encoded

### Phase 5 — CIs
Branch: `feat/cis`

- (8): list, update, types, view fields, relation types, get/create/delete relations
- `DELETE` with a JSON body; a 400 on create-relations surfaces the per-item failure message

### Phase 6 — Add-ons, Resource Bundle, Password Services, Reports
Branch: `feat/admin-resources`

- **Add-ons** (5): list, get, update, test connection, refresh — note `/addons` vs `/addon` (doc gap #6)
- **Resource bundle** (2): translate keys, optionally for a locale
- **Password services** (6): domains, permissions, questions, unlock, reset, update password — callable **without** login
- **Reports** (2): operators, run preview (body passed through as a dict; return type left as raw JSON — doc gap #13)

### Phase 7 — OAuth 1.0
Branch: `feat/oauth1`

- `SysAid.from_oauth(...)` plus helpers for the three legs: request token → authorize URL → access token
- Lazy import of `requests-oauthlib` with a clear error if the extra is missing

Kept late and isolated: it cannot be verified without a consumer key (doc gap #2). **May be dropped from 0.1.0** if the homologation instance has no consumer key.

### Phase 8 — Documentation
Branch: `docs/usage-guide`

- README: install, quick start, auth, pagination, filters, dates, errors, per-resource examples
- Docstrings on every public method (Google style), `CONTRIBUTING.md`, integration-test instructions

### Phase 9 — Live validation (needs the homologation instance)
Branch: `test/live-validation`

1. Run the unit suite for the first time; fix failures.
2. Run read-only integration tests; then destructive ones with `SYSAID_ALLOW_WRITES=1`.
3. Resolve every row of the doc-gap table below; replace doc-sample fixtures with sanitized real payloads.
4. Enable the CI test job.

### Phase 10 — Release
Branch: `chore/release-0.1.0`

- Confirm PyPI name, bump version, finalize CHANGELOG
- `release.yml`: build + publish via PyPI Trusted Publishing on tag; dry run on TestPyPI first
- Merge `develop` → `main`, tag `v0.1.0`

---

## 5. Doc gaps to settle in Phase 9

Coded with the "initial assumption" so each one is a one-line change if the server disagrees.

| Gap (ANOTATIONS §17) | Initial assumption |
|---|---|
| 1. Login body format | JSON body |
| 4. Photo download | `GET /users/{id}/photo` returns raw bytes |
| 5. CI relations path | `/ci/{id}/relation` |
| 6. Add-ons path | Plural for list/get/refresh, singular for update/test |
| 7. CI types param | `supportBarcode` |
| 8. `/ci/barcode` | Not implemented until confirmed |
| 9. `GET /asset` `type` param | Passed through if given |
| 11. Attachment part name | `file` |
| 12. Action-item state changes | Empty body |
| 13. `runPreview` response | Returned as raw JSON |
| 14. Download File / Translate Key | Not implemented (no path documented) |
| 15. Error format | `{"status","message"}` when JSON, else response text |
| 16. Asset caption keys | Both spellings accepted |
| 17. Default `limit` | Client always sends an explicit `limit` when iterating |

---

## 6. Risks

- **Docs vs reality.** Methods and paths come from a help index for v24.4.60; Phases 1–7 are unverified until Phase 9. Mitigation: one request path, assumptions isolated per the table above.
- **Login requires an admin with mobile-app permission.** The homologation account must have both.
- **Destructive calls** (delete SR, send message, password reset, add-on update) are never run without `SYSAID_ALLOW_WRITES=1`, and only against homologation — never the production host named in ANOTATIONS.md.
- **Late first test run.** Running nothing until Phase 9 means bugs accumulate. Recommendation: allow the mocked unit suite to run from Phase 1 (it needs no server).
