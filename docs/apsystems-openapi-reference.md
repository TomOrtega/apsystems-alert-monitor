# APsystems OpenAPI - Installer API reference

Source: **APsystems OpenAPI User Manual, version 1.8, dated 2025-07-18**.

This is a cleaned, machine-readable reference prepared from the official PDF. It is not an official OpenAPI/Swagger specification. When the PDF is ambiguous or internally inconsistent, this file marks the issue explicitly instead of guessing.

The endpoint paths, methods, parameter names, documented response fields, status values, plans, and response codes have been checked against all 38 pages of the source manual. Examples labelled **normalized illustration** are reconstructed from the documented fields because the PDF sometimes contains incomplete or malformed JSON examples.

External findings are kept in `docs/apsystems-additional-research.md`. In this reference, externally supported notes are labelled **Additional information** and cite source IDs from that file; they do not overwrite the supplied installer manual.

### Manual revision history

| Version | Date | Documented change |
|---|---|---|
| V1.0 | 2022-09-16 | First document |
| V1.1 | 2023-03-24 | Token URL edited; refresh-token expiration changed |
| V1.2 | 2023-10-07 | JWT-token authentication changed to signature authentication |
| V1.3 | 2023-10-31 | Meter interface added |
| V1.4 | 2023-11-17 | No description given |
| V1.5 | 2023-11-17 | Inverter-level data API added |
| V1.6 | 2024-02-07 | Installer interface optimized |
| V1.6 | 2025-03-17 | Base URL and third-party integration instructions added |
| V1.7 | 2025-04-17 | Storage-level data API added |
| V1.8 | 2025-07-18 | Shared sub-user system support added |

The duplicate `V1.6` entry is present in the source manual. The overview page still says there are five API categories even though later revisions also document storage and third-party integration.

## 1. Scope

The API is REST over HTTPS and returns JSON. The manual documents these groups:

- System details
- System-level data
- ECU-level data
- Meter-level data
- Inverter-level data
- Storage-level data
- Third-party integration

## 2. Access and authentication

### 2.1 Registration

Request an OpenAPI account from APsystems support. The application should state:

- Who you are
- Why you need an OpenAPI account
- What you will do with the data

After approval, APsystems supplies:

- `App Id`: alphanumeric identifier described by the manual as a "32-bit string"; the wording and examples indicate a 32-character value
- `App Secret`: alphanumeric secret described as a "12-bit string"; the wording appears to mean 12 characters

Keep both confidential. The manual's App Secret description still mentions access/refresh tokens, but its revision history says installer authentication changed from JWT tokens to per-request signatures in V1.2. Do not introduce a token flow for the installer endpoints unless APsystems supplies additional documentation.

### 2.2 Base URL

```text
https://api.apsystemsema.com:9282
```

The supplied installer manual uses the `/installer/api/v2` prefix throughout.

> **Additional information — profile distinction:** a separate vendor-branded end-user V1.8 manual and working community clients use `/user/api/v2`. Treat `installer` and `end_user` as explicit API profiles; never silently swap prefixes after an error. Source: `SRC-ENDUSER-MANUAL`, `SRC-HOMEY`, and `SRC-GITHUB-OPENAPI`.

### 2.3 Required request headers

Every request requires:

| Header | Type | Meaning |
|---|---|---|
| `X-CA-AppId` | string | OpenAPI application ID |
| `X-CA-Timestamp` | string | Request timestamp |
| `X-CA-Nonce` | string | UUID-like 32-character nonce |
| `X-CA-Signature-Method` | string | `HmacSHA256` or `HmacSHA1` |
| `X-CA-Signature` | string | Base64-encoded signature |

The manual does not specify the exact timestamp format or unit.

> **Additional information — community validated:** multiple working `/user` clients use Unix epoch milliseconds encoded as a decimal string. Use milliseconds as the default encoder, but keep it replaceable until a successful `/installer` request validates it. Accepted clock skew remains unknown. Sources: `SRC-HOMEY`, `SRC-GITHUB-OPENAPI`, `SRC-MATTHIJS` in `apsystems-additional-research.md`.

