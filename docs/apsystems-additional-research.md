# APsystems OpenAPI — additional information from external research

Research date: **2026-07-16**

This addendum complements the supplied **APsystems OpenAPI User Manual — Installer, V1.8 (2025-07-18)**. It does not replace that manual. It separates vendor-published information from community observations and marks every conclusion by evidence level.

## 1. Evidence levels and precedence

Use this order when sources disagree:

1. **A — supplied installer manual:** contractual source for installer endpoint paths and documented fields.
2. **B — official APsystems publications:** APsystems FAQ, EMA Manager manuals, APstorage manuals, and official product documentation.
3. **C — reproducible community implementation:** public code or forum examples that report a successful API response with `code: 0`.
4. **D — anecdotal community observation:** a single blog/forum report without a reproducible confirmation.

External research must never silently overwrite the installer manual. Code should attach an evidence tag to implementation assumptions that are not grade A or B.

## 2. Validation status at a glance

| Topic | Result after research | Confidence | Implementation decision | Sources |
|---|---|---:|---|---|
| Timestamp unit | Working community clients and a forum report attributed to APsystems use Unix epoch **milliseconds** | C, high | Default to epoch milliseconds, but keep configurable until installer credentials prove it | `SRC-HOMEY`, `SRC-GITHUB-OPENAPI`, `SRC-MATTHIJS` |
| Nonce | The manual example and working clients use 32 hexadecimal characters without hyphens | A+C, high | Generate a fresh lowercase `uuid4().hex`/16-byte hex nonce per request | Installer manual, `SRC-HOMEY`, `SRC-GITHUB-OPENAPI` |
| GET parameters | Working clients send `energy_level` and `date_range` as URL query parameters | C, high | Send GET parameters in the query string; do not include them in the HMAC input unless APsystems says otherwise | `SRC-HOMEY`, `SRC-GITHUB-OPENAPI`, `SRC-MATTHIJS` |
| POST serialization | No reliable installer example was found | unresolved | Keep JSON/form/query serialization configurable; block production POST flows until tested | Installer manual |
| Signed `RequestPath` component | Sources conflict between final URL segment/ID and an operation-name segment on some `/user` routes | unresolved | Use a per-endpoint signing-component strategy and a controlled credential test; never hard-code one global interpretation without testing | Installer manual, `SRC-HOMEY`, `SRC-GITHUB-OPENAPI`, `SRC-MATTHIJS` |
| Endpoint prefix | Supplied installer manual uses `/installer/api/v2`; a separate end-user V1.8 manual and working community clients use `/user/api/v2` | A+C, high that both exist; role mapping only medium | Model API role explicitly (`installer` or `end_user`); never silently substitute prefixes | Installer manual, `SRC-ENDUSER-MANUAL`, `SRC-HOMEY`, `SRC-GITHUB-OPENAPI` |
| Response success | Community tests show HTTP 200 may still contain non-zero JSON `code`, such as `4000` | C, high | Validate both HTTP status and JSON `code` | `SRC-HOMEY`, `SRC-GITHUB-OPENAPI` |
| Response content type | One maintained client reports valid JSON occasionally arrives with an unexpected content type such as `application/octet-stream` | C, medium | Parse the body as JSON defensively after bounded size/encoding checks; do not rely only on MIME type | `SRC-GITHUB-OPENAPI` |
| ECU/EMA cadence | APsystems says each microinverter is polled every 5 minutes and data is uploaded to EMA every 15 minutes | B, high | Do not expect cloud freshness below roughly 15 minutes; avoid wasteful sub-15-minute fleet polling unless storage tests prove otherwise | `SRC-APS-FAQ` |
| EMA measurement accuracy | APsystems describes ECU values as periodic DC-side snapshots and EMA energy as an estimate, not revenue-grade metering | B, high | Do not use EMA inverter energy for billing, settlement, or contractual guarantees | `SRC-APS-FAQ` |
| `light = 2` meaning | Official FAQ expands yellow to interrupted inverter communication, registration problems, or low/abnormal production/weak sunlight | B, high | Treat yellow as a broad vendor warning, not a specific inverter alarm | `SRC-APS-FAQ` |
| Meter graph semantics | APsystems says production is measured and positive, grid is signed import/export and measured, and consumption is calculated and normally positive | B, high for EMA UI; API field sign still partial | Keep `imported`/`exported` counters separate; empirically verify the API's minutely `imported_exported` sign | `SRC-APS-FAQ` |
| Empty inverter channels | APsystems explicitly allows unused inputs on several models | B, high | Build expected-channel inventory from commissioning metadata/model, not from maximum model channel count alone | `SRC-APS-FAQ`, `SRC-EMA-MANAGER` |
| Startup delay | APsystems states microinverters wait a 300-second dwell after valid DC, AC, and frequency conditions | B, high | Suppress startup/no-production alerts during commissioning, grid recovery, and the dwell window | `SRC-APS-FAQ` |
| ECU heartbeat/firmware/radio data | APsystems installer tools expose heartbeat, software version, UID sync warnings, and local communication quality in their UI | B, high that UI has them | Do not assume OpenAPI access: the supplied OpenAPI manual does not expose these fields | `SRC-EMA-MANAGER` |
| Remote commands | APsystems installer tools support remote management and changes apply on a later reporting cycle | B, high that UI has them | Do not implement control through OpenAPI without a documented endpoint and explicit authorization | `SRC-EMA-MANAGER` |
| Storage modes | APsystems publishes named modes: Backup, Self-consumption, Advanced/Time-of-Use, and in newer app documentation Peak-Shaving | B, high for names | Keep OpenAPI numeric/string `mode` opaque; no reliable numeric mapping was found | `SRC-APS-FAQ`, `SRC-APSTORAGE-APP` |
| Historical retention | A 2026 user report found older hourly data returned `1001` while coarser history remained available | D, low/installation-specific | Add a retention-capability probe and collect detailed telemetry prospectively; do not promise full historical backfill | `SRC-MATTHIJS` |
| Local ECU enrichment | A community Home Assistant integration reads local ECU data including per-inverter status and radio metrics | C, medium for local protocol only | Treat local ECU access as an optional, separately secured adapter; never merge it into the cloud OpenAPI contract | `SRC-LOCAL-ECU` |

