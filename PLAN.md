# python-sysaid — Implementation Plan

A Python wrapper for the SysAid REST API (`/api/v1`), to be published on PyPI.
Endpoint reference: [ANOTATIONS.md](ANOTATIONS.md) (61 endpoints, 12 resource areas, SysAid 15.4+).

Status: **phases 0–9 done; phase 10 (release) pending.** Live results: [§5](#5-live-validation-results-phase-9).

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
| 9 Live validation | Done against SysAid v24.4.60 (partial coverage, see §5) | — |
| 10 Release | **Pending** — after phase 9 | — |

**Pending before 0.1.0**
- Re-run the live suite with an account that can see inventory, CMDB, reports and add-on
  parameters, on an instance with action items and Password Services enabled (§5.3).
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

## 5. Live validation results (Phase 9)

Run against the homologation instance (SysAid **v24.4.60**) with the unit suite (97 tests)
and `tests/integration/` (27 tests: 22 passed, 4 skipped for permissions, 1 expected failure).

### 5.1 Bugs found and fixed

| Finding | Fix |
|---|---|
| `POST /sr` and `PUT /sr/{id}` answer HTTP 500 (`Integer cannot be cast to String`) for JSON numbers, including `due_date`; the guide's samples use numbers | `info` scalars (numbers, booleans, datetimes) are sent as strings |
| Activity `userId` must be the numeric user id, not the login name shown in the guide | `add_activity` takes `int \| str`; documented |
| `PUT /addon/{name}` and `/addon/{name}/testConnection` do not exist (404); the plural paths do | Both use `/addons/...` |
| `POST /reports/allReports/{id}/runPreview` does not exist (404); `/reports/{id}/runPreview` does | Path changed |
| `GET /users/{id}/permission/{permissionId}` does not exist (404) | `users.permission()` reads from the permissions list |
| Unrouted or filtered requests return Tomcat HTML pages, which ended up as the error message | The reason phrase is used for HTML bodies |

### 5.2 Doc gaps

| Gap (ANOTATIONS §17) | Outcome |
|---|---|
| 1. Login body format | **Confirmed**: JSON body. No top-level `user_id`; it is read from `user.id` |
| 4. Photo download | **Confirmed**: raw bytes (`application/octet-stream`); 204 with no body when there is no photo |
| 5. CI relations path | Route `/ci/{id}/relation` exists for GET/POST/DELETE (`/ci/{id}/relations` is 404); payloads unverified |
| 6. Add-ons path | **Wrong in the guide**: plural everywhere (fixed) |
| 7. CI types param | Unverified (no CMDB permission); `/ci/type` exists, `/ci/types` does not |
| 8. `/ci/barcode` | Does not exist (404); stays unimplemented |
| 9. `GET /asset` `type` param | Unverified (no inventory permission) |
| 11. Attachment part name | **Confirmed**: `file` |
| 12. Action-item state changes | Route exists and takes an empty body; unverified (no action items on the instance) |
| 13. `runPreview` response | Unverified (403); path fixed |
| 14. Download File / Translate Key | Still not implemented |
| 15. Error format | **Confirmed**: `{"status","message"}` from the API; HTML pages from the servlet container. A missing SR, user or list is 400, not 404 |
| 16. Asset caption keys | Unverified (no inventory permission) |
| 17. Default `limit` | `iter()` always sends `limit`; paging confirmed on users and SRs |

`send_message` was verified later, once the API user had an e-mail address: to/cc, subject,
body, attachments and the `method`, `addAttachmentToSr` and `addSrDetails` parameters are
accepted and the message is recorded on the SR. Only `email` was sent, and only to the API
user itself; delivery to the mailbox was not checked.

Other behaviour seen: `notes` is written as objects and read back as formatted strings;
unknown list values (e.g. a status id that does not exist) are ignored silently with HTTP 200;
`priority` is recomputed from `urgency`/`impact`.

### 5.3 Not verified end to end (disabled)

The API account lacks the permissions, or the instance lacks the data. Every call of the
resources below is **disabled**: it raises `UnverifiedFeatureError` until it is verified and
its `@unverified` decorator removed. That includes the parts that did work (action-item
count, add-on list and refresh, password-service domains and permissions), so that no
resource is half available.

| Area | Reason | What was checked |
|---|---|---|
| Assets (list, get, search) | 401, no inventory permission | Routes exist |
| CIs (all 8 calls) | 401, no CMDB permission | Routes exist |
| Add-ons get, update, test connection | 403 | Routes exist; list and refresh work |
| Reports (operators, run preview) | 403 | Routes exist |
| Action items list and state changes | `GET /action_item` answers HTTP 500 while the count is 0 | Count works |
| Password services questions, unlock, reset, update password | Module disabled (HTTP 500 with a message) | Domains and permissions work |
| SR delete | 401, no purge permission | Request reaches the permission check |
| OAuth 1.0 | No consumer key | The three endpoints exist |

---

## 6. Risks

- **Docs vs reality.** Methods and paths come from a help index for v24.4.60. Phase 9 verified the areas in §5; those in §5.3 still rest on the documentation.
- **Login requires an admin with mobile-app permission.** The homologation account must have both.
- **Destructive calls** (delete SR, send message, password reset, add-on update) are never run without `SYSAID_ALLOW_WRITES=1`, and only against homologation — never the production host named in ANOTATIONS.md.
- **Late first test run.** Running nothing until Phase 9 means bugs accumulate. Recommendation: allow the mocked unit suite to run from Phase 1 (it needs no server).
