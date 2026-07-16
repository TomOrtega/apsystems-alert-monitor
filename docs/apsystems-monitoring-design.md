# APsystems monitoring design notes

This file translates the APsystems OpenAPI manual into a practical monitoring strategy for a photovoltaic installer. It contains implementation recommendations in addition to documented API facts. Any diagnosis derived from telemetry must be labelled as an internal inference, not an official APsystems alarm.

Official and community-sourced additions are marked and fully sourced in `docs/apsystems-additional-research.md`; use its evidence grades when implementing defaults.

## 1. Separate four kinds of state

Do not collapse everything into one status field.

```text
vendor_status            # APsystems light value
telemetry_status         # fresh, stale, missing, malformed
calculated_status        # normal, warning, critical, unknown
calculated_reason        # machine-readable rule/reason
api_service_status       # APsystems API reachable/authenticated/rate-limited
```

Also store:

```text
vendor_status_changed_at
last_vendor_sample_at
last_successful_retrieval_at
last_attempt_at
calculation_version
```

An APsystems API outage or rate limit is not proof that a customer's plant has failed. Raise a platform/integration alert separately from a plant alert.

## 2. Inventory and commissioning baseline

Use:

```http
POST /installer/api/v2/systems
GET /installer/api/v2/systems/inverters/{sid}
GET /installer/api/v2/systems/meters/{sid}
GET /installer/api/v2/systems/storages/{sid}
```

Store an expected inventory snapshot:

- system and ECU IDs
- installed capacity and timezone
- ECU type
- inverter UID and model/type
- expected number of active channels per inverter
- meter/storage presence
- customer/site metadata not supplied by APsystems: orientation, tilt, module model, channel-to-module mapping, known shading, zero-export policy, battery reserve/mode

Alert on inventory changes only after confirming persistence, because commissioning and registration changes can be legitimate.

## 3. Fleet status

Use:

```http
POST /installer/api/v2/systems
```

Interpret the manual's `light` values as follows, with the official APsystems FAQ expansion for yellow:

- `1`: vendor reports normal
- `2`: broad warning — interrupted microinverter communication, registration problem, or low/abnormal production/weak sunlight; the OpenAPI manual also calls this an alarm/registration state
- `3`: ECU network connection issue/disconnected from internet
- `4`: no data has yet been uploaded; official FAQ describes black/gray as never having reported production

Recommended handling:

- `light = 2`: warning; compare current inventory with baseline and inspect batch/channel telemetry
- `light = 3`: critical vendor communication status, but corroborate with sample freshness
- `light = 4`: unknown during initial commissioning; warning/critical only when the system previously communicated

The list endpoint has no status timestamp. Track changes in your database and infer data freshness from minutely/period series.

## 4. ECU production and freshness

Use:

```http
GET /installer/api/v2/systems/{sid}/devices/ecu/energy/{eid}?energy_level=minutely&date_range=yyyy-MM-dd
```

Track:

- last available power
- daily energy
- last sample time
- gaps, duplicate timestamps, array-length mismatches
- sudden and persistent production drops

`time` contains `HH:mm`, not a full timestamp. Combine it with `date_range` and the plant timezone. Handle midnight, daylight-saving transitions, and late-arriving points explicitly.

Do not interpret lack of daytime power as a communication failure unless the time series itself is stale or missing. At night, zero production is normal and some systems may stop adding points.

Official APsystems guidance says the ECU polls each microinverter every five minutes and uploads to EMA every fifteen minutes. Channel samples can differ by a few minutes and the cloud may repeat unchanged data inside one upload window. Treat `minutely` as a high-resolution series name, not proof of one-minute cloud updates.

APsystems also says EMA inverter energy is estimated from periodic DC-side snapshots and is not revenue-grade. Use it for operations and anomaly detection, not billing or settlement.

## 5. Batch inverter-channel monitoring

Preferred routine endpoint:

```http
GET /installer/api/v2/systems/{sid}/devices/inverter/batch/energy/{eid}?energy_level=power&date_range=yyyy-MM-dd
```

Reasons:

- one request covers all inverter channels under an ECU
- supports peer comparison
- avoids one request per inverter during normal polling

Track per `uid-channel`:

- commissioning state: connected, intentionally unused, or unknown
- last power and timestamp
- daily maximum power
- daily energy when `energy_level=energy` is queried
- ratio to a suitable peer median
- zero-power duration during expected solar production
- missing/stale series

The response appears to return a day series, so each poll may repeat all earlier samples. Upsert by `(sid, eid, uid, channel, sample_at)` rather than inserting duplicates.

Peer groups must contain comparable modules: same roof plane/orientation, module type, approximate shading profile, and preferably similar rated power. A global median across unlike channels creates false alarms.

APsystems explicitly allows intentionally unused inputs on several models. Do not compare or alert on the model's maximum channel count; compare only the commissioned connected-channel set. Also tolerate ordinary instantaneous module variation and several minutes of polling skew before opening a low-output incident.

