# python-sysaid

Python wrapper for the SysAid REST API (`/api/v1`, SysAid 15.4+).

> Status: alpha, under development. Requests and paths come from the SysAid
> documentation and have not been validated against a live server yet.

## Installation

```bash
pip install python-sysaid
pip install "python-sysaid[oauth]"   # optional: OAuth 1.0
```

Requires Python 3.10+.

## Quick start

```python
from sysaid import SysAid

with SysAid("https://sysaid.example.com", username="sysaid", password="...") as client:
    sr = client.service_requests.get(273, fields=["title", "status"])
    sr["title"]            # raw value
    sr.caption("status")   # display value

    for sr in client.service_requests.iter(type="incident", status=[4, 5]):
        print(sr.id, sr["title"])

    client.service_requests.update(273, status=2, responsibility=66)
    client.service_requests.close(273, solution="restarted")
```

The client logs in on first use (`POST /login`, the `JSESSIONID` cookie is kept by the
session). The account must be an administrator with mobile-app permission. Pass
`account_id=` if your installation needs one, and `verify=`/`timeout=`/`session=` to
control the underlying `requests` session.

## Records

List and get calls return `Record` objects, which behave like a read-only mapping of
field key to raw value:

```python
record["status"]               # raw value (an id, ms timestamp or text)
record.caption("status")       # display value (valueCaption)
record.fields["status"]        # Field: key_caption, mandatory, editable, type, ...
record.raw                     # the original dict (canUpdate, name, group, ...)
```

## Pagination

`list()` returns one page (`limit`/`offset`); `iter()` yields every record and stops at the
first page shorter than `page_size` (default 100):

```python
client.service_requests.list(limit=50, offset=100)
client.service_requests.iter(page_size=200)
```

## Filters and parameters

Filter ids come from `client.filters`. Pass them as keyword arguments:

```python
client.service_requests.list(status=[4, 5], request_user=235)   # status=4,5&request_user=235
client.service_requests.list(archive=True)                      # archive=1
```

Use `view=` and `fields=` to choose the returned fields, and `sort=`/`direction=`.

## Dates

Datetimes are sent as milliseconds since the epoch in UTC (naive datetimes are taken as
UTC). A `(from, to)` tuple is a range, with `None` for an open end:

```python
from datetime import datetime, timezone

since = datetime(2024, 1, 1, tzinfo=timezone.utc)
client.service_requests.list(due_date=(since, None))        # due_date=<ms>,0
client.service_requests.update(273, due_date=datetime.now(timezone.utc))
```

## Writing

Write calls take field values as keywords. For field ids that clash with a method's own
keywords (the SR field `type`), pass a mapping as the first argument:

```python
from sysaid.resources.service_requests import make_note, problem_type

client.service_requests.create(
    {"type": 3},
    type="incident",             # the SR type query parameter
    template=39,
    title="Printer down",
    problem_type=problem_type("UserWorkstation", "PC", "Password"),
    notes=[make_note("sysaid", "Created from the API")],
)
```

`client.service_requests.template(type="incident")` shows the mandatory fields first.

Numbers, booleans and datetimes are sent as strings, which is the only form the server
accepts for field values. `add_activity` takes the numeric id of the user.

## Resources

| Attribute | Covers |
|---|---|
| `client.users` | list, iter, get, search, photo get/upload, permissions |
| `client.filters` / `client.lists` | filter definitions, dropdown id/caption pairs |
| `client.service_requests` | list, iter, get, search, count, template, create, update, close, links, attachments, activities, `send_message` |
| `client.resource_bundle` | translate |

### Disabled features

These are implemented from the REST guide but have not been verified against a live server
yet, so calling them raises `UnverifiedFeatureError` before any request is made:

| Attribute | Disabled calls |
|---|---|
| `client.service_requests` | delete |
| `client.action_items` | list, iter, count, approve, reject, complete, reopen |
| `client.assets` | list, iter, get, search |
| `client.cis` | list, iter, update, types, view_fields, relation types, relations |
| `client.addons` | list, get, update, test_connection, refresh |
| `client.password_services` | domains, permissions, questions, unlock, reset, update_password |
| `client.reports` | operators, run_preview |
| OAuth 1.0 | `SysAid.from_oauth` and the `sysaid.oauth` helpers |

## Errors

Every error derives from `SysAidError`. Non-2xx answers raise a subclass of
`SysAidHTTPError` (`BadRequestError`, `UnauthorizedError`, `ForbiddenError`,
`NotFoundError`, `ServerError`) carrying `status_code`, `message` and `response`.
Failed logins raise `AuthenticationError`. Failed CI relation creation raises
`RelationError` with the per-item `failures`.

```python
from sysaid import NotFoundError

try:
    client.service_requests.get(999999)
except NotFoundError as exc:
    print(exc.status_code, exc.message)
```

## OAuth 1.0

Disabled until verified (see [Disabled features](#disabled-features)). The intended flow
needs `python-sysaid[oauth]` and a consumer key issued by SysAid:

```python
from sysaid import SysAid, oauth

token = oauth.request_token(url, consumer_key, "https://app/callback")
print(oauth.authorize_url(url, token["oauth_token"]))
# ...the user authorizes; SysAid redirects with oauth_verifier...
access = oauth.access_token(
    url, consumer_key, token["oauth_token"], token["oauth_token_secret"], verifier
)
client = SysAid.from_oauth(url, consumer_key, access["oauth_token"], access["oauth_token_secret"])
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
