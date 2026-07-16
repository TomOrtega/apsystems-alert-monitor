# APsystems manual-to-Markdown audit

## Audit scope

Source checked: `APsystems OpenAPI User Manual`, 38 pages, revision V1.8 dated 2025-07-18.

This package was reviewed against every source page, including tables and malformed JSON examples. The goal is faithful implementation guidance, not a literal OCR dump. External APsystems publications and community implementations are documented separately in `apsystems-additional-research.md`; they are not blended invisibly into the manual transcription.

## Coverage result

- 19 of 19 documented endpoints included
- all documented request header names included
- signature concatenation order included
- both HMAC algorithms included
- base URL included
- system `light` mappings included
- system, ECU, meter, inverter, batch-inverter, storage, and third-party response fields included
- all 22 response codes included (`0` plus the listed `1000`-`7003` families)
- pricing limits and both USD/EUR prices included
- shared sub-user virtual ECU rule included
- visitor iframe authorization-code mechanism included
- manual revision history included

## Corrections made during audit

1. Added source revision history and the duplicate V1.6 note.
2. Added the omitted USD pricing column.
3. Added the visitor-access authorization-code generation description and iframe URL pattern.
4. Added the stale token-language warning: V1.2 says normal authentication changed to signatures.
5. Added missing implementation gaps: timestamp, clock skew, serialization, content type, HTTP status behavior, and exact signing path.
6. Added array-index semantics and the missing-year-label warning.
7. Marked reconstructed JSON examples as normalized illustrations.
8. Added response-shape inconsistencies where the manual calls objects/maps “lists”.
9. Added absent-channel/null/duplicate-sample handling as unresolved behavior.
10. Corrected monitoring terminology so `produced - exported` is not blindly called direct self-consumption on storage sites.
11. Separated APsystems API health from plant health.
12. Added timezone, daylight, idempotency, alert lifecycle, and acceptance-test requirements.

## External validation status

Research against official APsystems publications, a vendor-branded end-user manual, and reproducible community clients produced these results:

| Item | Status | Evidence |
|---|---|---|
| Timestamp unit | Operational default completed as Unix epoch milliseconds; still not stated by the installer manual | successful community clients and a forum report attributed to APsystems support |
| Nonce format | Completed as fresh 32-character lowercase hex | installer manual example plus working clients |
| GET parameters | Completed as URL query parameters, normally excluded from HMAC input | multiple working clients |
| Cloud cadence | Completed: 5-minute ECU polling and 15-minute EMA upload | official APsystems installer FAQ |
| Yellow `light` semantics | Expanded: communication, registration, or low/abnormal production/weak sunlight | official APsystems installer FAQ |
| Meter UI semantics | Partially completed | official APsystems installer FAQ; API minutely sign remains unverified |
| Expected unused channels | Completed as a valid commissioning state | official APsystems FAQ/EMA Manager manual |
| Storage mode names | Partially completed | official names found, numeric API mapping absent |
| API profile | Partially completed | `/installer` and `/user` surfaces both documented/used; exact credential-scope mapping remains unpublished |
| Signed path component | Still unresolved | public working implementations conflict by route/profile |
| POST serialization | Still unresolved | no reliable installer POST example found |

Full evidence grades, implementation decisions, source links, and the test matrix are in `apsystems-additional-research.md`.

## Unresolved source gaps after external research

The following still require APsystems confirmation or real installer credentials:

- timestamp clock-skew tolerance and replay window
- definitive signed component for every installer endpoint
- POST parameter serialization and required `Content-Type`
- official signature test vectors
- detailed alarm/event endpoints or alarm codes
- per-device online/last-seen fields through OpenAPI
- detailed inverter electrical units for every field
- API behavior for absent/null channels, partial arrays, duplicate and late samples
- storage numeric mode meanings and `latest` power units
- exact API `imported_exported` sign convention
- year labels and high-resolution retention policy
- firmware, radio quality, battery SOH/cycles, irradiance, webhooks, or remote control through OpenAPI
- the full third-party authorization flow; a separate OpenAPI PDF is required

These gaps must remain explicit in code and tests. APsystems UI capabilities must not be mistaken for OpenAPI fields.

## Fidelity decision

The revised Markdown plus the external research addendum is complete enough for OpenCode to design and implement a defensive client and monitoring system. It is not sufficient to guarantee a successful production integration without at least one real installer credential/test system, because path-signing behavior, POST serialization, several units/enums, and the third-party authorization flow remain unconfirmed.