## 3. Authentication and transport — additional information

### 3.1 Recommended timestamp default

The installer manual only calls `X-CA-Timestamp` a timestamp. Multiple independent community implementations that report successful requests use:

```text
Unix epoch time in milliseconds, encoded as a decimal string
```

Example generation:

```python
str(int(time.time() * 1000))
```

This is strong operational evidence, but it is not an official installer specification. Keep a configuration option or strategy interface for the timestamp encoder, and still ask APsystems for accepted clock skew and replay-window rules.

### 3.2 Recommended nonce default

Use 16 random bytes encoded as 32 lowercase hexadecimal characters, or UUIDv4 hex without hyphens:

```python
uuid.uuid4().hex
```

Create a new nonce for every request. Do not reuse one across retries; rebuild the timestamp, nonce, and signature for each retry attempt.

### 3.3 GET query serialization

Working examples place `energy_level`, `date_range`, and similar GET parameters in the URL query string. The observed HMAC input contains the timestamp, nonce, App ID, selected path component, HTTP method, and signature method — not the query string.

Recommended default:

```text
GET /.../energy/{id}?energy_level=minutely&date_range=2026-07-16
```

Do not append `sid`, `uid`, or `eid` redundantly as query parameters unless a tested endpoint actually requires them.

### 3.4 `RequestPath` remains the most important unresolved item

The supplied installer manual says to sign the last segment of the path. A successful forum example and a maintained `/user` client implement the final URL segment, normally the `sid`, `eid`, or `uid`. A separate 2026 blog reports that some `/user` routes require a static operation segment such as `details` or `energy`.

These reports may reflect:

- different `/user` route shapes or server revisions;
- account-role differences;
- endpoint-specific gateway routing;
- mistakes or undocumented compatibility aliases.

Do **not** turn either community interpretation into a universal rule. Implement:

```text
signature_component_strategy(endpoint, concrete_path) -> string
```

with at least these controlled strategies:

- `final_segment`: last non-empty concrete URL segment;
- `operation_segment`: explicitly configured static segment for that endpoint.

For the installer client, start from the supplied manual's `final_segment` rule and validate it with a harmless GET. Log the selected strategy name and a redacted string-to-sign, never the secret or full signature.

