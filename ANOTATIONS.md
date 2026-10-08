# SysAid REST API — Usage Notes

Compiled from:
- `SysAid Help.html` (frameset; real content in `SysAid Help_files/treecontent.html`): intro, OAuth, endpoint index (method + path), appendices.
- `SysAid API Guide.html`: per-endpoint parameters, payloads, sample responses.

Source instance: `centraldeservicos.presidencia.gov.br` — SysAid **v24.4.60**. The API is supported on SysAid **15.4+**.

> Items marked **⚠ Doc gap** are places where the documentation is missing, contradictory or marked "TBD". Verify them against the live server before relying on them.

---

## Contents

1. [General concepts](#1-general-concepts)
2. [Authentication](#2-authentication)
3. [Login (non-OAuth)](#3-login-non-oauth)
4. [Users](#4-users)
5. [Filters](#5-filters)
6. [Service Requests (SR)](#6-service-requests-sr)
7. [Action Items](#7-action-items)
8. [Assets](#8-assets)
9. [Lists](#9-lists)
10. [Add-ons](#10-add-ons)
11. [CIs (Configuration Items)](#11-cis-configuration-items)
12. [Resource Bundle (RB)](#12-resource-bundle-rb)
13. [Password Services (PS)](#13-password-services-ps)
14. [Reports](#14-reports)
15. [Non-resource calls](#15-non-resource-calls)
16. [Appendices (field types, list entities)](#16-appendices)
17. [Documentation gaps and inconsistencies](#17-documentation-gaps-and-inconsistencies)
18. [Quick reference table of all endpoints](#18-quick-reference-all-endpoints)

---

## 1. General concepts

### Base URL
The endpoint is appended to the account URL:

```
https://<your-sysaid-host>/api/v1/<api_url>
```

All paths below are relative to `/api/v1`. On this instance, the Help is served from `https://centraldeservicos.presidencia.gov.br/help/...`, so the API is likely `https://centraldeservicos.presidencia.gov.br/api/v1/...` (inferred, not stated in the docs).

### Format
- Requests and responses are JSON, except file uploads (multipart/form-data) and OAuth (header-based).
- The docs' sample JSON uses typographic quotes and has small syntax errors. Use standard JSON.

### SysAid entities
An entity is anything in SysAid with a list page and a form page. The API exposes: **service records (SR), assets, CIs, users** (plus action items, lists, filters, etc.).

### Common parameters

| Param | Meaning |
|---|---|
| `offset` | Start position for list calls. Zero-based. Default `0`. |
| `limit` | Max items per call. Default **500** (configurable server-side; CIs: `serverConf > apiConf > maxChunkSize`). |
| `view` | Name of a SysAid *view* that defines which fields are returned. Created/customized in the SysAid admin UI. Mobile views: `Mobile` (users), `SysAidMobile` (SR/filters), `SysAidMobileAssets` (assets). |
| `fields` | Comma-separated field names to return. If sent together with `view`, you get **view fields + these fields**. If neither is sent, **all fields** are returned. |
| `sort` | Field(s) to sort by (must be among fetched fields). |
| `dir` | `asc` (default) or `desc`. Only relevant when `sort` is sent. |
| `{filters}` | Dynamic key/value params: `{filter.id}={filter.values.id}`, e.g. `&status=19&request_user=235`. Several values: comma-separated, `&status=4,5`. Filter ids/values come from `GET /filters`. |
| `info` | Generic term for the array of `{key, value}` field objects in requests/responses. |

### Response object shape (`info` arrays)
Most entities come back as:

```json
{
  "id": "5433",
  "info": [
    { "key": "title", "keyCaption": "Title", "value": "basic Service Request", "valueCaption": "basic Service Request" }
  ]
}
```

- `key` = field id; `keyCaption` = display label.
- `value` = raw value (id, ms timestamp, text); `valueCaption` = display string.
- Form/template calls add metadata: `mandatory`, `editable`, `type` (see [Appendix A](#appendix-a--field-types)), `defaultValue`.
- Assets use `key_caption`/`value_caption` (snake_case) in samples, other entities use `keyCaption`/`valueCaption`. **⚠ Doc gap** (likely just inconsistent docs).

### Dates
- Always **milliseconds since epoch, UTC/GMT** (e.g. `1398935657000`).
- Exact match: `&due_date=1398935657000`
- Range: `&due_date=<from>,<to>` → `&due_date=1398935657000,1399313657000`
- From only: `&due_date=1398935657000,0`
- To only: `&due_date=0,1399313657000`

### User-related fields
User fields (e.g. `request_user`, `responsibility`) return the **user ID**. Call the Users API for details.

### Pagination pattern
```
GET /sr?limit=100&offset=0
GET /sr?limit=100&offset=100
...
```
Stop when you get fewer than `limit` items (or use `GET /sr/count?...` first).

---

## 2. Authentication

Two ways to use the API:

1. **Session login** (`POST /login`) → keep the `JSESSIONID` cookie. See [section 3](#3-login-non-oauth).
2. **OAuth 1.0** (more secure; requires a *consumer key*) — three-legged flow below.

### OAuth 1.0 flow

You need a **consumer key** first (how to create one is not covered in these docs). **⚠ Doc gap**

#### Step 1 — Get a request token
`POST /oauth/request_token`

Signed request; OAuth parameters go in the `Authorization` header:

| Parameter | Description |
|---|---|
| `oauth_consumer_key` | Consumer key |
| `oauth_signature_method` | e.g. `HMAC-SHA1` |
| `oauth_signature` | Signature |
| `oauth_timestamp` | Per OAuth 1.0 nonce/timestamp |
| `oauth_nonce` | Per OAuth 1.0 nonce/timestamp |
| `oauth_version` | Must be `1.0` |
| `oauth_callback` | Absolute URL SysAid redirects to after user authorization |

Example header:
```
Authorization: OAuth realm="http%3A%2F%2Flocalhost%2F",oauth_version="1.0",oauth_callback="http%3A%2F%2F10.1.11.124%3A8088%2Foauth%2FTestOAuth.html",oauth_consumer_key="87bef7e3...",oauth_timestamp="1441520072",oauth_nonce="5tR5N7yzfK0T6kcc",oauth_signature_method="HMAC-SHA1",oauth_signature="PXgTdIttGkvLcwYs6zMNOs4awX0%3D"
```

Response:
```json
{
  "oauth_token": "ab7d6485...",
  "oauth_token_secret": "a7983ed7...",
  "oauth_callback_confirmed": true
}
```
`oauth_callback_confirmed` must be `true`.

#### Step 2 — Authorize the user
`GET /oauth/authorize?oauth_token=<temporary token>`

Redirect the user's browser to SysAid. After they authorize, SysAid redirects to your `oauth_callback` with:
```
?oauth_token=ab7d6485...&oauth_verifier=ab7d6485...
```

#### Step 3 — Exchange for an access token
`POST /oauth/access_token`

Signed, `Authorization` header with: `oauth_consumer_key`, `oauth_token` (request token), `oauth_signature_method`, `oauth_signature`, `oauth_timestamp`, `oauth_nonce`, `oauth_version=1.0`, `oauth_verifier`.

Response:
```json
{ "oauth_token": "3b7d6485...", "oauth_token_secret": "a7983ed7..." }
```

#### Step 4 — Call the API
Sign **every** API request with: `oauth_consumer_key`, `oauth_token` (the access token), `oauth_signature_method`, `oauth_signature`, `oauth_timestamp`, `oauth_nonce`, `oauth_version=1.0`. The access token is valid for the session.

> The API Guide HTML has the OAuth section commented out, but the Help page still documents it.

---

## 3. Login (non-OAuth)

### Authenticate a user
`POST /login`

Checks that the user is an **administrator** and has permission to access the **mobile app**. (Per the Help index; a non-admin or user without mobile permission will likely fail. **⚠ Doc gap**: exact failure responses not documented.)

**Parameters**

| Field | Required | Description |
|---|---|---|
| `user_name` | **Yes** | User name (example: `sysaid`) |
| `password` | **Yes** | Password, URL-encoded (UTF-8) |
| `account_id` | No | Account id (example: `cmdb`) |
| `mobile_app` | No | `true` for the mobile app |
| `version` | No | App version |
| `device` | No | Device model |
| `os` | No | OS type |
| `os_version` | No | OS version |
| `push_id` | No | Push-notification id |

**⚠ Doc gap:** the docs don't say whether these go in a JSON body, form body, or query string. A JSON body (`Content-Type: application/json`) is the usual choice; test form-encoded if it fails.

**Returns:** access info, SysAid version, and basic info about the logged-in user.

```json
{
  "language": "en",
  "sysaid_version": "",
  "date_format": "yyyymmdd hh:MM:ss",
  "user": {
    "id": "2",
    "name": "ILIENT\\Barby",
    "info": [
      { "key": "display_name", "value": "Barbara Straisend" },
      { "key": "email_address", "value": "barbara@gmail.com" },
      { "key": "building", "value": "1C" }
    ]
  }
}
```

| Return field | Description |
|---|---|
| `logged_in` | true/false |
| `user_id` | Unique user id |
| `language` | User's default language |
| `error_msg` | Optional error text on failure |
| `sysaid_version` | Server version |

> **Important:** after a successful login, read the **`JSESSIONID` cookie** from the response headers and send it with **every subsequent request**.

Example:
```bash
curl -i -X POST "https://HOST/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"user_name":"sysaid","password":"password123"}'
# then:
curl "https://HOST/api/v1/sr?limit=5" -H "Cookie: JSESSIONID=<value>"
```

---

## 4. Users

### 4.1 Get Users List
`GET /users?view={view}&fields={f1,f2}&type={type}&offset={n}&limit={n}`

| Param | Description |
|---|---|
| `view` | Optional. View defining fields (mobile view = `Mobile`). |
| `fields` | Optional. Comma-separated fields; combined with `view` if both sent. |
| `type` | Optional. `admin`, `user`, or `manager`. Default: all. |
| `offset` | Optional. Zero-based. Default 0. |
| `limit` | Optional. Default 500. |

Returns a list of `{id, name, info[]}`. With no `view`/`fields`, full user info.

```json
[
  { "id": "1", "name": "ILIENT\\Johnny",
    "info": [ {"key":"display_name","value":"John Doe"}, {"key":"email_address","value":"john@gmail.com"} ] }
]
```

### 4.2 Get User
`GET /users/{id}?view={view}&fields={f1,f2}`

Returns `{id, name, info[]}`. Example `GET /users/1?view=Mobile` returns the fields defined in *User Form > Mobile tab* (display_name, first_name, last_name, phone, cell_phone, email_address, cubic...).

### 4.3 Search Users
`GET /users/search?query={q}&view=&fields=&type=&offset=&limit=&sort=&dir=`

| Param | Description |
|---|---|
| `query` | **Required.** Search criteria. |
| `view`, `fields`, `type`, `offset`, `limit` | As in Get Users List. |
| `sort` | Optional. Default `calculated_user_name`. |
| `dir` | Optional. `asc` (default) / `desc`. |

Returns, per user: `id`, `name`, `isAdmin`, `isSysAidAdmin`, `isManager`, `info[]` (each with `key`, `keyCaption`, `value`, `valueCaption`).

Example: `GET /users/search?query=Jo&fields=display_name,email_address&limit=2`

### 4.4 Get User's Photo
`GET /users/{id}/photo` — downloads the user's photo (file response).
**⚠ Doc gap:** only listed in the Help index; the Guide's "Download File" section is "TBD".

### 4.5 Upload User's Photo
`POST /users/{id}/photo`

- Payload: `multipart/form-data`
- Field `file`: the image file part
- **Max size: 500 KB**

```bash
curl -X POST "https://HOST/api/v1/users/1/photo" -H "Cookie: JSESSIONID=..." -F "file=@photo.jpg"
```

### 4.6 Get User Permissions
`GET /users/{id}/permission` — no parameters.

```json
{ "id": "1", "name": "ILIENT\\Moshiko",
  "permissions": [
    {"key":"userPermissionUserSelfService","value":"false"},
    {"key":"userPermissionHelpDeskView","value":"true"},
    {"key":"userPermissionHelpDeskChangeType","value":"All"},
    {"key":"userPermissionCMDBViewType","value":"All"}
  ] }
```

### 4.7 Get a User's Permission
`GET /users/{id}/permission/{permissionId}` — e.g. `/users/1/permission/userPermissionUserSelfService`

```json
{ "key": "userPermissionUserSelfService", "value": "false" }
```

---

## 5. Filters

Filters define the valid query parameters (and their allowed values) for list calls such as `/sr`, `/ci`, `/action_item`.

### 5.1 Get Filters List
`GET /filters?view={view}&fields={f1,f2}&offset={n}&limit={n}`

| Param | Description |
|---|---|
| `view` | Optional. Defaults to `SysAidMobile`. |
| `fields` | Optional. Filter fields to return (e.g. `values`). All if omitted. |
| `offset` / `limit` | Optional. For the **filter values**. Default 0 / 500. |

```json
[
  { "id": "status", "type": "list",
    "values": [ {"id":"1","caption":"closed"}, {"id":"2","caption":"awaiting"} ],
    "metadata": { "limit":"20", "offset":"0", "total":"2" } }
]
```

| Field | Description |
|---|---|
| `id` | Filter id (always returned). Use as the query-param name. |
| `type` | `text`, `numeric`, `boolean`, `date`, `list`, `nested`, `custom` |
| `values[].id` / `values[].caption` | Value id (use as param value) and display text |
| `metadata.limit/offset/total` | Pagination info (only when `values` is returned) |

### 5.2 Get Filter
`GET /filters/{id}?view={view}&offset={n}&limit={n}` — same output shape for a single filter, e.g. `/filters/status?view=SysAidMobile`.

**Typical use:** fetch `/filters/status` to learn status ids, then `GET /sr?status=4,5`.

---

## 6. Service Requests (SR)

"Service record" covers types: **incident, request, problem, change** (plus `all` in some calls).

### 6.1 Get Service Request List
`GET /sr?view=&fields=&ids=&type=&archive=&offset=&limit=&sort=&dir=&{filter}={value}...`

| Param | Description |
|---|---|
| `view` | Optional. If absent → `fields`; if both absent → all fields. |
| `fields` | Optional. Combined with `view` if both given. |
| `type` | Optional. `incident`, `request`, `problem`, `change`, `all`. Multiple comma-separated (`type=incident,request`). If omitted, defaults to views created on the *incident* list. **If your view was created on the "All" list, you must pass `type=all`.** |
| `ids` | Optional. Comma-separated SR ids. |
| `archive` | Optional. `1` = archived SRs, `0` = not. |
| `offset`, `limit` | Optional. Default 0 / 500. |
| `sort`, `dir` | Optional. |
| `{filters}` | Optional. e.g. `&status=19&request_user=235`, `&status=4,5`. Dates in ms (see [Dates](#dates)). |

Response:
```json
[
  { "id": "5433", "canUpdate": "true", "canDelete": "false", "canArchive": "false",
    "info": [
      {"key":"title","keyCaption":"Title","value":"basic Service Request","valueCaption":"basic Service Request"},
      {"key":"insert_time","keyCaption":"Request Time","value":"1397564800000","valueCaption":"2014-04-01 11:46:48"},
      {"key":"request_user","keyCaption":"Request User","value":"leo@law.com","valueCaption":"Leonardo Gonzalez"}
    ] }
]
```
`canUpdate` / `canDelete` / `canArchive` = current user's permissions on that SR.

Example: `GET /sr?view=SysAidMobile&fields=type,computer_id&limit=2`

### 6.2 Get Service Request (form)
`GET /sr/{id}?view={view}&fields={f1,f2}`

Returns the SR with per-field metadata: `mandatory`, `editable`, `type`, `defaultValue` in addition to key/value/captions.

Example: `GET /sr/273?fields=type,archive,update_time,status`

### 6.3 Search Service Requests
`GET /sr/search?query={q}&view=&fields=&type=&offset=&limit=&archive=&sort=&dir=&{filter}={value}`

Same as the list call plus a required `query`. **`type` defaults to `incident`** here.

Example: `GET /sr/search?query=54&view=SysAidMobile&limit=2`

### 6.4 Update Service Request
`PUT /sr/{id}`

Body: JSON with **only the fields to change**.

| Field | Description |
|---|---|
| `id` | SR id |
| `info[].key` | Field id |
| `info[].value` | New value |

```json
{
  "id": "273",
  "info": [
    { "key": "update_time", "value": 1391756438000 },
    { "key": "status", "value": 2 },
    { "key": "notes", "value": [ { "userName": "sysaid", "createDate": 1391756438000, "text": "Note 123" } ] },
    { "key": "responsibility", "value": 66 }
  ]
}
```
(The doc sample writes the last item as `{"responsibility":66}`, which is not in key/value form; it's almost certainly a doc typo. **⚠ Doc gap**)

**Special fields**

| Field | Format |
|---|---|
| `notes` | Array of `{ "userName": <name>, "createDate": <ms>, "text": <text> }` |
| `due_date` | Long, ms UTC. (`insert_time` is read-only.) |
| `problem_type` | Categories joined by `_`: `<type>` (level 1), `<type>_<subtype>` (levels 1–2), `<type>_<subtype>_<third>` (all 3). |

**Not updatable here** (use their own calls): messages, attachments, links, activities.
**Read-only:** history, chats, department, CI relations, computer_name.

### 6.5 Count Service Requests
`GET /sr/count?{filter}={value}...`

```json
{ "count": 128 }
```
Example: `GET /sr/count?computer_id=1`

### 6.6 Close Service Request
`PUT /sr/{id}/close`

Sets the status to the default *Close* status from Help Desk settings.

```json
{ "solution": "restart the computer…" }
```

### 6.7 Get Service Request Template
`GET /sr/template?view=&fields=&type=&template=`

| Param | Description |
|---|---|
| `view`, `fields` | Optional, as usual. |
| `type` | Optional. `incident` (default), `request`, `problem`, `change`, `all`. |
| `template` | Optional. Template id for that SR type. Default = first/default template. |

Returns an SR with `id: "0"` (= new/unsaved) and fields with `mandatory/editable/type/defaultValue`. Use it to discover required fields before creating.

Example: `GET /sr/template?type=incident&template=39`

### 6.8 Create Service Request
`POST /sr?view={view}&type={sr_type}&template={template_id}` (`fields` also accepted)

Body: JSON with `info[]` of key/value pairs.

```json
{
  "info": [
    { "key": "due_date", "value": 1391756438000 },
    { "key": "status", "value": 2 },
    { "key": "problem_type", "value": "UserWorkstation_PC_Password" },
    { "key": "notes", "value": [ { "userName": "sysaid", "createDate": 1391756438000, "text": "Note 123" } ] },
    { "key": "responsibility", "value": 66 }
  ]
}
```
(The doc sample has a missing comma and the same `{"responsibility":66}` typo; fixed above.)

Special fields: `notes`, `due_date`, `problem_type` (e.g. `Cat1_SubCat1_ThirdCat1`), as in Update.

Returns the new SR (with its real `id`, e.g. `"45"`) in the shape requested by `view`/`fields`.

**After creation**, add messages, attachments, links and activities via their own endpoints.

**Recommended flow:**
1. `GET /sr/template?type=incident` → see mandatory fields.
2. `GET /list?entity=sr` (or `/filters`) → find valid ids for lists (status, priority, etc.).
3. `POST /sr?type=incident` with the needed `info`.

### 6.9 Delete Service Request(s)
`DELETE /sr?ids={id1,id2,...}`

| Param | Description |
|---|---|
| `ids` | Comma-separated SR ids to delete. |

### 6.10 Links

**Add** — `POST /sr/{id}/link`
```json
{ "name": "link2", "link": "http://google.co.il" }
```

**Delete** — `DELETE /sr/{id}/link`
```json
{ "name": "link2" }
```
(Delete takes its payload in the request **body**.)

### 6.11 Attachments

**Add** — `POST /sr/{id}/attachment`
- `multipart/form-data` with the file.
- **⚠ Doc gap:** the part name isn't stated (likely `file`, as for photos).

**Delete** — `DELETE /sr/{id}/attachment`
```json
{ "fileId": "111934645_312638760" }
```

### 6.12 Activities

**Add** — `POST /sr/{id}/activity`

| Field | Description |
|---|---|
| `userId` | User name for the activity (e.g. `"sysaid"`) |
| `fromTime` | Start time (ms) |
| `toTime` | End time (ms) |
| `description` | Text |

```json
{ "userId": "sysaid", "fromTime": "1378501200000", "toTime": "1378846800000", "description": "This is an activity from API" }
```
Total time is calculated automatically.

**Delete** — `DELETE /sr/{id}/activity`
```json
{ "id": 2 }
```

### 6.13 Send Message From a Service Request
`POST /sr/{id}/message?method={method}&addAttachmentToSr={bool}&addSrDetails={bool}`

| Param | Description |
|---|---|
| `method` | Optional. `email` (default), `sms`, `broadcast`, `im`. |
| `addAttachmentToSr` | Optional. `true` (default) / `false` — also attach files to the SR. |
| `addSrDetails` | Optional. `true` (default) / `false` — include SR details in the message. |

Body: **multipart** with:
- `file` (optional, repeatable): attachments
- `message`: a **non-encoded JSON string**:

| Field | Description |
|---|---|
| `fromUserId` | Sender user id |
| `toUsers` | Required. Comma-separated user ids; groups in brackets, e.g. `"1,23,22,45,[3],67"` |
| `ccUsers` | Optional. Same format |
| `msgSubject` | Optional |
| `msgBody` | Optional |

```json
{"fromUserId":"124","toUsers":"1,140,123,124","ccUsers":"3,125,127,[11]","msgSubject":"This is a message from API","msgBody":"Hello"}
```

```bash
curl -X POST "https://HOST/api/v1/sr/6/message?method=email" -H "Cookie: JSESSIONID=..." \
  -F 'message={"fromUserId":"124","toUsers":"1,140","msgSubject":"Hi","msgBody":"Hello"}' \
  -F "file=@doc.pdf"
```
Invalid addresses or addresses of disabled users are ignored (logged); valid ones still receive the mail.

---

## 7. Action Items

### 7.1 Get Action Items
`GET /action_item?view=&fields=&type=&archive=&ids=&staticFilterId=&{filter}={value}&query=&offset=&limit=&sort=&dir=`

| Param | Description |
|---|---|
| `view`, `fields` | As usual. |
| `type` | `incident`, `request`, `problem`, `change`, `all` (default incident per docs). |
| `ids` | Comma-separated **SR ids** whose action items to return. |
| `{filters}` | e.g. `status=19`. `status=active` returns only active action items. |
| `staticFilterId` | Static filter from the scoreboard. |
| `archive` | `1`/`0`. |
| `query` | Search criteria. |
| `offset`, `limit`, `sort`, `dir` | Standard. |

```json
[
  { "id": "24", "tabName": "1", "subTabName": "2", "hasApproved": "true", "hasEmptyRequred": "false" }
]
```
(`hasEmptyRequred` is spelled this way in the docs.)

### 7.2 Count Action Items
`GET /action_item/count?` (same filter params as above, without paging/sort)

```json
{ "count": 24 }
```

### 7.3 State changes
All take the **action item id** in the path, no payload documented:

| Action | Call |
|---|---|
| Approve | `PUT /action_item/{id}/approve` |
| Reject | `PUT /action_item/{id}/reject` |
| Complete | `PUT /action_item/{id}/complete` |
| Reopen | `PUT /action_item/{id}/reopen` |

---

## 8. Assets

### 8.1 Get Assets List
`GET /asset?view=&fields=&offset=&limit=`

Mobile view: `SysAidMobileAssets`. (The Help index also lists a `type` param that the Guide doesn't describe. **⚠ Doc gap**)

Returns `{id, name, group, info[]}` per asset. Asset ids are strings like `497db453:147bee7ec09:-7ff2` or a license-like key.

```json
[
  { "id": "497db453:147bee7ec09:-7ff2", "name": "ISA-VCHER-DW7", "group": "\\",
    "info": [ {"key":"computer_type","key_caption":"Type","value":"Workstation","value_caption":"Workstation"} ] }
]
```
Example: `GET /asset?fields=computer_type,ip_address,serial&limit=2`

### 8.2 Get Asset
`GET /asset/{id}?view={view}&fields={f1,f2}`

`view` here is a SysAid *Asset Form* view. Asset ids containing `:` should be URL-encoded if your client requires it.

### 8.3 Search Assets
`GET /asset/search?query={q}&view=&fields=&offset=&limit=`

Example: `GET /asset/search?query=DW7&fields=computer_type,ip_address,serial&limit=2`

---

## 9. Lists

Lists provide the id/caption pairs for dropdown fields (priority, status, impact, urgency, location, company, department, SLA agreement, source, custom lists, etc.). Use them to translate captions to ids when creating/updating records.

### 9.1 Get All Lists
`GET /list?entity={entity}&fields={f1,f2}&offset={n}&limit={n}`

| Param | Description |
|---|---|
| `entity` | Optional. Default `sr`. See [Appendix B](#appendix-b--list-entities). |
| `fields` | Optional. `id` (always), `caption`, `values`. |
| `offset`, `limit` | For list values. Default 0 / 500. |

```json
[
  { "id": "priority", "caption": "Priority",
    "values": [ {"id":"1","caption":"Highest"}, {"id":"2","caption":"High"}, {"id":"3","caption":"Low"} ] },
  { "id": "sr_type", "caption": "Service Record type",
    "values": [ {"id":"1","caption":"Change"}, {"id":"2","caption":"Problem"}, {"id":"3","caption":"Incident"}, {"id":"4","caption":"Request"} ] }
]
```
Sample lists in the docs: location, impact, urgency, priority, change_category, survey_status, sr_type, responsibility, status, company, department, agreement, source, cust_list1, cust_list2. The values shown are illustrative; fetch your own.

### 9.2 Get List
`GET /list/{id}?entity=&entityId=&entityType=&fields=&offset=&limit=&key=`

| Param | Description |
|---|---|
| `{id}` (path) | List id, e.g. `responsibility`, `priority`. |
| `entity` | Optional. Default `sr`. |
| `entityId` | Optional. Entity record id to apply context filtering (e.g. SR id: `responsibility` may be restricted to that SR's admin group). The Guide's sample URL spells it `entityid`. |
| `entityType` | Optional, numeric. For `sr`: the `sr_type` id. For `ci`: the CI type id (e.g. to get CI sub-types). |
| `fields` | `id`, `caption`, `values`. |
| `key` | Optional. For user/group lists: `id` (default) or `name` as each value's key. |
| `offset`, `limit` | Standard. |

Example: `GET /list/responsibility?entity=sr&entityId=6`

---

## 10. Add-ons

### 10.1 List Add-ons
`GET /addons` — no parameters.

Each add-on: `name`, `title`, `description`, `logoFileName`, `version`, `addonType`, `link`, `linkText` (optional), `active` (bool), `implemented` (bool; non-implemented add-ons are delivered through Professional Services), `params` (always `null` in the list).

### 10.2 Get Add-on Parameters
`GET /addons/{addon name}` — e.g. `/addons/bomgar`

Returns the add-on plus `params[]`:

| Field | Description |
|---|---|
| `params.name` | Parameter name |
| `params.description` | Description |
| `params.value` | Current value |
| `params.type` | Parameter type |
| `params.mandatory` | Required? |
| `params.editable` | Editable? |
| `params.encrypted` | Masked like a password field |

### 10.3 Update Add-on Parameters
`PUT /addon/{addon name}` (note: **singular** `addon` in the Help index; the list/get use plural `addons`)

Only `active` and `params[].value` are updated; other changes are ignored.

```json
{
  "name": "bomgar",
  "active": true,
  "params": [
    { "name": "bomgar_url", "value": "https://sysaid.bomgar.com" },
    { "name": "bomgar_user_name", "value": "MyUserName" },
    { "name": "bomgar_password", "value": "MyPassword" }
  ]
}
```
Returns an HTTP header with a success message or error text.

### 10.4 Test Add-on Connection
`PUT /addon/{addon name}/testConnection` — same payload as update; only tests, doesn't save. Returns an HTTP header with a success message or error text.

### 10.5 Refresh Add-ons List
`GET /addons/refresh` — no params. Refreshes immediately; returns a message and success status.

---

## 11. CIs (Configuration Items)

### 11.1 Get CI List/Form
`GET /ci?view=&fields=&ids=&offset=&limit=&sort=&dir=&{filter}={value}&supportBarcode={true|false}`

| Param | Description |
|---|---|
| `view`, `fields` | As usual (all CI fields if none). |
| `ids` | Comma-separated CI ids. |
| `offset`, `limit` | Default 0 / 500 (config: `serverConf>apiConf>maxChunkSize`). |
| `sort`, `dir` | Standard. |
| `{filters}` | Dynamic filters. Dates in ms (see [Dates](#dates)). |
| `supportBarcode` | Flag: CI supports barcodes. |

Returns `[ { id, info[] } ]` where each info item has `key`, `keyCaption`, `value`, `valueCaption`, `mandatory`, `editable`, `defaultValue`, `type`.
The sample path in the Guide is `/ci/barcode?view=SysAidMobile&fields=ci_name,location&limit=2` (**⚠ Doc gap**: `/ci/barcode` isn't listed in the index).

### 11.2 Update CI
`PUT /ci/{id}`

```json
{
  "id": "273",
  "info": [
    { "key": "accept_date", "value": 1391756438000 },
    { "key": "status", "value": 2 },
    { "key": "owner", "value": "sysaid" }
  ]
}
```
(The sample writes the owner as `{"owner":"sysaid"}`; use key/value.) Only send changed fields.

### 11.3 Get CI Types
`GET /ci/type?supportBarcode={true|false}` (the Guide names the param `barcode`; the Help index says `supportBarcode`. **⚠ Doc gap**)

```json
[
  { "id": "1", "name": "Asset", "description": "System Asset (Workstation,Server,Laptop,Printer,PDA,Other)", "predefined": "true" },
  { "id": "6", "name": "Business Process", "description": "", "predefined": "false" }
]
```

### 11.4 Get CI View
`GET /ci/view/{ciTypeId}?view={view_name}`

Returns the list of fields (with `key`, `keyCaption`, `value`, `valueCaption`, `mandatory`, `editable`, `type`, `defaultValue`, `displayOrder`) in a view for a CI type. The `id` field is always included (at the end if not part of the view).

Example: `GET /ci/view/180?view=barcode_book`

### 11.5 Get CI Relation Types
`GET /ci/relationtypes`

```json
[
  { "relationTypeId": 5, "relationName": "Accessed by", "oppositeRelationName": "Can access" },
  { "relationTypeId": 4, "relationName": "Connected to", "oppositeRelationName": "Connected to" }
]
```

### 11.6 Get CI Relations
`GET /ci/{ciId}/relation` (the Help index writes `/ci/relation`; the Guide's sample is `/ci/9/relation` → use the latter)

```json
[ { "src": 9, "dest": 1, "ciRelationType": 2 }, { "src": 9, "dest": 2, "ciRelationType": 3 } ]
```

### 11.7 Create CI Relations
`POST /ci/{ciId}/relation`

Body: array of `{ "dest": <CI id>, "ciRelationType": <relation type id> }`.

```json
[ { "dest": 2, "ciRelationType": 3 }, { "dest": 1, "ciRelationType": 2 } ]
```
- Returns `OK` if all were created **or already exist** (no duplicates).
- If any fail → HTTP 400 with a message listing the failures (CSV-parsable):
  `{"status":400,"message":"Ci:9 Invalid CI id 100,Ci:9 Invalid CI Relation type 11"}`

### 11.8 Delete CI Relations
`DELETE /ci/{ciId}/relation` — same body as create (array of `{dest, ciRelationType}`).

Always returns `OK` (unless not logged in/unauthorized), even for non-existent relations.

---

## 12. Resource Bundle (RB)

Translate resource-bundle keys. Both calls are **POST** with the keys in the body.

### 12.1 Get RB Translated Keys (account locale)
`POST /rb`

Body: `[ { "key": "dir" } ]`
Response: `[ { "key": "dir", "value": "LTR" } ]`

### 12.2 Get RB Translated Keys (given locale)
`POST /rb/{locale}`

Same body/response, translated for `{locale}`.

---

## 13. Password Services (PS)

Self-service unlock/reset flow. These calls are meant for end users (not necessarily logged in).

### 13.1 Get LDAP Domains
`GET /ps/domain` → `["ILIENT-HQ","PM-TEST","QA-LAB"]`

### 13.2 Get PS Permissions
`GET /ps/permission`

```json
{ "enableUserSelfServices": true, "enableUnlockAccount": true, "enableResetPassword": true,
  "enableLdapSupport": true, "enableUserReset": false }
```
`enableUserReset` = true when the reset method is `user`.

### 13.3 Get Security Questions
`POST /ps/{method}/question` where `{method}` = `reset` or `unlock`.

Body:
```json
{ "userName": "test11", "domainName": "QA-LAB" }
```
Response:
```json
{ "userRefId": 842, "userId": "QA-LAB\\test11",
  "userSecurityQuestionsList": [ {"id":1,"question":"In which city were you born?"}, {"id":2,"question":"In which state were you born?"} ],
  "enableCaptcha": true }
```
Keep `userRefId` for the next step.

### 13.4 Unlock Account
`POST /ps/unlock`

```json
{ "userRefId": 842,
  "userSecurityQuestionsList": [ {"id":1,"question":"In which city were you born?","answer":"…"} ] }
```
Response: `{ "actionMessage": "Unlock user account succeeded! ..." }`

### 13.5 Reset Password
`POST /ps/reset`

Same body as unlock. Response depends on the configured reset method:

- **email / sms**: `{ "actionMessage": "...", "settings": { "temporaryPasswordValidity": 20, "resetPasswordMethod": "email" } }` — a temporary password (valid 20 min in the example) is sent.
- **user**: `{ "policy": { "complexity": true, "minLength": 7, "historyLength": 24 }, "token": "9f56…" }` — then call Update Password with the one-time `token`.

### 13.6 Update Password
`POST /ps/reset/update`

```json
{ "userRefId": 842, "newPassword": "NewPass#123", "token": "9f5641643c7f49b9920823ba18381a05" }
```
Response: `{ "actionMessage": "Reset user password succeeded!" }`

**Flow:** `GET /ps/permission` → `POST /ps/{method}/question` → `POST /ps/unlock` **or** `POST /ps/reset` (→ `POST /ps/reset/update` if method=`user`).

---

## 14. Reports

### 14.1 Report Field Operators
`GET /reports/operators?type={data_type}`

`type` is optional (`string`, `date`, `int`, …); without it, all operators are returned grouped by type.

```json
[ { "type": "date", "operator": "between", "sqlOperator": "between", "orderOfAppearance": 1 },
  { "type": "string", "operator": "Contains", "sqlOperator": "like '%?%'", "orderOfAppearance": 1 } ]
```

### 14.2 Run Preview
`POST /reports/allReports/{id}/runPreview` — runs a report in preview mode (partial data, limited by the records-limit configuration).

Body sections:

| Section | Contents |
|---|---|
| `entity` | Report entity, e.g. `"sr"` |
| `select.reportSelect[]` | Columns: `index`, `entityName`, `dbFieldName`, `caption`, `dataType`, `path`, `sort` (bool), `groupBy` (int; `-1`/none = no grouping) |
| `filter.basicFilter` / `filter.advancedFilter` | `state`, `formula`, `lockedFormula`, `filtersList[]` |
| `filter.*.filtersList[]` | `index`, `uid`, `entityName`, `dbFieldName`, `caption`, `dataType`, `path`, `entityReference`, `value`, `operator`, `locked` |
| `layout.previewLayout` | `type`, `groupBy`, `chartData`, `list`, `chartPosition`, `chartSize`, `chartDirection`, `aggregation` (Sum/Average), `aggregatedBy`, `trendField`, `trendPer`, `stackField`, `otherThreshold`, `other` |
| `layout.paperLayout` | `outputFormat` (pdf/excel), `orientation` (portrait/landscape), `details`, `cover.isCoverActive`, `header.isHeaderActive` + `header.contents[]`, `footer.isFooterActive` + `footer.contents[]` (items: `align`, `contentType`, `value`) |

Minimal example (columns + one filter):
```json
{
  "entity": "sr",
  "select": { "reportSelect": [
    { "index": 1, "entityName": "sr",   "dbFieldName": "title",      "caption": "Title",      "dataType": "string", "path": "sr.title" },
    { "index": 2, "entityName": "user", "dbFieldName": "first_name", "caption": "First Name", "dataType": "string", "path": "sr.submit_user:user.first_name" } ] },
  "filter": { "basicFilter": {
    "filtersList": [ { "index": 1, "value": "a@b.com", "operator": "=", "entityName": "user",
                       "dbFieldName": "email_address", "dataType": "string", "path": "sr.submit_user:user.email_address" } ],
    "formula": "1", "state": 0 } }
}
```
Paths follow `entity.fk_field:relatedEntity.field`. **⚠ Doc gap:** the sample return for `/reports/allReports/72/runPreview` is empty, and the Guide's return table is a copy of the operators table.

---

## 15. Non-resource calls

Calls that return something other than a plain resource. Both are incomplete in the Guide. **⚠ Doc gap**

- **Download File** — takes `file` (URL of the file), e.g. to download a user's photo. Return is "TBD", and no HTTP path is given.
- **Translate Key** — takes `key` (string key from the SysAid resources file) and `language`. Returns `{ "key": "welcome", "value": "Bienvenue" }`. No HTTP path is given. See `POST /rb` and `POST /rb/{locale}` for the documented translation endpoints.

---

## 16. Appendices

### Appendix A — Field types
Appear in `info.type`:

| Type | Description |
|---|---|
| `text` | Text value |
| `numeric` | Number |
| `boolean` | `0/1` or `true/false` |
| `date` | ms since epoch UTC; `valueCaption` is the formatted date per SysAid's date config |
| `list` | Value from a list; full list from `GET /list/{id}` |
| `nested` | Item in a nested list (currently category levels) |
| `object` | Object with sub-values |
| `custom` | "TBD" in the docs |

### Appendix B — List entities
Use as `entity=` in `/list` calls:

| Entity | Contents |
|---|---|
| `sr` | Service-record lists |
| `asset` | Asset lists |
| `user` | User lists |
| `ci` | CI lists |
| `company` | Company lists |
| `action_item` | Action-item lists |
| `project` | SR sub-tab lists |
| `task` | Task lists |
| `catalog` | Catalog lists |
| `software` | Software lists |
| `sr_activity` | SR activity lists |
| `supplier` | Supplier lists |
| `task_activity` | Task activity lists |
| `user_groups` | User group lists |

---

## 17. Documentation gaps and inconsistencies

1. **Login body format** is not specified (JSON vs form vs query).
2. **Consumer-key creation** for OAuth isn't explained.
3. **HTTP methods and paths** come only from the Help index. The Guide has none; its section anchors and sample captions only partially show them.
4. **Get/Download User's Photo:** only in the index. The Guide's "Download File" is TBD.
5. **Get CI Relation path:** index says `/ci/relation`, the sample says `/ci/9/relation`.
6. **Add-ons:** list/get use `/addons`, update/test use `/addon` (singular).
7. **CI types param:** `barcode` (Guide) vs `supportBarcode` (index).
8. **`/ci/barcode`** appears in a sample but not in the index.
9. **`GET /asset`:** index lists a `type` param that the Guide doesn't describe.
10. **Sample JSON typos:** `{"responsibility":66}` and `{"owner":"sysaid"}` aren't in key/value form; missing commas; mixed typographic quotes.
11. **Attachment upload** part name isn't stated.
12. **Action Items** have no sample for the state-change calls (approve/reject/complete/reopen) and no payload is documented.
13. **Reports:** `runPreview` sample return is empty.
14. **Non-resource calls** (Download File, Translate Key) lack paths and return details.
15. **Error format:** only seen once (CI relations: `{"status":400,"message":"..."}`). Other errors aren't documented.
16. **Asset key names:** assets use `key_caption`/`value_caption`; other entities use `keyCaption`/`valueCaption`.
17. **`limit` default (500)** is configurable per server, so real behavior may differ.
18. The Guide's Service Request Form section appears twice (duplicated text, same content).

---

## 18. Quick reference — all endpoints

| Area | Method | Path | Purpose |
|---|---|---|---|
| OAuth | POST | `/oauth/request_token` | Get request token |
| OAuth | GET | `/oauth/authorize` | User authorization (redirect) |
| OAuth | POST | `/oauth/access_token` | Get access token |
| Login | POST | `/login` | Authenticate (session cookie) |
| Users | GET | `/users` | List users |
| Users | GET | `/users/{id}` | Get user |
| Users | GET | `/users/search` | Search users |
| Users | GET | `/users/{id}/photo` | Download photo |
| Users | POST | `/users/{id}/photo` | Upload photo (≤500KB) |
| Users | GET | `/users/{id}/permission` | All permissions |
| Users | GET | `/users/{id}/permission/{permissionId}` | One permission |
| Filters | GET | `/filters` | List filters |
| Filters | GET | `/filters/{id}` | Get filter |
| SR | GET | `/sr` | List SRs |
| SR | GET | `/sr/{id}` | Get SR |
| SR | GET | `/sr/search` | Search SRs |
| SR | PUT | `/sr/{id}` | Update SR |
| SR | GET | `/sr/count` | Count SRs |
| SR | PUT | `/sr/{id}/close` | Close SR |
| SR | GET | `/sr/template` | New-SR template |
| SR | POST | `/sr` | Create SR |
| SR | DELETE | `/sr?ids=` | Delete SR(s) |
| SR | POST | `/sr/{id}/link` | Add link |
| SR | DELETE | `/sr/{id}/link` | Delete link |
| SR | POST | `/sr/{id}/attachment` | Add attachment |
| SR | DELETE | `/sr/{id}/attachment` | Delete attachment |
| SR | POST | `/sr/{id}/activity` | Add activity |
| SR | DELETE | `/sr/{id}/activity` | Delete activity |
| SR | POST | `/sr/{id}/message` | Send message |
| Action items | GET | `/action_item` | List |
| Action items | GET | `/action_item/count` | Count |
| Action items | PUT | `/action_item/{id}/approve` | Approve |
| Action items | PUT | `/action_item/{id}/reject` | Reject |
| Action items | PUT | `/action_item/{id}/complete` | Complete |
| Action items | PUT | `/action_item/{id}/reopen` | Reopen |
| Assets | GET | `/asset` | List assets |
| Assets | GET | `/asset/{id}` | Get asset |
| Assets | GET | `/asset/search` | Search assets |
| Lists | GET | `/list` | All lists |
| Lists | GET | `/list/{id}` | One list |
| Add-ons | GET | `/addons` | List add-ons |
| Add-ons | GET | `/addons/{name}` | Get add-on + params |
| Add-ons | PUT | `/addon/{name}` | Update add-on |
| Add-ons | PUT | `/addon/{name}/testConnection` | Test add-on |
| Add-ons | GET | `/addons/refresh` | Refresh list |
| CIs | GET | `/ci` | List CIs |
| CIs | PUT | `/ci/{id}` | Update CI |
| CIs | GET | `/ci/type` | CI types |
| CIs | GET | `/ci/view/{ciTypeId}` | CI view fields |
| CIs | GET | `/ci/relationtypes` | Relation types |
| CIs | GET | `/ci/{ciId}/relation` | Get relations |
| CIs | POST | `/ci/{ciId}/relation` | Create relations |
| CIs | DELETE | `/ci/{ciId}/relation` | Delete relations |
| RB | POST | `/rb` | Translate keys |
| RB | POST | `/rb/{locale}` | Translate keys (locale) |
| PS | GET | `/ps/domain` | LDAP domains |
| PS | GET | `/ps/permission` | PS permissions |
| PS | POST | `/ps/{method}/question` | Security questions |
| PS | POST | `/ps/unlock` | Unlock account |
| PS | POST | `/ps/reset` | Reset password |
| PS | POST | `/ps/reset/update` | Set new password |
| Reports | GET | `/reports/operators` | Field operators |
| Reports | POST | `/reports/allReports/{id}/runPreview` | Run preview |