### 2.4 Signature construction

Inputs:

- HTTP method: `GET`, `POST`, or `DELETE`
- Headers: `X-CA-AppId`, `X-CA-Timestamp`, `X-CA-Nonce`, `X-CA-Signature-Method`
- `RequestPath`: the last segment of the path, according to the manual

Construct:

```text
stringToSign =
  X-CA-Timestamp + "/" +
  X-CA-Nonce + "/" +
  X-CA-AppId + "/" +
  RequestPath + "/" +
  HTTPMethod + "/" +
  X-CA-Signature-Method
```

Then calculate HMAC using the App Secret and Base64-encode the raw result. The Java example in the manual uses UTF-8 for both secret and message. Its local byte-array variable is misleadingly named `md5Result`, but the operation shown is HMAC-SHA256 or HMAC-SHA1, not MD5.

Prefer `HmacSHA256` unless APsystems instructs otherwise. No official test vector is provided, so a successful real request is required to validate the implementation.

> **Additional information — unresolved conflict:** successful community clients commonly sign the final concrete path segment, usually an ID. A separate 2026 implementation reports operation-name segments for some `/user` routes. Implement the signature component as a per-endpoint/profile strategy and validate it with a bounded test. Do not assume one community behavior applies to the installer API. Sources: `SRC-HOMEY`, `SRC-GITHUB-OPENAPI`, `SRC-MATTHIJS`.

### 2.5 Request serialization and HTTP behavior

The manual does not state:

- the timestamp unit/format or allowed clock skew
- whether POST parameters are JSON body, form data, or query parameters
- the required POST `Content-Type`
- whether query parameters or the complete path participate in signing
- the mapping between API `code` values and HTTP status codes

> **Additional information — community validated for GET:** working clients send `energy_level`, `date_range`, and similar values in the URL query string and exclude the query string from the HMAC input. Use that as the GET default. POST serialization remains unresolved. Sources: `SRC-HOMEY`, `SRC-GITHUB-OPENAPI`, `SRC-MATTHIJS`.

> **Additional information — defensive response parsing:** community implementations show HTTP 200 with non-zero JSON `code`, and one maintained client reports valid JSON with an unexpected MIME type such as `application/octet-stream`. Validate transport status and JSON `code` separately, and parse bounded JSON-like bodies defensively. Sources: `SRC-HOMEY`, `SRC-GITHUB-OPENAPI`.

### 2.6 Authorization scope

The manual says an approved application can access default data and can choose a category corresponding to its business. It does not define the category names, scope model, or which plan unlocks which data range. Therefore, a valid App ID may still receive `2002` (not authorized) or `2004` (no permission) for particular endpoints.

### 2.7 Monthly request plans in the manual

| Level | Monthly requests | USD price | EUR price |
|---|---:|---:|---:|
| Lv0 | 1,000 | Free | Free |
| Lv1 | 100,000 | USD 27/month or USD 269/year | EUR 25/month or EUR 249/year |
| Lv2 | 500,000 | USD 54/month or USD 539/year | EUR 50/month or EUR 499/year |
| Lv3 | 1,000,000 | USD 76/month or USD 755/year | EUR 70/month or EUR 699/year |

Treat pricing as historical documentation and confirm current commercial terms with APsystems.

---

## 3. Identifier model

| Identifier | Meaning |
|---|---|
| `sid` | System ID |
| `eid` | ECU ID, Meter ECU ID, or Storage ECU ID depending on endpoint |
| `uid` | Inverter ID |

For a shared sub-user system, the systems response may show an ECU value like:

```text
2030000001236-002405253708
```

The manual says the part before `-` is the main-user ECU and the part after `-` is the virtual ECU. Subsequent data queries must use the virtual ECU number as `eid`.

---

## 4. Endpoint index

