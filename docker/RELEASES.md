## candidate-20261103-background-observer

- User acceptance: **pending**. Observation-only MuJoCo worker; the numeric 1D supervisor retains command authority.
- Image ID: `sha256:6b492b8a086469154e4853bc50161672db58eb8633a8645c8bbf24b629e0e914`.
- PASS: 110 image logic tests, 2 host delivery tests, integration, reset (15 message cases and 2 MuJoCo runs), and 24-run regression (zero verification failures).
- Three paced cycles have identical compared traces and evaluator-confirmed placement. Complete observations are received; incomplete replies are discarded. Worker-termination probe returns through the foreground path, and workers close.
- Foreground-call timing excludes physics, file output, pacing, initialization and shutdown; no hard realtime or physical validation claim. See the timing table and observation counts in the evidence.
- Source hashes matched. All prior image IDs including accepted-core-v1 and native-physics are unchanged. No accepted/stable/latest tag or registry push.
- CAD V5 remains distinct from the evaluated MuJoCo representation. No physical calibration claim.
- Evidence: [candidate record](evidence/candidate-20261103-background-observer.json); [Vietnamese report](../docs/bao_cao_du_bao_nen_20261103.md).

## candidate-20261103-native-physics — checked 2026-11-03

- User acceptance: **pending**. No accepted/stable/latest tag assigned.
- Image ID: `sha256:d7458ca5cc4766b8a537aa80b77b48bcf6e32096c49574f2a42606132f22aa27`.
- Scope: native grouped contact forecasts, configurable 1..16 workers (default 1),
  reference implementation retained, optional 8-worker profile. Numeric supervisor remains default.
- Final container: 103 logic checks; 12 numerical fixtures at 1/4/8 workers;
  trajectory regression; integration; 24 qualification runs; opt-in native-profile cycle.
  All commands exited 0. Native cycle held with prediction_deadline_exceeded and supported product;
  this is not completed production.
- Source hashes matched; all previous delivered images/tags preserved, including the accepted core.
- Evidence: [evidence/candidate-20261103-native-physics.json](evidence/candidate-20261103-native-physics.json).
- Benchmark output: `output/docker/physics-check_20261103T030306Z_e2d2c233`.
- Earlier candidate attempt failed parameter-report initialization for native_threads.
  The unit declaration was corrected at the shared boundary and checked in the final image.
  Failed logs remain at output/docker/qualification_20261103_native/.
- Grouped native calls cannot be preempted mid-call. Observed 20 ms overruns still select HOLD;
  these findings do not qualify hard realtime or physical accuracy. No step/scenario reduction.
- Neither CAD V5 synchronization nor physical calibration is newly claimed.

## candidate-20261102-qualification — checked 2026-11-02

- Scope: configurable timing benchmark, 24 matched fault/network/plant-variation runs,
  Vietnamese report and read-only dashboard timing table. Existing control parameters unchanged.
- User acceptance: **pending**; no accepted/stable/latest tag assigned.
- Image ID: `sha256:050de0d323a5230c824311f684f61653076ff753cca2abce7087b550cb613ed7`.
- Container: 97 logic checks, qualification study 24/24 without verification failures,
  integration strict/open-loop/replay/forecast/deadline checks all exit 0.
- Additional host checks: 8 web checks, 2 delivery checks and JavaScript syntax passed.
- Runtime source hashes matched; all previous accepted/candidate images preserved.
- Evidence: [evidence/candidate-20261102-qualification.json](evidence/candidate-20261102-qualification.json).
- Qualification output: `output/docker/qualification-check_20261102T164207Z_cd5d5129`.
- Measured timings do not qualify hard realtime. MuJoCo incomplete at the configured
  20 ms deadline in 15/15 measured calls; complete at the separate functional allowance.
- Local WSL start failed while C: was nearly full. Transparent NTFS compression of
  generated results and the local environment retained file paths/data, then WSL and Docker ran.
  Low disk capacity remains an operational limitation; no previous image was deleted.
- CAD V5/full-cell geometry and hardware calibration limits remain unchanged.

## candidate-20261031-integrated-core-v1 — checked 2026-11-01