### 3.5 `/installer` and `/user` are separate API surfaces

The supplied manual documents `/installer/api/v2/...`. A vendor-branded end-user V1.8 manual mirrored publicly and several working community projects use `/user/api/v2/...`.

The likely explanation is separate installer and end-user credential scopes, but APsystems has not been found stating this mapping explicitly in a public document. Therefore:

- require an `account_role`/`api_profile` setting;
- bind `installer` to `/installer/api/v2` by default;
- bind `end_user` to `/user/api/v2` only when the credentials were obtained through the EMA end-user OpenAPI service and the end-user manual applies;
- do not auto-fallback from one prefix to the other after an auth error;
- record credential provenance and manual version during onboarding.

### 3.6 HTTP and JSON handling

Community evidence shows HTTP 200 can carry an application-level error code. Always evaluate:

1. transport status;
2. body parse success;
3. JSON `code`;
4. expected `data` shape.

A maintained client also reports valid JSON with an unexpected MIME type. A defensive client may parse text as JSON when:

- the response size is bounded;
- encoding is valid or recoverable;
- the first non-whitespace byte is JSON-like;
- parsing errors are recorded without exposing credentials.

This does not validate POST `Content-Type`; POST serialization is still unresolved.

## 4. Monitoring semantics validated by APsystems

### 4.1 Cloud update rhythm

APsystems states that the ECU polls each microinverter every five minutes, one by one, and sends data to the EMA portal every fifteen minutes. Consequences:

- channel timestamps can differ by several minutes;
- two panels should not be compared as if sampled at the exact same instant;
- repeated API polls inside one 15-minute upload interval may return identical data;
- a freshness warning should allow at least one missed upload interval plus processing/network tolerance.

Suggested internal defaults — **not vendor thresholds**:

```text
fresh: latest sample age <= 25 minutes during expected production
warning candidate: > 30 minutes
critical communication candidate: > 45 minutes
```

Use persistence and the vendor `light` state before alerting. Make these thresholds configurable by fleet and SLA.

### 4.2 Broader meaning of the system traffic light

The OpenAPI manual summarizes yellow as inverter alarms or registration problems. APsystems' installer FAQ expands yellow to include:

- interrupted microinverter communication since the beginning of the day;
- improperly registered microinverters;
- low or abnormal power production, including weak/no sunlight.

Therefore `light = 2` is a broad triage signal. It cannot identify the device or prove a hardware fault.

### 4.3 Telemetry is not revenue-grade

APsystems says ECU production values are periodic DC-side snapshots and EMA energy is estimated from those intervals, whereas a utility meter continuously measures AC energy. Use EMA/OpenAPI for operations and fault detection, not invoices, regulatory settlement, guaranteed-yield compensation, or revenue-grade reconciliation.

### 4.4 Panel/channel comparisons need timing and topology tolerance

APsystems notes ordinary module-to-module variation around ±10%, different polling times, and shading differences. Do not alert on one instantaneous percentage deviation alone. Compare aligned windows or daily energy within valid peer groups and require persistence.

### 4.5 Unused channels are normal

Several APsystems models allow one or more inputs to be intentionally unused. The EMA Manager documentation also notes that local tools may display the model's maximum channels and may warn that an intentionally unused channel has no panel.

The system database should store:

```text
expected_channel_count
connected_channel_set
unused_channel_set
commissioning_verified_at
```

Never infer a missing panel solely because `dc_pN` is zero or absent.

### 4.6 Meter interpretation — partial validation only

For the EMA meter graph, APsystems describes:

- solar production: measured and positive;
- grid flow: measured and signed as import/export;
- household consumption: calculated and normally positive.

This helps validate CT orientation and high-level energy balance, but the OpenAPI field `imported_exported` still lacks a published sign convention. During commissioning, create a known import condition and a known export condition, then record the observed sign before enabling related alerts.

## 5. Data available in APsystems tools but not validated for OpenAPI

Official APsystems installer documentation shows that EMA Manager/local ECU tools can expose:

- ECU heartbeat/last connection to EMA;
- ECU software version and timezone;
- UIDs registered in EMA but not synchronized to the ECU;
- inverter-to-ECU communication quality in local commissioning;
- detailed inverter power, grid voltage, frequency, and temperature;
- remote UID/grid-profile management and other installer controls.