### System details

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/installer/api/v2/systems` | List accessible systems |
| `GET` | `/installer/api/v2/systems/details/{sid}` | Get one system |
| `GET` | `/installer/api/v2/systems/inverters/{sid}` | List ECUs and inverters in a system |
| `GET` | `/installer/api/v2/systems/meters/{sid}` | List meter ECU IDs |
| `GET` | `/installer/api/v2/systems/storages/{sid}` | List storage ECU IDs |
| `POST` | `/installer/api/v2/partnerSystems` | List accessible partner systems |

### System-level data

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/installer/api/v2/systems/summary/{sid}` | System energy summary |
| `GET` | `/installer/api/v2/systems/energy/{sid}` | System energy by period |

### ECU-level data

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/installer/api/v2/systems/{sid}/devices/ecu/summary/{eid}` | ECU energy summary |
| `GET` | `/installer/api/v2/systems/{sid}/devices/ecu/energy/{eid}` | ECU power and energy by period |

### Meter-level data

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/installer/api/v2/systems/{sid}/devices/meter/summary/{eid}` | Meter energy summary |
| `GET` | `/installer/api/v2/systems/{sid}/devices/meter/period/{eid}` | Meter power and energy by period |

### Inverter-level data

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/installer/api/v2/systems/{sid}/devices/inverter/summary/{uid}` | Inverter energy summary per channel |
| `GET` | `/installer/api/v2/systems/{sid}/devices/inverter/energy/{uid}` | Detailed inverter telemetry per channel |
| `GET` | `/installer/api/v2/systems/{sid}/devices/inverter/batch/energy/{eid}` | Batch power or daily energy for all inverter channels below an ECU |

### Storage-level data

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/installer/api/v2/systems/{sid}/devices/storage/latest/{eid}` | Latest storage status and power |
| `GET` | `/installer/api/v2/systems/{sid}/devices/storage/summary/{eid}` | Storage energy summary |
| `GET` | `/installer/api/v2/systems/{sid}/devices/storage/period/{eid}` | Storage power and energy by period |

### Third-party integration

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/installer/api/v2/getSystemsByToken` | Get systems authorized by an end user |

---

## 5. System details endpoints

## 5.1 List systems

```http
POST /installer/api/v2/systems
```

Request parameters (the manual does not explicitly state whether these are JSON-body, form, or query parameters for the POST request):

| Parameter | Required | Type | Notes |
|---|---:|---|---|
| `page` | no | integer | Default 1, minimum 1 |
| `size` | no | integer | Allowed/documented values: 10, 20, 50 |
| `sort` | no | string | Fields documented: `sid`, `username`, `create_date`; prefix `-` for descending |
| `query` | no | object | Filter using supported system fields; manual says three query fields are supported but does not identify all three clearly |

Example body:

```json
{
  "page": 1,
  "size": 50,
  "sort": "sid",
  "query": {
    "sid": "AZ02849ADDFC",
    "type": 1
  }
}
```

Response:

```json
{
  "data": {
    "total": 200,
    "page": 1,
    "size": 10,
    "systems": [
      {
        "sid": "AZ02849ADDFC",
        "create_date": "2022-09-01",
        "capacity": "2.38",
        "type": 1,
        "timezone": "Asia/Shanghai",
        "ecu": ["203000001234"],
        "light": 1,
        "authorization_code": "..."
      }
    ]
  },
  "code": 0
}
```

System fields:

| Field | Type | Meaning |
|---|---|---|
| `sid` | string | System ID |
| `create_date` | `yyyy-MM-dd` string | EMA registration date |
| `capacity` | numeric string | System size, default unit kW |
| `type` | integer | 1 PV, 2 storage, 3 PV plus storage |
| `timezone` | string | ECU timezone |
| `ecu` | string[] | ECU IDs |
| `light` | integer | System health/status light |
| `authorization_code` | string | Optional visitor/embedded-site authorization code |

`light` values:

| Value | Colour | Meaning |
|---:|---|---|
| 1 | Green | System functioning normally |
| 2 | Yellow | One or more microinverters have alarms or are not correctly registered |
| 3 | Red | ECU network connection issue detected |
| 4 | Grey | No data has yet been uploaded from the ECU |

Important limitation: the API does not document which inverter or alarm caused `light = 2`.

### Visitor/embedded-system authorization code

The manual says `authorization_code` is generated after enabling **Allow visitors to access this system** on the **PERSONAL INFO** page of **ACCOUNT Details**. It provides this embed pattern:

```html
<iframe
  id="frame1"
  width="100%"
  height="100%"
  frameborder="0"
  src="https://www.apsystemsema.com/ema/intoDemoUser.action?id={authorization_code}&locale=en_US">