## 6. Detailed inverter diagnostics

Only after an anomaly, use:

```http
GET /installer/api/v2/systems/{sid}/devices/inverter/energy/{uid}?energy_level=minutely&date_range=yyyy-MM-dd
```

Inspect:

- DC voltage/current/power/energy per channel
- AC power
- AC voltage
- AC frequency
- inverter temperature

Possible inferred conditions:

- DC voltage near zero on a commissioned connected input: disconnected module/input, nighttime/low irradiance, or no usable telemetry
- normal DC voltage with near-zero current: low irradiance, heavy shading, module/connector/channel issue
- one channel persistently below comparable peers: shading, soiling, mismatch, degradation, orientation difference, or channel issue
- all channels of one inverter at zero while peers produce: inverter, AC, registration, or communication issue
- all inverters under one ECU stale: ECU/network/API path issue
- temperature materially above comparable peers: possible thermal/installation issue

These are hypotheses for triage. Do not present them as manufacturer fault codes.

APsystems states that microinverters wait a 300-second dwell after valid DC, AC, and frequency conditions. Suppress startup/no-production alerts during commissioning, grid restoration, and this dwell window.

## 7. Meter monitoring

Use:

```http
GET /installer/api/v2/systems/{sid}/devices/meter/summary/{eid}
GET /installer/api/v2/systems/{sid}/devices/meter/period/{eid}?energy_level=minutely&date_range=yyyy-MM-dd
```

Documented streams:

- produced
- consumed
- imported
- exported
- minutely `imported_exported` power channel with undocumented sign convention

Safe derived metrics after validating field meaning with real data:

```text
non_exported_generation = max(produced - exported, 0)
self_consumption_ratio = non_exported_generation / produced
self_sufficiency_ratio = max(consumed - imported, 0) / consumed
grid_dependency = imported / consumed
```

Guard against division by zero, counter resets, negative values, missing intervals, and meter sign/configuration errors.

`produced - exported` is not always the same as **direct** self-consumption, particularly when a battery can charge or discharge during the period. Name it `non_exported_generation` unless the site topology and storage behavior make the stronger interpretation valid.

Official APsystems EMA guidance describes production as measured/positive, grid flow as measured/signed import-export, and consumption as calculated/positive. That validates the UI concept but not the exact OpenAPI `imported_exported` sign. Commission the API using one known import interval and one known export interval before enabling sign-dependent rules.

Potential alerts:

- production telemetry is fresh but meter series is stale
- unexpected export where a configured zero-export policy is known
- energy balance outside a configured tolerance after field conventions are validated
- unusual night baseload relative to that site's own history
- grid import inconsistent with production, load, battery SOC, reserve, and configured operating mode

## 8. Storage monitoring

Use:

```http
GET /installer/api/v2/systems/{sid}/devices/storage/latest/{eid}
GET /installer/api/v2/systems/{sid}/devices/storage/period/{eid}?energy_level=minutely&date_range=yyyy-MM-dd
```

Track:

- SOC
- operation mode as an opaque string until APsystems supplies the mapping; official publications name Backup, Self-consumption, Advanced/Time-of-Use, and Peak-Shaving modes but do not map them to OpenAPI values
- charge/discharge power
- produced/consumed/imported/exported power
- latest sample time and freshness

Potential alerts, only with site configuration context:

- SOC frozen while other storage telemetry changes
- no charging during sustained surplus while SOC is below the configured ceiling and mode permits charging
- no discharge during sustained import while SOC is above reserve and mode permits discharge
- stale sample
- unexpected mode change after mode values have been verified

The `latest` example contains only `HH:mm`. Do not treat it as a globally unique timestamp without adding date and timezone context.

## 9. Internal alert lifecycle

Use a lifecycle instead of sending a message on every failed rule evaluation:

```text
pending -> active -> acknowledged -> recovered -> closed
```

Recommended fields:

- rule ID and rule version
- scope: system/ECU/inverter/channel/meter/storage/integration
- first detected, last detected, activated, acknowledged, recovered
- severity and confidence
- observed values and peer/baseline values
- raw source payload references
- deduplication key

Require persistence or repeated observations before activation. Use separate recovery thresholds/hysteresis to avoid alert flapping.

## 10. Suggested polling cadence

APsystems officially states a five-minute inverter polling cycle and a fifteen-minute upload to EMA. The table below is an operational starting point, not a vendor SLA. Tune it to fleet size, plan limits, and support commitments.

| Data | Suggested cadence |
|---|---|
| System list and `light` | Every 15 minutes; 10 minutes only when the quota/SLA justifies duplicate polls |
| Batch inverter power | Every 15-30 minutes in daylight |
| ECU minutely curve | Every 15-30 minutes in daylight or as fallback |
| Meter minutely curve | Every 15 minutes |
| Storage latest | Every 15 minutes by default; test whether the storage service updates faster before reducing it |
| Inventory | Daily and after persistent change |
| Summary totals | End of day plus on-demand |
| Individual detailed inverter telemetry | On alert/diagnosis |