- User acceptance: **pending**. No accepted/stable/latest tag assigned.
- Scope: six integrated software modules, single product, shared simulation/replay core,
  session/generation guards, independent belt/block forecast and read-only Vietnamese dashboard.
- Image ID: `sha256:ec749e5566c1c800890cbef02463f7b76d0051efa0015c88ed884bc65ef2d220`.
- Container checks: 93 unit checks; integration strict/open-loop/replay/physics/deadline guard;
  15 reset-message cases plus 2 MuJoCo scenes; 15 reconfiguration cases. All exited 0.
- Image source hashes matched the workspace; previous accepted and candidate images preserved.
- Evidence and runtime source hashes: [evidence/candidate-20261031-integrated-core-v1.json](evidence/candidate-20261031-integrated-core-v1.json).
- MuJoCo forecast remains opt-in; functional 2 s allowance is not real-time qualification.
  Default 20 ms budget is unchanged. No physical calibration, PLC outputs or full CAD V5 synchronization.
- Web HTTP/content checked in WSL, JavaScript syntax checked; no browser visual review claimed.
- No registry or GitHub push occurred.

# Docker delivery record

## candidate-20261031-reset-protocol

- User acceptance: **pending**. User authorized continued implementation and
  requested easy Vietnamese reports; no personal candidate acceptance inferred.
- Image ID: `sha256:df33a46dec93f611343a7037221a86d6f86069e0421f54c58543dcb124abf31a`.
- Adds simulation-only reset/request-ack/separate-start coordinator, session,
  generation/profile/hold binding, timeouts checked even without incoming messages,
  and a single-consumption new-cycle grant. No old-controller/product resume.
- Simulator adapter creates a separate scene before acknowledgement, then runs
  that same prepared scene after a distinct start. Used/unreset prepared scenes
  and mismatched profiles are rejected. Old held scene remains unchanged.
- PASS in final image: 88 logic tests; **15 message-only probes and 2 MuJoCo
  movement runs** in reset demonstration (distinct counts); 10 recovery review
  cases; 78 robustness cases; 9 adaptive smoke; 15 fixed-policy cases; default
  demo DONE/placement=true; strict HOLD. Host delivery boundary checks: 2 PASS.
- 78 controller traces match prior hold-review regression traces byte-for-byte.
  Default runtime profile remains fixed-cap; reset demonstration is explicit opt-in.
- Operator confirmations are synthetic; outage removal between scenes is declared
  in before/after profiles. No automatic network repair or mid-cycle recovery claim.
- Logical message time, in-memory sequential prototype and 1 s functional predictor
  budget; no real PLC transport/authentication, global sensor-generation envelope,
  concurrent command writers, 20 ms qualification or full CAD V5 synchronization.
- All final runtime hashes matched workspace. Accepted core and six previous
  candidate image IDs verified unchanged; no registry push or remote CI run.
- [Evidence](evidence/candidate-20261031-reset-protocol.json),
  [easy Vietnamese guide](../docs/dat_lai_chu_trinh_moi.md),
  [plain progress report](../docs/bao_cao_tien_do_de_hieu.md).

## candidate-20261031-hold-review

- User acceptance: **pending**. Continued implementation is authorized; personal
  review/acceptance of this or prior candidates has not been inferred.
- Image ID: `sha256:9da55946676d7edf4bf22b6186b541128b6631e68f10713922e54e3a01efc542`.
- Adds first-cause HOLD context, read-only post-HOLD assessment, received-data
  streaks, reason categories, manual blockers/checklist and transient telemetry
  outage fixtures. Review profile has 205 numeric fields including design settings.
- OPERATOR_REVIEW never authorizes resume: all review rows have
  automatic_resume_allowed=false and restart_command_issued=false. No reset/resume API.
- Default profile remains fixed-cap with assessment disabled; review is opt-in.
- PASS in final image: 82 logic tests; 10 review fixtures, all without restart;
  78 robustness fixtures; 9 adaptive smoke; 15 fixed-policy regressions; default
  demo DONE/placement=true; strict HOLD. Host delivery boundary checks: 2 PASS.
- 78 full controller.jsonl traces match the earlier robustness candidate byte
  hashes exactly, not just aggregate counts. The assertion is fixture-specific.