The supplied OpenAPI manual does not document heartbeat, firmware, radio quality, synchronization state, maintenance history, or remote-control endpoints. Treat these as **vendor UI capabilities, not OpenAPI capabilities**. Do not scrape private EMA pages or reverse-engineer control calls in the production integration without a separate agreement and security review.

## 6. Storage information — what was and was not completed

Official APsystems publications name these storage modes:

- Backup;
- Self-consumption;
- Advanced/Time-of-Use;
- Peak-Shaving in newer APstorage app documentation.

No reliable public source was found mapping those names to the OpenAPI `mode` values such as the example value `"4"`. Therefore:

- store the raw value;
- display `Unknown mode (raw: 4)` until mapped;
- allow an externally configured mapping per firmware/product family;
- never trigger mode-specific control or fault logic from an unverified numeric mapping.

The units of `storage/latest` power fields also remain unconfirmed by a public installer API source. The period endpoint documents W, so W is a plausible hypothesis, not a validated contract for `latest`.

## 7. Historical retention and prospective collection

One 2026 user report found that old hourly requests returned `code: 1001` while daily/monthly/yearly data remained available. This may be account-, region-, firmware-, or retention-policy-specific.

At onboarding, run a low-cost capability probe against known dates:

- current day minutely/hourly;
- previous week hourly;
- previous month daily;
- previous year monthly.

Store the result as a capability matrix. For detailed analysis, collect new series prospectively rather than assuming APsystems will provide an indefinite high-resolution backfill.

## 8. Optional local ECU adapter

Community projects demonstrate local ECU access with extra data such as per-inverter online state and radio metrics. This is a different protocol and trust boundary from the cloud OpenAPI.

If local enrichment is later required:

- implement it as a separate adapter/module;
- authenticate and segment the local network;
- rate-limit queries to the ECU;
- keep local and cloud timestamps/source IDs separate;
- do not let local reverse-engineered fields redefine the cloud API schema;
- treat compatibility as ECU-model/firmware specific.

## 9. Production validation matrix for OpenCode

OpenCode should create an integration test harness that records redacted request/response evidence for each API profile.

| Test | Installer profile | End-user profile | Pass condition |
|---|---:|---:|---|
| Base prefix | `/installer/api/v2` | `/user/api/v2` | Expected endpoint responds without auth/parameter error |
| Timestamp | epoch milliseconds | epoch milliseconds | `code: 0` on a safe GET |
| Signature component | final segment first; configured alternative only if needed | final segment first; endpoint override if proven | One strategy consistently succeeds per endpoint |
| GET parameters | query string | query string | Period endpoint returns expected shape or legitimate `1001` |
| Query in HMAC | excluded first | excluded first | Signature succeeds |
| POST body | JSON, form, query variants only in controlled test | according to applicable manual | System-list/authorized-system request returns `code: 0` |
| Clock skew | controlled offsets | controlled offsets | Accepted window documented without excessive requests |
| MIME tolerance | JSON and unexpected JSON-like MIME | same | Body parsed safely |
| Retention | minutely/hourly/daily/monthly probes | same | Capability matrix stored |
| Meter sign | known import/export test | same | Sign convention recorded |
| Storage mode | manually change known mode when authorized | same | Raw-value mapping confirmed per product/firmware |

Do not brute-force signature or serialization variants. Limit the matrix, stop after success, and preserve the request quota.

## 10. Questions still requiring APsystems confirmation

External research did **not** safely resolve:

1. accepted timestamp clock skew and replay-window behavior;
2. definitive installer `RequestPath` component for every endpoint;
3. POST body/query/form serialization and required `Content-Type`;
4. official signature test vectors;
5. installer vs end-user credential-scope rules and whether endpoints differ beyond the prefix;
6. `storage/latest` units and numeric `mode` mapping;
7. exact OpenAPI `imported_exported` sign convention;
8. retention windows and sample replacement/late-arrival policy;
9. detailed alarm/event, heartbeat, firmware, radio-quality, and remote-control API availability;
10. the complete third-party authorization flow and the missing dedicated OpenAPI third-party integration document.