</iframe>
```

Treat the authorization code as an access-bearing token. Do not expose it unintentionally in logs, analytics, or public source code. This iframe mechanism is separate from OpenAPI request authentication.

## 5.2 Get one system

```http
GET /installer/api/v2/systems/details/{sid}
```

Returns the same main fields as a list-system item:

- `sid`
- `create_date`
- `capacity`
- `type`
- `timezone`
- `ecu`
- `light`
- `authorization_code`

## 5.3 List ECUs and inverters

```http
GET /installer/api/v2/systems/inverters/{sid}
```

Response example:

```json
{
  "data": [
    {
      "eid": "203000001234",
      "type": 0,
      "timezone": "Asia/Shanghai",
      "inverter": [
        { "uid": "902000001234", "type": "QT2D" },
        { "uid": "902000001235", "type": "QT2D" }
      ]
    }
  ],
  "code": 0
}
```

ECU `type`:

| Value | Meaning |
|---:|---|
| 0 | ECU |
| 1 | ECU with meter activated |
| 2 | ECU with storage activated |

The response model also mentions `model` and `capacity` for a storage-activated ECU, with capacity in kWh, although they are absent from the example.

## 5.4 List meters

```http
GET /installer/api/v2/systems/meters/{sid}
```

Response data is a list of meter ECU IDs:

```json
{
  "data": ["203000001234"],
  "code": 0
}
```

## 5.5 List storages

```http
GET /installer/api/v2/systems/storages/{sid}
```

Response data is a list of storage ECU IDs:

```json
{
  "data": ["203000001234"],
  "code": 0
}
```

## 5.6 List partner systems

```http
POST /installer/api/v2/partnerSystems
```

Pagination, sorting, and query parameters are the same shape as `/systems`.

Documented system fields:

- `sid`
- `create_date`
- `capacity`
- `type`
- `timezone`
- `ecu`

The example does not include `light` or `authorization_code` for partner systems.

---

## 6. Common energy query model

Several endpoints accept:

| `energy_level` | `date_range` format | Typical result |
|---|---|---|
| `minutely` | `yyyy-MM-dd` | Irregular time points with power and/or energy |
| `hourly` | `yyyy-MM-dd` | 24 values |
| `daily` | `yyyy-MM` | Number of values equals days in month |
| `monthly` | `yyyy` | 12 values |
| `yearly` | omitted | One value per year since installation |

The manual repeatedly says future `date_range` values are rejected. It does not explicitly state the timezone used to decide what counts as "today" or a future date. The safest implementation is to use the system/ECU `timezone`, while keeping this behavior configurable until confirmed.

Index semantics for array-only responses:

- hourly index `0..23` corresponds to hours `00..23`
- daily index `0..N-1` corresponds to days `1..N` of the requested month
- monthly index `0..11` corresponds to months `1..12`
- yearly returns one value per year since installation, but the response does not include year labels; do not assume the first year without checking installation/registration metadata

Important: the manual calls the level `minutely`, but does not guarantee one data point per minute. Treat timestamps as irregular samples and inspect actual returned `time` arrays. For `HH:mm`-only timestamps, combine the time with the requested `date_range` and plant timezone, and handle midnight carefully.

---

## 7. System-level energy

## 7.1 System summary

```http
GET /installer/api/v2/systems/summary/{sid}
```

Response, unit kWh:

```json
{
  "data": {
    "today": "12.28",
    "month": "12.28",
    "year": "12.28",
    "lifetime": "12.28"
  },
  "code": 0
}
```

## 7.2 System energy by period

```http
GET /installer/api/v2/systems/energy/{sid}
```

Parameters:

- `energy_level`: `hourly`, `daily`, `monthly`, or `yearly`
- `date_range`: format depends on level

The system-level endpoint does not document `minutely`.

Response data is a numeric-string array in kWh.

---

## 8. ECU-level energy and power

## 8.1 ECU summary

```http
GET /installer/api/v2/systems/{sid}/devices/ecu/summary/{eid}
```

Response fields, unit kWh:

- `today`
- `month`
- `year`
- `lifetime`

## 8.2 ECU energy by period

```http
GET /installer/api/v2/systems/{sid}/devices/ecu/energy/{eid}
```

Parameters:

- `energy_level`: `minutely`, `hourly`, `daily`, `monthly`, `yearly`
- `date_range`: as described in the common energy model

For `hourly`, `daily`, `monthly`, and `yearly`, response data is an array of energy values in kWh.

For `minutely`, response data is an object. **Normalized illustration:**

```json
{
  "data": {
    "time": ["10:00", "10:05"],
    "energy": ["2.14", "2.22"],
    "power": ["1840", "1965"],
    "today": "2.22"
  },
  "code": 0
}
```

Units:

- `energy`: kWh
- `power`: W
- `today`: kWh

---

## 9. Meter-level data

## 9.1 Meter summary

```http
GET /installer/api/v2/systems/{sid}/devices/meter/summary/{eid}
```

For each of `today`, `month`, `year`, and `lifetime`, the response contains:

| Field | Meaning |
|---|---|
| `consumed` | Energy consumed |
| `exported` | Energy exported to grid |
| `imported` | Energy imported from grid |
| `produced` | Energy produced |

Example:

```json
{
  "code": 0,
  "data": {
    "today": {
      "consumed": "394.408090",
      "exported": "0.000000",
      "imported": "560.523540",
      "produced": "833.884550"
    },
    "month": {},
    "year": {},
    "lifetime": {}
  }
}
```

The context and period endpoints indicate energy units are kWh.

## 9.2 Meter data by period

```http
GET /installer/api/v2/systems/{sid}/devices/meter/period/{eid}
```

Parameters:

- `energy_level`: `minutely`, `hourly`, `daily`, `monthly`, `yearly`
- `date_range`: as described in the common energy model

For `hourly`, `daily`, `monthly`, and `yearly`, the response is an object with aligned arrays:

```json
{
  "code": 0,
  "data": {
    "time": ["01", "02"],
    "produced": ["40.300", "50.016"],
    "consumed": ["40.300", "50.016"],
    "imported": ["40.300", "50.016"],
    "exported": ["40.300", "50.016"]
  }
}
```

Energy unit: kWh.

For `minutely`:

```json
{
  "code": 0,
  "data": {
    "today": {
      "consumed": "5.996600",
      "exported": "0.071860",
      "imported": "3.712280",
      "produced": "2.356180"
    },
    "time": ["23:57"],
    "power": {
      "consumed": ["167.96"],
      "imported_exported": ["167.96"],
      "produced": ["0.00"]
    },
    "energy": {
      "consumed": ["0.015620"],
      "exported": ["0"],
      "imported": ["0.01562"],
      "produced": ["0.00000"]
    }
  }
}
```

Units:

- `power.*`: W
- `energy.*`: kWh
- `today.*`: kWh

The field `imported_exported` represents a signed or combined grid-flow channel in the example, but the manual does not document its sign convention. Validate with real data before interpreting positive/negative direction. The summary and period examples imply kWh for energy, but the summary section itself does not explicitly print units.

---

## 10. Inverter-level data

## 10.1 Inverter summary per channel

```http
GET /installer/api/v2/systems/{sid}/devices/inverter/summary/{uid}
```

The response may include up to four channels:

```json
{
  "data": {
    "d1": "12.28", "m1": "12.28", "y1": "12.28", "t1": "12.28",
    "d2": "12.28", "m2": "12.28", "y2": "12.28", "t2": "12.28",
    "d3": "12.28", "m3": "12.28", "y3": "12.28", "t3": "12.28",
    "d4": "12.28", "m4": "12.28", "y4": "12.28", "t4": "12.28"
  },
  "code": 0
}
```

Likely naming:

- `dN`: today for channel N
- `mN`: current month for channel N
- `yN`: current year for channel N
- `tN`: lifetime total for channel N

However, pages 25-27 contain obvious copy/paste errors in the field descriptions. Treat this naming interpretation as provisional until verified against APsystems or real values.

## 10.2 Detailed inverter telemetry

```http
GET /installer/api/v2/systems/{sid}/devices/inverter/energy/{uid}
```

Parameters:

- `energy_level`: `minutely`, `hourly`, `daily`, `monthly`, `yearly`
- `date_range`: as described in the common energy model

For non-minutely levels, response keys are per-channel energy arrays:

- `e1`
- `e2`
- `e3`
- `e4`

For `minutely`, documented arrays include:

### Time

- `t`: sample times in `HH:mm`

### DC values, per PV channel

- `dc_p1` ... `dc_p4`: DC power
- `dc_i1` ... `dc_i4`: DC current
- `dc_v1` ... `dc_v4`: DC voltage
- `dc_e1` ... `dc_e4`: DC energy

### AC values

- `ac_v1`, `ac_v2`, `ac_v3`: AC voltage channels/phases
- `ac_t`: AC/inverter temperature
- `ac_p`: AC power
- `ac_f`: AC frequency

The manual explicitly states W for the batch-power endpoint and identifies these as power/current/voltage/energy fields, but it does not consistently print units for every detailed inverter field. It also calls `data` a list while documenting named fields as though it were an object. Implement a tolerant decoder and do not hard-code undocumented units without verifying actual API data or APsystems support.

Channels that do not exist on a particular inverter model may be absent, empty, or null; the manual does not define this behavior. Determine active channel count from inventory/model and actual payloads rather than assuming four populated channels.

## 10.3 Batch inverter power or daily energy below one ECU

```http
GET /installer/api/v2/systems/{sid}/devices/inverter/batch/energy/{eid}
```

Required parameters:

| Parameter | Values/format |
|---|---|
| `energy_level` | `power` or `energy` |
| `date_range` | `yyyy-MM-dd` |

The prose has a typo saying `power` or `power`; the parameter table says `power` or `energy`.

For `energy`, the response contains strings formatted:

```text
uid-channel-energy
```

Example:

```text
701000001234-1-1.24
```

For `power`, the response contains:

- `time`: `HH:mm` samples
- `power`: map keyed by `uid-channel`, each value an array aligned with `time`

**Normalized illustration based on the documented shape:**

```json
{
  "data": {
    "time": ["10:00", "10:05", "10:10"],
    "power": {
      "701000001234-1": [45, 56, 78],
      "701000001234-2": [43, 55, 76]
    }
  },
  "code": 0
}
```

Power unit: W.

This is the preferred endpoint for regular fleet monitoring because one request returns every inverter channel below an ECU.

---

## 11. Storage-level data

## 11.1 Latest storage status

```http
GET /installer/api/v2/systems/{sid}/devices/storage/latest/{eid}
```

Response:

```json
{
  "data": {
    "mode": "4",
    "soc": "97",
    "time": "23:57",
    "discharge": "394.408",
    "charge": "0.000",
    "produced": "560.523",
    "consumed": "560.523",
    "exported": "560.523",
    "imported": "833.884"
  },
  "code": 0
}
```

Fields:

| Field | Meaning |
|---|---|
| `mode` | Storage operation mode |
| `soc` | Battery state of charge, percent |
| `time` | Time of latest sample; present in example but omitted from the descriptive field list |
| `discharge` | Latest discharge power |
| `charge` | Latest charge power |
| `produced` | Latest produced power |
| `consumed` | Latest consumed power |
| `exported` | Latest exported power |
| `imported` | Latest imported power |

The manual does not define the numeric meanings of `mode` and does not explicitly print units for the latest power fields. The example `time` contains only `HH:mm`, so it is not a complete timestamp. Confirm mode mappings, units, date association, and update cadence before using this endpoint for automation.

## 11.2 Storage summary

```http
GET /installer/api/v2/systems/{sid}/devices/storage/summary/{eid}
```

For each of `today`, `month`, `year`, and `lifetime`:

- `discharge`
- `charge`
- `produced`
- `consumed`
- `exported`
- `imported`

These are cumulative energy values; period endpoints identify energy unit as kWh.

## 11.3 Storage data by period

```http
GET /installer/api/v2/systems/{sid}/devices/storage/period/{eid}
```

Parameters:

- `energy_level`: `minutely`, `hourly`, `daily`, `monthly`, `yearly`
- `date_range`: as described in the common energy model

For non-minutely levels, aligned arrays:

- `time`
- `discharge`
- `charge`
- `produced`
- `consumed`
- `exported`
- `imported`

Energy unit: kWh.

For `minutely`:

- `today`: cumulative daily values
- `time`: `HH:mm` samples
- `power`: arrays for discharge, charge, produced, consumed, exported, imported; unit W
- `energy`: matching arrays; unit kWh

---

## 12. Third-party user authorization

```http
POST /installer/api/v2/getSystemsByToken
```

Body:

```json
{
  "token": "end-user-authorization-token"
}
```

The token expires after five minutes.

The response returns authorized end-user systems with:

- `sid`
- `create_date`
- `capacity`
- `type`
- `timezone`
- `ecu`
- `username`: EMA login account

The manual says the complete authorization flow is in a separate document named `Apsystems OpenAPI User Manual - Third-party Integration.pdf`, which is not part of this package. This endpoint alone is insufficient to implement end-user authorization because the process for obtaining the five-minute token is missing.

---

## 13. Documented operational/status fields

The manual exposes relatively few direct state fields. Most detailed monitoring must be derived from telemetry.

> **Additional information — official APsystems:** the public installer FAQ says yellow can also represent interrupted inverter communication since the start of the day or low/abnormal production/weak sunlight. Therefore `light = 2` is a broad triage warning rather than a precise fault code. Source: `SRC-APS-FAQ`.

| Scope | Direct field | What it tells you | What it does not tell you |
|---|---|---|---|
| System | `light` | Normal, inverter/registration warning, ECU network issue, or no uploaded data | Alarm code, affected inverter, start time, recovery time |
| ECU | `type` | Plain ECU, meter-enabled ECU, or storage-enabled ECU | Online/offline state or communication quality |
| Storage | `mode` | Opaque operation-mode value | Meaning of each mode code |
| Storage | `soc` | Battery state of charge in percent | State of health, cycles, cell details |
| Storage | `time` | Latest sample time as `HH:mm` in the example | Full date/time and timezone |
| Any response | `code` | API-level success/error category | Device alarm state |
| Minutely/period data | last item in `time` | Inferable data freshness | Explicit device `last_seen` |

The API does not document a standalone alarm/event endpoint. A monitoring application should store both the vendor-provided state and its own inferred state, and must label inferred diagnoses as such.

---

## 14. Response codes

| Code | Meaning |
|---:|---|
| 0 | Request succeeded |
| 1000 | Data exception |
| 1001 | No data |
| 2000 | Application account exception |
| 2001 | Invalid application account |
| 2002 | Application account not authorized |
| 2003 | Application account authorization expired |
| 2004 | Application account has no permission |
| 2005 | Application account access limit exceeded |
| 3000 | Access token exception |
| 3001 | Missing access token |
| 3002 | Unable to verify access token |
| 3003 | Access token timeout |
| 3004 | Refresh token timeout |
| 4000 | Request parameter exception |
| 4001 | Invalid request parameter |
| 5000 | Internal server exception |
| 6000 | Communication exception |
| 7000 | Server access restriction exception |
| 7001 | Server access limit exceeded |
| 7002 | Too many requests; retry later |
| 7003 | System busy; retry later |

Implementation guidance:

- Do not treat HTTP 2xx alone as success; inspect JSON `code`.
- Retry transient codes `5000`, `6000`, `7002`, and `7003` with exponential backoff and jitter.
- Do not retry authentication, permission, or invalid-parameter errors without corrective action.
- Treat `1001` as valid no-data state, not necessarily a transport failure.

---

## 15. Important gaps and ambiguities

The manual does **not** document endpoints for:

- Detailed active alarm list
- Alarm codes and descriptions
- Alarm start/end timestamps
- Historical events
- Explicit online/offline state per inverter
- Explicit `last_seen` per device
- ECU radio-signal quality
- Firmware versions
- Remote control commands
- Battery state of health or cycle count
- Irradiance or ambient temperature
- Webhooks/push events

Known documentation problems:

1. The exact `X-CA-Timestamp` format is not stated.
2. `RequestPath` is described as the last path segment, which should be verified because unusual signature rules are easy to misinterpret.
3. The inverter summary field descriptions contain copy/paste errors.
4. The batch inverter endpoint says `power` or `power` in prose, while its parameter table says `power` or `energy`.
5. Storage `mode` codes are not defined.
6. Some latest-power and detailed electrical units are not explicitly documented.
7. The meter field `imported_exported` lacks a sign convention.
8. The manual uses both `date_range` and misspelled `data_rage`/`date_rage` in prose; use `date_range`.
9. POST parameter serialization, required POST `Content-Type`, exact HTTP status behavior, and clock-skew tolerance are not documented. GET query-string behavior is externally validated but not stated in the installer manual.
10. Several period endpoints describe `data` as a list even though their examples show an object containing aligned arrays.
11. The batch endpoint says it returns "five levels" although only `power` and `energy` are documented.
12. The batch `power` field is called a list but its documented example shape is a map keyed by `uid-channel`.
13. Yearly array responses do not include explicit year labels.
14. The separate third-party integration document required to obtain the authorization token is absent.
15. The behavior of absent channels, null values, empty arrays, partial-day data, and duplicate samples is not defined.

Code should preserve unknown values, raw payloads, and unrecognized fields; avoid inventing enum mappings; and tolerate fields added by future firmware/API revisions.

---

## 16. Additional information from APsystems publications and field implementations

The full evidence table, source links, and validation matrix are in `docs/apsystems-additional-research.md`. The key additions are:

### 16.1 Official operational cadence

APsystems states that an ECU polls each microinverter every five minutes, sequentially, and uploads data to EMA every fifteen minutes. Channel values may therefore refer to slightly different moments, and cloud polling faster than the upload cycle will often repeat data. Source: `SRC-APS-FAQ`.

### 16.2 Accuracy boundary

APsystems describes EMA inverter production as an estimate built from periodic DC-side snapshots and explicitly distinguishes it from continuously measured, revenue-grade AC metering. Use the API for monitoring and triage, not billing or settlement. Source: `SRC-APS-FAQ`.

### 16.3 Expected unused channels

APsystems allows intentionally unused inputs on several microinverter models. The maximum channel count of a model is not the same as the commissioned connected-channel set. Source: `SRC-APS-FAQ`, `SRC-EMA-MANAGER`.

### 16.4 Meter semantics are only partially completed

Official EMA guidance says production is measured and positive, grid flow is measured and signed import/export, and consumption is calculated and normally positive. This does not fully define the OpenAPI `imported_exported` field; verify its sign under known import/export conditions. Source: `SRC-APS-FAQ`.

### 16.5 APsystems UI capabilities are not automatically OpenAPI fields

Official installer tools expose ECU heartbeat, software version, UID synchronization warnings, local communication quality, and remote management. None of these should be treated as OpenAPI capabilities unless APsystems documents a corresponding endpoint. Source: `SRC-EMA-MANAGER`.

### 16.6 Storage mode names do not provide numeric mappings

Official material names Backup, Self-consumption, Advanced/Time-of-Use, and Peak-Shaving modes. No reliable public source maps those names to the API's opaque `mode` value. Preserve the raw value and require product/firmware-specific validation. Sources: `SRC-APS-FAQ`, `SRC-APSTORAGE-APP`.

### 16.7 Historical high-resolution retention may vary

One field implementation reports `1001` for older hourly dates while coarser history remains available. Treat this as an account-specific warning, not vendor policy. Probe capabilities during onboarding and collect detailed telemetry prospectively. Source: `SRC-MATTHIJS`.