Do not poll every minute merely because the level is called `minutely`. The response appears to return the day's series, and the official cloud upload rhythm is fifteen minutes.

Suggested freshness states during expected production — internal defaults, not APsystems thresholds:

```text
fresh: latest sample age <= 25 minutes
warning candidate: > 30 minutes
critical communication candidate: > 45 minutes
```

Require persistence, corroborate with `light`, and make thresholds configurable. Use the plant timezone and a solar/daylight scheduler. Continue lightweight communication checks at night, but suppress production alerts when production is not expected.

## 11. Alert quality controls

Combine:

- absolute safety/data-validity thresholds
- persistence and hysteresis
- sun elevation/daylight context
- peer comparison within a valid peer group
- installed capacity and channel/module rating
- site-specific baseline and seasonality
- known shading/orientation metadata
- weather/irradiance from an external source when available

Useful performance metrics:

```text
specific_yield = daily_kWh / installed_kWp
channel_peer_ratio = channel_energy / peer_median_energy
availability = fresh_expected_intervals / expected_intervals
```

Do not calculate or label a formal performance ratio (PR) without irradiance and the other inputs required by your chosen methodology.

## 12. API request-budget planning

Manual limits range from 1,000 to 1,000,000 calls/month. Treat prices as historical until confirmed.

Estimate each endpoint family separately:

```text
system_list_calls = pages_per_poll * list_polls_per_day * days
batch_calls = ecu_count * batch_polls_per_day * days
meter_calls = meter_count * meter_polls_per_day * days
storage_calls = storage_count * storage_polls_per_day * days
diagnostic_calls = expected_alerts * average_diagnostic_calls
monthly_total = sum(all families) + retries + backfills
```

Example: 100 ECUs, 24 daylight batch polls/day, 30 days:

```text
100 * 24 * 30 = 72,000 calls/month
```

Budget headroom for retries, manual dashboard refreshes, new installations, and historical backfill. Cache inventory and use batch endpoints.

## 13. Recommended storage model

Core tables/collections:

- `systems`
- `ecus`
- `inverters`
- `inverter_channels`
- `system_status_observations`
- `ecu_samples`
- `inverter_channel_samples`
- `meter_samples`
- `storage_samples`
- `alerts`
- `api_call_log`
- `raw_vendor_payloads` or object-storage references

Always store:

- APsystems IDs as strings
- raw payload or raw-payload reference for traceability
- parsed numeric values as decimal/numeric types
- source endpoint and original response `code`
- plant timezone
- vendor sample timestamp and retrieval timestamp separately
- parser/schema version

Use idempotent upserts for repeated day-series responses. Preserve unknown JSON fields so new vendor fields are not silently discarded.

## 14. Implementation safeguards

- Use HMAC-SHA256 and Base64 over the raw HMAC bytes.
- Default to Unix epoch milliseconds and generate a unique lowercase 32-hex nonce per request; rebuild both on each retry.
- Keep App Secret server-side and out of logs/client bundles.
- Keep timestamp encoder, clock skew, POST serialization, API profile, and per-endpoint signing component configurable until installer credentials verify them.
- Send GET parameters in the query string by default and exclude them from HMAC unless a tested profile proves otherwise.
- Parse numeric strings defensively and preserve null/missing/unrecognized values.
- Validate aligned arrays have equal lengths; quarantine malformed payloads rather than shifting data silently.
- Retry only transient API/integration errors with bounded exponential backoff and jitter.
- Respect monthly limits and stop retry storms on quota/auth errors.
- Test shared sub-user virtual ECU IDs.
- Never invent storage mode mappings, detailed units, alarm codes, or meter-flow signs.
- Version alert rules so historical decisions remain explainable.

## 15. Minimum acceptance tests before production

1. Record credential provenance and select the correct `/installer` or `/user` API profile.
2. Complete a real signed GET using epoch milliseconds, a fresh 32-hex nonce, and the profile's validated signing component.
3. Complete a real installer POST and record JSON/form/query serialization plus `Content-Type`.
4. Measure allowed clock skew/replay handling with a bounded test.
5. Verify all response envelopes, HTTP-200/non-zero-code behavior, and unexpected-MIME JSON parsing.
6. Capture real payloads for each installed inverter, meter, and storage model.
7. Verify five-minute sampling/15-minute upload behavior, duplicate and late samples, retention, missing-channel behavior, and units.
8. Verify meter import/export direction with controlled import and export observations.
9. Verify storage mode mapping and latest-power units with APsystems/support or controlled authorized observation.
10. Exercise `1001`, `2005`, `7001`, `7002`, `7003`, timeout, malformed payload, unexpected MIME, and partial-array cases.
11. Load-test the intended polling schedule against the monthly call budget without exhausting production credentials.
12. Preserve redacted fixtures and evidence grades for every validated behavior.