- Transient feed/TRACK outages reach OPERATOR_REVIEW while controller stays HOLD;
  persistent outage waits for observations; sensor/sequence/feedback/expired-review
  cases require manual intervention. This is not successful autonomous recovery.
- Plant, estimator, predictor, supervisor, sensing and policy source hashes are
  unchanged from adaptive candidate. Sequence adds context logging; config/network
  add optional outage/review settings; experiment wires the read-only observer.
- Timing/fixtures are simulation-only, with 1 s functional predictor budget; no
  physical safety, 20 ms deadline, full CAD V5 synchronization or real PLC feedback.
- Accepted image and five earlier candidates verified unchanged. No public push,
  accepted tagging or remote CI run. All final runtime hashes match workspace.
- [Evidence/hashes/results](evidence/candidate-20261031-hold-review.json),
  [guide/functions/limits](../docs/hold_recovery.md),
  [progress index](../docs/dt_core_progress.md).

## candidate-20261031-adaptive-speed

- User acceptance: **pending**. Continued development authorization is not personal
  validation or approval to replace an accepted image.
- Image ID: `sha256:f6e7e1a8cd3cb9c1910cb6687a7be66fdc1a01742c9afb33c07487cc3d6654e7`.
- Experimental observed-timing/uncertainty speed ceilings, current stop-margin
  budget from issued history, downward-only cap latch and no-admissible-speed HOLD.
  New adaptive profile/205-field CSV; three-policy 117-run plan and 9-run smoke.
- **Default remains fixed-cap** `reconfigurable_cell_20261030.json`. Adaptive is
  explicit opt-in through adaptive-check/profile; it is not promoted as better.
- PASS in final image: 74 logic tests; 117 study runs under terminal support/
  placement, cap and logging criteria; 9 adaptive smoke; 6 previous robustness
  smoke; 15 fixed-policy regressions; default fixed-cap demo DONE/placement=true;
  strict HOLD. Host delivery checks: 2 PASS.
- Counts over 39 runs/policy: disabled 16 DONE/23 HOLD; fixed 19/20; adaptive 15/24.
  The negative completion result is retained. All runs meeting criteria does not
  mean all complete production or demonstrate calibrated uncertainty/safety.
- In delay20/seed0, fixed is 14.60 s, adaptive 14.26 s (0.34 simulated s shorter).
  This fixture benefit does not offset the evidence of more HOLD under jitter/loss.
- Study compute budget explicitly 1 s; not 20 ms qualification. Observed timing
  maxima and default zero age guard do not guarantee future timing bounds.
- Source hashes matched workspace. Sequence/pickup gates, estimator, predictor,
  supervisor, sensing and physical plant source hashes are unchanged from the
  previous candidate. Config/experiment/policy/driver changes are recorded separately.
- Accepted core-v1 and four prior candidate image IDs verified unchanged. No
  registry push, accepted tagging, automatic recovery or remote CI run.
- [Full evidence](evidence/candidate-20261031-adaptive-speed.json),
  [formulas/functions/results](../docs/adaptive_speed.md),
  [progress index](../docs/dt_core_progress.md).

## candidate-20261031-robustness

- User acceptance: **pending**. "tiếp tục đi" authorizes the next work; it is not
  personal validation of this or prior candidates.
- Image ID: `sha256:31f56fd0c6aa724efaed3148f7df89fa8f7e21c23994062fe7e804cdfbf0169e`.
- Adds configurable paired experiment plans, full 78-run study, 6-run smoke plan,
  source-aligned empirical error-bound coverage, incremental Markdown/CSV/JSON
  reporting, preserved failures and external read-only plan selection.
- Control core hashes are unchanged from the reconfiguration candidate. Default
  runtime profile remains `reconfigurable_cell_20261030.json`; no threshold tuning.
- PASS in final image: 68 logic tests; 78 full matrix runs under terminal
  support/placement, speed-cap and logging criteria; 6 smoke runs; 15 policy
  regressions; default demo DONE/placement=true; strict HOLD. Host delivery: 2 PASS.
- Full matrix (39 runs per policy): disabled 16 DONE/23 HOLD; enabled 19 DONE/20
  HOLD. **Not all 78 runs complete production.** Jitter seed2 has disabled DONE
  and enabled HOLD; the adverse case is retained. No superiority/accuracy claim.
