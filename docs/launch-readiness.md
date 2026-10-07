# Pocket Guru launch audit — October 6, 2026

Decision: beta, not ready for paid public launch. Selected model: free core offering plus a recurring subscription. No subscription price or payment account has been selected. Revenue is not guaranteed by technical readiness.

## Verified and repaired

| Area | Evidence / resulting behavior |
| --- | --- |
| Catalog | Manufacturer-documented 1988–1989 Kawasaki models; instant historical/farm lookup; bounded upstream waits; repeated frontend queries reused; stale responses rejected. |
| Diagnosis | Duplicate submissions suppressed; upload/diagnosis deadlines; successful results survive browser-storage failure. |
| Repair follow-up | Saved steps reopen; findings retained; fixed/reopen status persists; no duplicate finding sections. |
| Privacy | Separate browser sessions cannot list/read another session’s API profiles/diagnoses or submit private photo IDs. HttpOnly signed cookies; private APIs no-store. Guest session isolation is not a verified account. |
| Data recovery | Export/import of browser-local garage/history; merge preserves existing records; malformed files rejected. Photos are not in backups. |
| Guidance | Item names/media filenames excluded from symptom evidence; unvalidated numerical rule scores removed from UI; explicit gas/fuel/electrical/braking hazards take priority across categories. |
| Item identity | Serial/VIN saved with item and repair; known appliance dropdowns suggest a type while leaving it editable. |
| Uploads | Failed batches clean partial files; supported-type inputs align; new upload files ignored by Git. One previously tracked photo removed from current repository tree (history still contains it). |
| Abuse | Guest mutation rate limits; photo inspection bounded to six per session/hour and sixty per process/hour. Limits are process-local and reset on restart. |
| Browser security | Source backup assets blocked; nosniff, referrer, frame and CSP headers. Inline scripts still permitted until legacy inline project code is extracted. |
| Updates | Versioned app assets, service-worker refresh on reload/open, push/PR/daily regression workflow and daily automated bug-check task. No uncontrolled dependency auto-merges. |

Dependency audit: upgraded FastAPI/Starlette, Pydantic, multipart parser and pytest; pinned the resolved runtime dependency set, separated test dependencies, and added scheduled dependency scanning. Validate audit results against the current vulnerability feed.

Validation: 65 backend checks and six DOM-based frontend suites. Live catalog release verified in a real browser; deployment health and privacy must be rechecked after the hardening release. These checks do not establish exhaustive correctness or calibrated diagnostic accuracy.

## Paid launch gates

| Gate | Current blocker | Acceptance criteria |
| --- | --- | --- |
| Verified accounts | PR2 remains draft. Supabase project restored; application integration remains incomplete. Domain/SMTP/code-delivery setup incomplete. | Real external-email signup, verification, expired/wrong codes, resend, recovery, sign-out, session expiry and isolation pass. |
| Durable private data | Garage/history browser-local; API records and uploads in process memory/files; guest signing key ephemeral unless configured. | Per-user durable database with ownership rules, cross-device sync, conflict handling, tested export/deletion, backups and restore rehearsal. |
| Subscription revenue | No checkout, price, entitlement database, webhook handler, customer portal or billing provider account. | Free access works; successful payment grants paid access; canceled/unpaid subscriptions revoke correctly; duplicated/out-of-order webhook tests; refunds/cancellation/support paths verified. Never grant access based on a checkout redirect. |
| Content | Partial motorcycle/farm/appliance models, five-code OBD starter library, basic library cards; rules are broad checks rather than model-specific service procedures. | Credible sourced coverage for the advertised audience; no wrong-year matches; known limitation labels; vetted repair/safety scenarios and fault-confirmation tests. |
| Operational scale | Process-local rate limits/state; no centralized budget enforcement; no load test or restore drill. | Durable/distributed limits, request/load budget, cost ceiling, measured latency under representative concurrency, alerting and rollback exercised. |
| Privacy and support | No complete published privacy/terms/contact/account-deletion flow. | Accurate product disclosures of local/server/provider data handling and retention, reachable support, user deletion/export; owner approves business/legal text. |
| Quality/accessibility | Desktop live test + DOM tests, not a mobile device matrix. | Android/iOS camera uploads, keyboard/screen reader, narrow viewports, offline/reconnect, full storage, expired session, network failure and update recovery verified. |
| Customer retention | Free-plus-subscription selected; offer and willingness to pay unvalidated. | Define audience and paid benefit, test with target users, instrument privacy-conscious completion/conversion/retention and cost per paying customer. |