Recommended support request: send APsystems this numbered list and ask for a current installer sample request/response for one GET, one POST, meter minutely data, and storage latest data.

## 11. Source registry

### `SRC-APS-FAQ` — official APsystems

- Title: Professional Installer FAQ
- Publisher: APsystems EMEA
- URL: https://emea.apsystems.com/resources/installer-faq/
- Used for: 5-minute inverter polling, 15-minute EMA upload, traffic-light meanings, meter graph semantics, non-revenue-grade warning, normal panel variation, intentionally unused channels, 300-second startup dwell, storage mode names, installer API availability.
- Evidence grade: **B**

### `SRC-EMA-MANAGER` — official APsystems

- Title: EMA Manager User Manual
- Publisher: APsystems
- URL: https://global.apsystems.com/wp-content/uploads/2021/06/EMA-Manager-User-Manual-Release.pdf
- Used for: ECU heartbeat and software version in installer UI, UID synchronization warnings, local communication quality, unused-channel UI behavior, remote management/reporting-cycle behavior.
- Evidence grade: **B**

### `SRC-APSTORAGE-APP` — official APsystems

- Title: EMA APP Operation Manual — APstorage V1.0.2
- Publisher: APsystems
- URL: https://global.apsystems.com/wp-content/uploads/2025/05/EMA-APP-Operation-Manual_APstorage_V1.0.2_EN.pdf
- Used for: published storage mode names and newer Peak-Shaving mode; not used to infer numeric OpenAPI mappings.
- Evidence grade: **B**

### `SRC-ENDUSER-MANUAL` — vendor-branded manual mirrored publicly

- Title: APsystems OpenAPI User Manual — End User, V1.8
- Mirror: GitHub repository `emlynmac/apsystems-openapi`
- URL: https://github.com/emlynmac/apsystems-openapi/blob/main/Apsystems_OpenAPI_User_Manual_End_User_EN.pdf
- Used for: existence of a `/user/api/v2` API surface distinct from the supplied `/installer/api/v2` manual.
- Evidence grade: **B/C** because the content is vendor-branded but the delivery URL is not an APsystems domain.

### `SRC-HOMEY` — community forum with successful response

- Title: Solar system from APsystems — page 4
- Publisher: Homey Community
- URL: https://community.homey.app/t/solar-system-from-apsystems/74759?page=4
- Used for: epoch-millisecond timestamp, 32-character nonce, final-segment signing observation, URL query parameters, HTTP 200 with JSON errors, and a reported `code: 0` system-details response.
- Evidence grade: **C**

### `SRC-GITHUB-OPENAPI` — maintained community client

- Title: `emlynmac/apsystems-openapi`
- Publisher: GitHub community repository
- API client URL: https://github.com/emlynmac/apsystems-openapi/blob/main/apsystems_openapi/api.py
- Used for: epoch milliseconds, UUID hex nonce, final concrete path segment, query parameters excluded from signature, HTTP-200/application-code handling, and tolerant JSON parsing when MIME type is unexpected.
- Evidence grade: **C**

### `SRC-MATTHIJS` — independent 2026 implementation report

- Title: Getting the APSystems API to work
- Publisher: Matth-ijs.nl
- URL: https://www.matth-ijs.nl/posts/2026/2026-04-10-solar-APSAPI/
- Used for: additional working-request patterns, conflicting operation-segment signing report, and account-specific hourly-retention observation.
- Evidence grade: **C/D**; use only as a compatibility clue, never as the sole contract source.

### `SRC-LOCAL-ECU` — community local-protocol integration

- Title: `HAEdwin/homeassistant-apsystems_ecu_reader`
- Publisher: GitHub community repository
- URL: https://github.com/HAEdwin/homeassistant-apsystems_ecu_reader
- Used for: evidence that local ECU integrations can expose extra operational/radio fields. It does not validate cloud OpenAPI fields.
- Evidence grade: **C**, local protocol only.

## 12. Change-control rule

When a real installer request proves or disproves an item in this addendum:

1. save a redacted fixture;
2. record API profile, region, endpoint, ECU model/firmware where known, and test date;
3. update this file's validation table;
4. move the behavior into the main reference only when it is reproducible;
5. retain the previous behavior as a compatibility strategy if existing installations still need it.