- Empirical source-aligned error samples within engineering bounds: disabled
  2905/2905; enabled 3224/3224. Correlated, uncalibrated finite-fixture observations;
  not a statistical guarantee. Study predictor compute budget is explicitly 1 s.
- No 20 ms realtime qualification, physical validation, automatic HOLD recovery,
  sensor replacement, multi-product testing or full CAD V5 synchronization claimed.
- All runtime hashes matched workspace; accepted core-v1 and three prior candidate
  images verified unchanged. No registry push, accepted tagging or remote CI run.
- [Evidence/hashes/results](evidence/candidate-20261031-robustness.json),
  [guide and interpretation](../docs/robustness.md),
  [progress/functions](../docs/dt_core_progress.md).

## candidate-20261030-reconfiguration

- User acceptance: **pending**. User requested continued implementation and Markdown
  descriptions of completed work/functions, not personal acceptance of a candidate.
- Image ID: `sha256:1eaf75229e7080cb3ea585c846a9960bc246e37c7e4dc7b5b20228e552463200`.
- Default profile: `reconfigurable_cell_20261030.json`; 202 numeric fields including
  three new policy settings and design parameters. Previous profiles are unchanged.
- Adds receiver-evidence policy: NORMAL → DEGRADED speed cap, per-cycle latch,
  health-triggered HOLD, retained vacuum command and no automatic HOLD reset.
  Sequence and predictor still have priority to stop. No sensor bypass/ML/RL.
- PASS in final image: 63 logic tests; 15 reconfiguration cases; 13 observer cases;
  18 parameterized-model functional cases with explicit **1 s** compute budget;
  10 legacy predictive cases; default demo DONE/placement=true; strict HOLD for
  unconfirmed XY/intermediate A2/vacuum. Host delivery checks: 2 PASS.
- Matched 20 ms delay fixture: policy disabled at 0.16 m/s HOLD on pick uncertainty;
  enabled policy caps to 0.12 m/s and finishes. Fixed 0.12 m/s also finishes in the
  same 14.60 simulated seconds; this is not evidence of optimal throughput.
- Missing pickup edge fixture: health-triggered HOLD at ~6.96 s vs timeout ~7.58 s,
  **0.62 s earlier reaction after missing expected evidence**, not advance failure prediction.
- Runtime 20 ms case/default demo completed in this run. This does not remove the
  previous observer candidate's timing misses or qualify realtime reliability.
- Runtime source hashes matched workspace. Accepted core-v1 and both previous
  candidate image IDs were verified unchanged. No registry push/accepted tagging.
- Full checks, hashes and retained trial information:
  [evidence/candidate-20261030-reconfiguration.json](evidence/candidate-20261030-reconfiguration.json).
  [Guide/functions](../docs/reconfiguration.md), [project progress](../docs/dt_core_progress.md).
- No physical calibration, continuous multi-product validation, automatic recovery,
  full MuJoCo predictive rollouts or full CAD V5 synchronization is claimed.

## candidate-20261030-observer-health

- User acceptance: **pending**. The message "ok tiếp tục đi" authorizes development;
  it is not personal validation of this new image or the previous parameters candidate.
- Image ID: `sha256:ccdc62250152215b7fd44c5a7f7fbd266d68587cdf41df87186a4579bd769e0c`.
- Scope: opt-in piecewise issued-command integration, two-anchor command gain,
  conservative delayed-data prediction, source-time admission compensation,
  variable-speed travel deadline, and receiver-only health hypotheses.
- Default profile: `observable_cell_20261030.json`; 199 numeric settings exported
  in the blank CSV, including design parameters. Previous profiles remain available.
- PASS: 57 logic tests in the image, 2 host delivery checks, 13 observer simulation
  fixtures, 10 legacy predictive fixtures, default demo DONE/placement=true, and
  strict mode HOLD for unconfirmed XY/intermediate A2/vacuum feedback.
- **Timing limitation retained:** original 20 ms measured-profile suite passed
  17/18; speed_low held on `prediction_deadline_exceeded`. A separate run of the
  same 18 fixtures with an explicit 1 s compute budget passed 18/18. This is
  functional regression evidence, not qualification of 20 ms realtime reliability.
  The 20 ms observer runtime case and default demo completed in their recorded runs.