## Subscription implementation contract

Keep basic symptom checks free. Define a paid benefit that provides repeat value (for example deeper evidence-guided follow-up and durable private repair records), with usage limits that cover photo-processing cost. The exact price/features need owner selection and real customer validation. Do not advertise cloud sync, complete catalogs, guaranteed repair accuracy, or “unlimited” AI before those promises are implemented and economically tested.

Use hosted checkout and customer portal. Store entitlements server-side under verified user IDs. Verify webhook signatures, deduplicate event IDs and tolerate out-of-order delivery. Test first payment, renewal, failure, recovery, cancellation, refund and re-subscription in test mode before activating real charges. Provider credentials and financial-account onboarding must be completed through the provider’s secure setup flow.

## Immediate sequence

1. Deploy and verify privacy/recovery hardening.
2. Restore/configure existing Supabase and verified email; complete PR2 integration and real email tests.
3. Add durable owned garage/history storage and verified migration of guest data.
4. Select subscription price/benefit and connect billing in test mode.
5. Complete checkout/lifecycle tests, published disclosures/support and mobile/load checks.
6. Release a small beta to target users; fix measured failures before paid public launch.

## Guided problem-solving release

Diagnosis now leads with one actionable check, captures the result and evidence, and selects the next step. Starting problems branch between no-crank and crank-no-start; passed battery tests lead to cable/ground testing before starter diagnosis. A reported fault requires confirmation and a repair retest. A failed retest remains open; success is clearly a user-reported outcome. Reopening clears the previous completion state. Other symptoms use recorded observations to advance the available checklists, confirm a finding or prepare a targeted handoff. Prior photo evidence is retained without re-uploading it on each follow-up. Changing item identity resets structured tests.

This is an initial predefined workflow, not universal model-specific diagnostic coverage. Expanding and validating targeted branches remains a product release gate.

## Full workflow rerun — October 6, 2026

Reran all 63 backend tests and six frontend suites. Live health, app shell, manifest, supported/unknown OBD lookup and all six diagnosis categories were exercised. These are representative workflow checks, not exhaustive real-device or load validation. Provider photo analysis remains covered by mocks; a configured API key does not establish image accuracy.

Repaired this pass:
- Different item or original complaint creates a separate case and cannot inherit old findings, photo analysis, media counts or structured results. The old case remains available.
- DIY planning ignores item names and filenames as project intent, stops assuming 12x24 tile dimensions, and removes an unimplemented quantity-calculation promise.
- Plain-language drain/heating complaints route to relevant appliance checks.
- Crank-no-start motorcycle/equipment complaints request exact engine/fuel identity and appropriate manufacturer tests rather than assume petrol components.
- Dripping faucets receive leak-location and water-isolation checks.
- Reopened cases explain that earlier photo inspection is retained; new uploads are needed only for new evidence.

The strongest next product milestones are verified accounts with durable owned case data, model-specific evidence-guided repair coverage, genuine mobile/device validation, and subscription lifecycle implementation. The app remains a beta until those acceptance criteria are met.

## Bug-check release — October 7, 2026

Reproduced locally and live: an older free-text crank-no-start finding overrode a later guided no-crank observation, so the cause checklist and next question disagreed. The latest guided starting observation now takes precedence; cases without guided answers continue to use saved findings. Hazard handling is unchanged. Two regression cases cover no-crank and slow-crank after an earlier cranking attempt.

Validation: 65 backend tests and six frontend suites, including garage/history, dependent pickers, uploads/provider failure mocks, backup, stale responses, and app failure recovery. Live smoke checks cover all six categories, catalog make dependencies, supported catalog examples, private profile/case reads and app assets. Real-camera/provider image accuracy, complete catalog coverage, cross-device persistence, load testing and PR2 external account configuration remain outside these checks.