- Health labels are ambiguous hypotheses; health does not automatically stop,
  bypass a missing sensor, clear HOLD, or restart the system. No hardware validation.
- Source hashes matched workspace. Prior accepted-core-v1 and parameters-candidate
  image IDs were checked and are unchanged. No registry push or new accepted tag.
- Full evidence, hashes, retained failures and output locations:
  [evidence/candidate-20261030-observer-health.json](evidence/candidate-20261030-observer-health.json).
  Guide: [observer/health](../docs/observer_health.md).
- CAD V5 and the functional MuJoCo model remain different representations; no
  claim of full geometry/dynamics synchronization or calibrated uncertainty.

## candidate-20261030-parameters

- User acceptance: **pending**. Only the earlier core-v1 image is accepted.
- Scope: functional parameterized plant with the reported envelope, 60 mm workpiece,
  three optical roles, guarded sensor-based admission and finite-force suction footprint.
- 194 numeric fields are editable via profiles/CSV, including design settings; they
  are not 194 required physical measurements. Blank input remains unknown.
- Image ID: `sha256:a4b738583d27b30d6adb814d845e064f825232bb656b79d5bd3c3ed1fb0ba0ed`.
- PASS in final Docker image: 43 logic tests, 18 parameterized-profile cases, 10
  legacy predictive cases, and the default demo with placement=true. Host delivery
  boundary checks: 2 PASS. Runtime source hashes matched the workspace.
- New matched geometry comparison: nominal cycle difference **0 s**, pickup-fault
  earlier HOLD **0 s**; both supervisors hold through the tracking timeout in that
  fixture. The 40 ms observation from the old geometry is not transferred to this one.
- Full source/image/check record: [evidence/candidate-20261030-parameters.json](evidence/candidate-20261030-parameters.json).
- Detailed instructions: [parameterized core](../docs/parameterized_core.md).
- This shares measured envelope dimensions with CAD V5 but is not a full CAD/V5
  dynamics synchronization or physical calibration. Two failed development grasp
  trials are retained and listed in the evidence record.
- Accepted core-v1 tag and image ID remain unchanged. No image registry push occurred.

## accepted-20261030-core-v1

- User acceptance reference: message on 2026-10-30 starting "rất tốt, giờ hãy tiếp tục
  hoàn thành dự án phần lõi dts" immediately after candidate Docker delivery.
  Acceptance applies to the existing Docker/core delivery, not future measured geometry.
- Immutable image: `sha256:23ba06be2d283f73032a7f27294cccb040a72142cc42f48f506bd0ecb6892bb8`.
- Rechecked 2026-10-30: 10/10 predictive cases PASS, with original source hashes
  preserved in `evidence/candidate-20261029.json`.
- New check evidence: `output/docker/predictive-check_20261030T145342Z_2f9535fc/`.
- This accepted tag remains unchanged while measured-profile work is a new candidate.

## candidate-20261029

- Scope: existing modular DT core and headless MuJoCo; external profiles and output logs.
- User acceptance: accepted on 2026-10-30 as `accepted-20261030-core-v1` above.
- Automated checks: **PASS** — 2 delivery-boundary tests; 36 logic tests inside
  final container; 12 baseline MuJoCo cases; 10 predictive paired cases; one demo
  using the read-only mounted slow-A2 profile and destination bin 3 (DONE, placement=true).
- Image ID: `sha256:23ba06be2d283f73032a7f27294cccb040a72142cc42f48f506bd0ecb6892bb8`.
- Runtime: Linux/amd64, Python 3.12.16, MuJoCo 3.16.0, NumPy 2.5.4.
- Preserved image/source/test record: [evidence/candidate-20261029.json](evidence/candidate-20261029.json).
- Full local logs and effective profiles: `output/docker/`; qualification record
  at `output/docker/qualification_20261029/report.json`.
- Image source hashes matched the workspace after container testing. No source
  code bind mount was used; only external profiles and output directories were mounted.
- GitHub Actions job is configured locally; no remote CI run or registry push occurred.
- Geometry: simulation baseline unchanged; measured CAD V5 is not merged into this image.

Future entries must identify the item accepted by the user, the acceptance message/date,
immutable image ID, preserved source manifest, and the tests actually run.
