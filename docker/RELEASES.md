## candidate-20261104-sensor-drive-v2 — 2026-11-04

- User acceptance: **pending**. Final seven-case, 21-trial virtual sensor/drive study uses unique opaque UUID4 session contexts; fault names remain in evaluator/fixture metadata only.
- Image ID: `sha256:8a7dbd9f1f9962df23ae18a1008f31968cb19ed02f6186f2f194df862679032a`. Existing runtime/control/estimator/profile source hashes remain unchanged.
- PASS: 143 core tests, 8 web tests, integration-check; 21 trials completed, six paired input/decision collisions, 21 evaluator position-support checks. No physical safety or diagnostic-accuracy claim.
- Compared to the retained pilot: all 21 observation traces and 21 logical decision traces match after excluding prediction compute duration. Pilot session strings included fixture names; final study rerun to remove that metadata channel.
- Timing interpretation separates injection from first hidden ideal-sensor disagreement. Ground-truth poses and applied-drive overrides remain outside the core. Three repeated deterministic trials are not independent physical systems.
- Prior image IDs and accepted defaults preserved; no accepted/stable/latest promotion or registry push. CAD V5 is not silently declared synchronized with MuJoCo.
- [Evidence](evidence/candidate-20261104-sensor-drive-v2.json); [Vietnamese report](../docs/nghien_cuu_cam_bien_va_truyen_dong_20261104.md).

## candidate-20261104-sensor-drive — 2026-11-04

- User acceptance: **pending**. Seven controlled virtual sensor/drive cases, three repeats each, with fault labels/applied-drive overrides/plant poses outside the RuntimeCore input boundary.
- Image ID: `sha256:94cc89a803810ede646e2b4c7c261609bd9e7ce67702d2529bd250c2e34a917b`. Existing runtime/control/estimator/profile source hashes unchanged; new study, plan and tests only.
- PASS: 143 core tests, 8 web tests, integration-check and 2 host delivery checks. All 21 planned trials completed; all non-baseline fixtures triggered; independent position-support criterion true after HOLD in 21/21, not a physical safety certificate.
- Six paired counterexamples have identical sensor and logged decision histories through first HOLD, while evaluator pose separation is about 0.354 m (feed) and 0.248 m (pickup). Does not establish sensor-versus-drive fault isolation or classification accuracy.
- Latency is fixture/event dependent. Separate injection-to-HOLD and hidden ideal-sensor-disagreement-to-HOLD timestamps; neither is CPU latency or a clock visible to the core. Three repeats are not independent physical systems.
- Prior image IDs including the accepted version preserved. Accepted defaults unchanged; no registry push. CAD V5 still differs from the evaluated MuJoCo geometry.
- [Evidence](evidence/candidate-20261104-sensor-drive.json); [Vietnamese report](../docs/nghien_cuu_cam_bien_va_truyen_dong_20261104.md).

## candidate-20261104-time-boundary — 2026-11-04

- User acceptance: **pending**. Shared inclusive elapsed-time comparison for Sequence and SignalHealth fixes one-sample silence-boundary delays from floating-point roundoff. Absolute numerical tolerance 1 ns; profile silence threshold remains 100 ms.
- Image ID: `sha256:538a4939d6c118bce51169e7975c2a36ccc8b8741284cea99070db496520a844`.
- All 9 software groups PASS: 141 core tests, 8 web tests, stream, integration, reset, background, boundary, qualification, stream archive. Two host delivery checks PASS. Fresh 18-trial study: 36/36 matching logical replays, injected-deadline negative control detected.
- Gap and long-delay trials: HOLD after fixture epoch 100 -> 80 ms; since the last valid pre-epoch packet 120 -> 100 ms. Speed reduction remains 20 ms. These are simulated-clock measurements, not PLC latency or diagnosis accuracy.
- Three delay-versus-loss pairs have identical normalized input/logical traces through HOLD. Root-cause discrimination is not established. Existing runtime changes limited to sequence.py/health.py; profiles and generated plant hashes unchanged.
- Prior image IDs including the accepted version preserved. Defaults still use the accepted version; no new accepted/stable/latest tag or registry push. CAD V5 remains distinct from the evaluated MuJoCo geometry.
- [Evidence and source hashes](evidence/candidate-20261104-time-boundary.json); [Vietnamese result](../docs/ket_qua_phan_ung_mang_20261104.md).

## candidate-20261104-mujoco-only — 2026-11-04

- User acceptance: **pending**. Unity scene/assets/C# and export paths removed from the active source. The unchanged 113-part CAD ledger now lives at `cad_reference/production_twin_v0_parts.csv`; a stdlib-only CAD exporter replaces the old export script.
- Candidate image: `sha256:19e62d5b7a616862c46b413e761a00c401cb2679741cce27bc3dd04565438254`.
- All 9 software groups PASS after migration: 135 core unit tests, 8 web tests, stream, integration, reset, background, boundary, qualification and stream archive. Two host delivery checks PASS.
- Post-migration demo: DONE, evaluator placement PASS, 13.92 s simulated under explicit open-loop assumptions. Legacy reconstruction compiles and matches the committed XML after newline normalization; original template is retained.
- Project is canonical on D. Ubuntu-24.04/Docker disk moved with native WSL tooling; stopped-disk SHA-256 identical before/after. All 19 previous Docker aliases and Python/MuJoCo/NumPy versions preserved. Accepted defaults unchanged; no registry push.
- Historical mixed delivery ZIPs are preserved outside the active project instead of being deleted; immutable image/source history is retained. CAD V5 is not silently declared synchronized with MuJoCo, and no physical verification is claimed.
- [Evidence and source hashes](evidence/candidate-20261104-mujoco-only.json); [Vietnamese guide](../docs/chuyen_sang_o_D_va_bo_unity.md).

## candidate-20261104-stream-evidence — 2026-11-04

- User acceptance: **pending**. Two additions: replay recorded stream ticks (including silence) through the shared core; transport a six-file ZIP with integrity verification. No controller tuning or physical output.
- Image ID: `sha256:568e54e2b6def4a568a3d45ee4b39cb20c099a7dfc89267a66e7549cd91d121b`.
- All 9 software groups PASS: 132 core tests, 8 web tests, loopback, integration, reset, background, 144-input boundary study, 24-run qualification, and stream archive checks. Two host delivery checks, PowerShell parse and JavaScript syntax also PASS.
- Three actual loopback sessions: 34 replay ticks each, 102 total, no logical differences; all three ZIP bundles verified. Six unit tests cover replay, tampering, changed source, missing final command, unsupported asynchronous observer, unsafe and duplicate ZIP names, and overwrite refusal.
- Runtime source manifest matches. All 16 previous aliases rechecked unchanged; accepted defaults retained. No registry push or new accepted/stable/latest alias.
- Replay excludes measured compute duration and refuses asynchronous-background sessions. Tests do not cover predictive TRACK trajectories or prove wall-time/physical reproducibility. Bundle hashes provide integrity, not sender authentication. CAD V5 remains distinct from MuJoCo.
- [Evidence and full source hashes](evidence/candidate-20261104-stream-evidence.json); [Vietnamese guide](../docs/phat_lai_va_dong_goi_phien.md).

## accepted-20261103-software-v2 — 2026-11-03

- User acceptance reference: message on 2026-11-03 (Asia/Saigon): **“ok tất cả mọi thứ đều ổ, hãy cập nhật vào docker”**. Applies to the immediately preceding software-v2 delivery; not physical validation.
- Immutable image: `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`. Accepted runtime source commit: `57a6509`. This is the exact candidate image the user reviewed, not a rebuilt substitute.
- Rechecked before promotion: all 8 software groups PASS — 126 core tests, 8 web tests, 3 loopback UDP fixtures, integration, reset, background, boundary (144 inputs) and qualification (24 runs). Two host delivery checks and PowerShell syntax check also PASS.
- Runtime source hashes match; prior accepted-core-v1 and all candidate IDs unchanged. No registry push, stable alias or latest alias.
- Execution defaults now select this accepted tag. Builds and CI continue to use candidate tags, and the build helper still rejects accepted tags.
- After tagging, the default PowerShell demo command also completes with evaluator-confirmed placement under its declared open-loop simulation assumptions.
- Build-time candidate labels remain immutable. Current user acceptance and source hashes are recorded in [the acceptance evidence](evidence/accepted-20261103-software-v2.json).
- Boundaries retained: no S7 driver or PLC actuation, no physical clock synchronization/calibration, no hard realtime claim; CAD V5 differs from the functional MuJoCo scene.

## candidate-20261103-software-v2

- User acceptance: accepted on 2026-11-03 as `accepted-20261103-software-v2` above. Six-item pre-hardware software batch: loopback tag input, validation/watchdog, UDP fixtures, diagnostics UI, combined checks and parameterized provenance.
- Image ID: `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
- PASS: all 8 combined groups; 126 core tests, 8 web tests, 3 real loopback UDP fixtures, integration, reset, background, 144-input boundary study, and 24-run qualification. Two host delivery checks also pass.
- Earlier WSL run failed one core test because its fixture reused equal decision times. Failed run retained; fixture fixed and entire final Docker suite rerun. No parameter tuning or hidden acceptance.
- Gateway stamps local reception time, retains session/order guards and checks silence with no incoming packet. Output commands are written only to files. This is not an S7 driver, PLC connection, physical clock synchronization or actuation.
- Dashboard reviewed in browser: latest PASS and earlier failed run both displayed. No hard realtime or physical validation claim. CAD V5 remains distinct from the functional MuJoCo model.
- Source hashes match; all prior image IDs preserved. No new accepted/stable/latest tag or registry push.
- [Evidence and source hashes](evidence/candidate-20261103-software-v2.json); [Vietnamese guide](../docs/phan_mem_truoc_khi_do_may.md).

## candidate-20261103-boundary-study

- User acceptance: **pending**. New exploratory fixed-grid tool only; no controller parameter fitting or actuation changes.
- Image ID: `sha256:b5deba36508289c5c2c1c13bd13418622540ceae7e310c64fa94456131d86a14`.
- PASS: 119 core tests, 2 host delivery checks, integration-check, and all 144 planned boundary inputs complete. No full-versus-forward constraint invariant violations.
- Results: 138 matching decisions, 3 reduced-CONTINUE/contact-HOLD, 3 reverse. Forward-only and full-contact actions match in this grid; not a universal removal of lateral/vertical constraints.
- Local/Docker comparison: 144 inputs, matching actions and maximum margin difference 0.0 m at tolerance 1e-9 m. This is software reproducibility, not physical accuracy.
- Separate post hoc local sensitivity: 24 selected inputs at 1/2/4 ms, retaining a 20 ms control interval. One near-zero contact margin changes sign. Not independent confirmation or convergence proof.
- Functional study allowance is 5 s, not realtime 20 ms qualification. Physical parameters are uncalibrated; no safety/diagnostic-accuracy claim.
- All prior image IDs including accepted-core-v1 and model-audit unchanged. No accepted/stable/latest tag or registry push. CAD V5 remains distinct from the evaluated MuJoCo scene.
- [Evidence and hashes](evidence/candidate-20261103-boundary-study.json); [Vietnamese report](../docs/bao_cao_bien_mo_hinh_20261103.md).

## candidate-20261103-model-audit

- User acceptance: **pending**. Offline same-snapshot model comparison; no actuation or default algorithm change.
- Image ID: `sha256:9759ff58df75954b550b111ea7f4001c761b63d002d52a49d47cb12c642a0f46`.
- PASS: 116 image logic checks, 2 host delivery checks, background-check (three paced cycles plus worker-termination probe) and integration-check.
- Observer audit: 24 complete pairs, 22 admitted and 2 discarded at receipt; all 24 have matching model actions in this fixture. Incomplete-worker audit excludes all 82 replies from agreement counts. Not physical accuracy.
- All three control traces match and placement checks pass. Timing limitation retained: incomplete-worker foreground call maximum 32.749 ms, 1/697 steps over 20 ms. No hard realtime qualification.
- Runtime source hashes match; every previous image ID, including the accepted image and background-observer, remains unchanged. No accepted/stable/latest tag or registry push.
- CAD V5 remains different from the functional MuJoCo model; no physical calibration.
- [Evidence and hashes](evidence/candidate-20261103-model-audit.json); [Vietnamese guide](../docs/doi_chieu_du_bao.md).

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


## 2026-11-05 — Anatomy interactive explainer (candidate)

- Tag: `production-twin-dt:candidate-20261105-anatomy`.
- Image ID: `sha256:c854829373ce629b9e273a313b1d9cbcbe63df7e8416a44f66d1217f7cf49d40`.
- User acceptance: **pending**. No accepted/stable/latest tag changed; no registry push.
- Evidence: `docker/evidence/candidate-20261105-anatomy.json` records runtime and authoring hashes, 30 source-study hashes and unchanged accepted image.
- Checks: 10 web tests in read-only/network-none container; image/runtime hashes match host; all 113 prior MuJoCo files unchanged. Browser: 21 representative poses, seek/play/pause/first-HOLD, comparison, light/dark, explanation buttons; clean console; phone 390 px and 4× close-up inspected. Line-end 0/0 because there are no separate texture lines. No mechanical assembly audit claimed.
- Scope: 67 SVG solids, 1,973 samples from trial 01 of seven existing `sensor_drive_20261104_v2` cases. Offline recorded replay; no new physical claims, network-fault experiment or PLC output. Robot and pusher remain reference poses because joint feedback is not logged. CAD V5 remains different from MuJoCo.
- Last accepted remains `accepted-20261103-software-v2`, image `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
- Source and logs: `output/anatomy_20261105`; instructions `docs/truc_quan_anatomy.md`. Runtime open: `web/anatomy.html` directly, or host `python web/server.py --port 8766` and `/anatomy.html`. Rebuild with explicit `python docker/build_image.py --tag candidate-20261105-anatomy`; normal accepted defaults are preserved.


## 2026-11-05 — Prediction/observation residual and scope cleanup (candidate)

- Tag: `production-twin-dt:candidate-20261105-residual-focus`.
- Image ID: `sha256:29d160c2541cfe45a7a6f02938de5ce6394ca46031e824ce687eb6a270eda34a`.
- User acceptance: **pending**. No promotion or registry push. Last accepted remains
  `accepted-20261103-software-v2` (`sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`).
- Checks: 147 core tests, 10 web tests inside the candidate; two host delivery checks.
  Full runtime manifest matches host; all 113 pre-existing MuJoCo files remain unchanged.
- Study: 21 existing sensor-drive recordings × two fixed engineering-bound variants;
  advisory causal replay, current command recorded after the same-tick observation.
  Plant truth is evaluator-only. No feedback from this monitor to RuntimeCore/PLC.
- Pilot/final results and every parsed JSONL row match exactly. Raw byte comparison
  initially failed on CRLF vs LF; source-location verification also required the
  documented /app/output → output/docker volume mapping. Original logs retained;
  no trial or threshold altered to resolve either verification issue.
- Narrow assumed interval reports the missing pickup edge at 6.84 s vs the single-event
  fixed timeout at 6.86 s; broad profile interval does not report before the old 6.96 s
  HOLD. No productivity gain, learned ML, calibrated confidence or fault isolation claimed.
- Evidence: `docker/evidence/candidate-20261105-residual-focus.json` (runtime hashes,
  complete study summary, input manifest, volume mapping and checks).
- Source/replay: `mujoco/innovation.py`, `mujoco/study_residual.py`,
  `mujoco/experiments/residual_20261105.json`; outputs `output/docker/residual_20261105_final`,
  logs `output/residual_validation_20261105`; plain Vietnamese report
  `docs/sai_lech_du_doan_quan_sat.md`.
- Cleanup changes authoring tree only: duplicate draft sources, obsolete PDFs and temporary
  verification copies removed after SHA-256-verified private archival. Active paper,
  CAD, parameter profiles, experiment evidence and accepted images preserved.


## 2026-11-05 — Optical interval calibration (candidate)

- Tag: `production-twin-dt:candidate-20261105-interval-calibration`.
- Image ID: `sha256:a2221c62dc831f5c9dab9337075af6250ed88dfeaa2f77b771c518830404cbbe`. User acceptance **pending**; no registry push/promotion.
- Checks: 149 core tests, 10 web tests; 37 run result JSONs and independent analysis
  reproduced exactly from WSL pilot; runtime hashes match host, 117 prior MuJoCo files
  unchanged. Last accepted `accepted-20261103-software-v2` remains
  `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
- Nine normal calibration fixtures seal bounds before 8 held-out normal, 16 fault
  and 4 shifted-condition fixtures. Only optical transitions and command integrals fit
  gain; true pose/gain are evaluator-only. Drift remains a prior engineering assumption.
- Zero alerts on eight held-out normal fixtures, 766/766 anchored sample coverage;
  16/16 fault alerts but 160–260 ms slower than fixed single-event timeout. No throughput
  superiority, fault isolation, physical confidence, diagnostic ML or PLC authority claim.
- Post-hoc same-drift ablation is explicitly disclosed: fitted gain bounds reduce mean
  width 5.1% (80.9→76.8 mm); comparison with full old profile confounds drift selection.
- Evidence: `docker/evidence/candidate-20261105-interval-calibration.json`, source manifest,
  sealed calibration SHA-256 and per-input analysis hashes. Data/logs under
  `output/docker/interval_calibration_20261105_final` and
  `output/interval_calibration_validation_20261105`; report
  `docs/hieu_chuan_mien_du_doan_20261105.md`.


## 2026-11-05 — Upstream pulse observer (candidate)

- Tag `production-twin-dt:candidate-20261105-pulse`, ID `sha256:a3535b3c17d167fd80c3148272be8852870e029e7f09faae91cd362d966d91a3`.
- User acceptance pending; no registry push/promotion. Last accepted ID remains
  `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
- 151 core tests, 10 web tests; 28 fresh-condition run results exactly reproduced
  from WSL pilot; 112 observation/command/evaluator/decision JSONL files byte-identical.
  Runtime manifest matches host and 121 pre-existing MuJoCo files unchanged.
- Pulse-only gain fit uses the complete upstream pulse and issued command integral,
  before the target event; fixed size/shape guard and drift remain uncalibrated assumptions.
- Normal interval width 52.6 vs 77.4 mm, 786/786 covered samples. Only 8/16 fault
  trials alerted in window versus 16/16 pulse-informed timeout; observed alerts 60–120 ms
  later. No superiority, PLC continuation, diagnostic ML, confidence or productivity claim.
- Evidence `docker/evidence/candidate-20261105-pulse.json`; data
  `output/docker/pulse_20261105_final`, logs `output/pulse_validation_20261105`;
  report `docs/du_doan_tu_xung_PS2_20261105.md`.


## 2026-11-05 — Pulse evidence validity under scheduled packet impairment (candidate)

- Tag `production-twin-dt:candidate-20261105-pulse-network`, ID `sha256:0e87787d426182f7884829b152e2a2d7371929bac8be16f07ed9225bcc1cc444`.
- User acceptance pending. No registry push/promotion; accepted remains
  `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
- 152 core tests, 10 web tests. 168 scheduled replays and 168 JSONL logs
  logically match host pilot; runtime hashes match host. Intentional changes
  to prior source: pulse_observer.py and test_pulse.py; other prior files unchanged.
- Evidence eligibility is separate from stored pulse fit. History loss is latched
  for the single-product observer; source-time predictions are labeled with age.
- Immediate/40ms: 8/16 model alerts and 16/16 pulse-timeout alerts. Combined 16/16
  preserves attribution; extra timeout alerts are not credited to predictive DT.
  120ms rejects stale inputs; gaps reject pulse/history availability. No UDP,
  closed-loop recovery, productivity, physical calibration or PLC authority claim.
- Receipt `docker/evidence/candidate-20261105-pulse-network.json` contains source
  and recording hashes and the study input manifest. Logs/data:
  `output/pulse_network_validation_20261105`, `output/docker/pulse_network_20261105_final`.


## 2026-11-06 — Closed-loop stopping segment (candidate)

- Tag `production-twin-dt:candidate-20261106-closed-loop`, ID `sha256:3964d237420b537621695b535de8e79fb0a4161b91ac405288fa56b6cffeb1b8`.
- User acceptance pending, no registry push/promotion. Accepted remains
  `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
- 154 core tests, 10 web tests. 144/144 final summaries match corrected pilot_v2;
  runtime manifest matches host, prior MuJoCo files unchanged. Compute deadlines
  remain active in decisions; zero forecast overruns recorded in this matrix.
- Three same-signal policies, two provisional stop zones, speed/gain/delay and missing
  target feedback. Predictive selection integrates past commands for age propagation;
  adaptive reference timeout integrates its actual issued slowdown.
- Missing PS3: 0/24 predictive upper-bound exceedances vs 15/24 sequential and 24/24
  chosen age-rule. Tight healthy zone: predictive 2/12 confirmed completions vs 12/12
  age-rule. Strict completion requires PS3, so missing-sensor completed cycles remain 0
  by design; no bypass, recovery or full-production superiority claim.
- Original pilot contained an adaptive-timeout bug; retained but excluded. Corrected
  pilot and final use a regression test. No post-result threshold adjustment.
- Evidence `docker/evidence/candidate-20261106-closed-loop.json`, data/logs
  `output/docker/closed_loop_segment_20261106_final`, `output/closed_loop_validation_20261106`;
  report `docs/thu_kin_doan_bang_20261106.md`.


## 2026-11-06 — Alternative confirmation qualification (candidate v2)

- Corrected tag `production-twin-dt:candidate-20261106-confirmation-v2`, ID
  `sha256:a9bde45902a5d0852a3a6548e4b68608ba2e1039aeba317fc4576e41b60227e5`. User acceptance pending, no registry push/promotion.
  Accepted unchanged: `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
- 155 core tests, 10 web tests; 72/72 summaries and corrected audit run/pair
  values match pilot. Runtime hashes match host. Prior-source intentional
  change is study_closed_loop_segment.py (plant-side drive-stall fixture);
  existing controller/runtime/parameter profiles preserved.
- Read-only gate requires full model interval inside provisional zone plus verified
  prerequisites for release. No prerequisite verification supplied in this study.
- 24/24 sensor-missing/stalled-drive pairs share observations/logical decisions while
  final position differs 191–271 mm. Corrected gate finds 0/72 conditional positions
  eligible (interval outside zone), releases 0; not a 100% accuracy/safety claim.
- Superseded pilot tag candidate-20261106-confirmation, ID
  sha256:663ace05c41d3002f429b7742683f61cdbb99a1b4583dd336aef664fc1cdbe84,
  retained with original evidence: its stop-maintenance gate incorrectly included
  speed immediately before stop. It is NOT the version to approve. Boundary regression
  test fixes caller use of CommandHistory; no shared-history semantics changed.
- Evidence `docker/evidence/candidate-20261106-confirmation-v2.json`; source/data
  `output/docker/confirmation_20261106_final_v2`, audit
  `output/docker/confirmation_20261106_audit_v2.json`, logs
  `output/confirmation_validation_20261106_v2`. Report
  `docs/xac_nhan_thay_the_20261106.md`. No actual bypass/PLC/full-cycle recovery.


## 2026-11-06 — First trained Ridge ETA residual model (candidate)

- Training tag `production-twin-dt:candidate-20261106-eta-ml`, ID
  `sha256:37c1baadcc5532b1cb30f1651f02a4d1dada10ca084de5782d661d0378d87289`.
  158 core tests and 10 web tests; 61 normal segment runs (32/8/8/9/4 split),
  122 observation/command input hashes checked. Original pilot errors reproduce
  within 1e-8 ms. A failed fixture attempt before train_00 is retained separately.
- Delivery v2 tag `production-twin-dt:candidate-20261106-eta-ml-v2`, ID
  `sha256:1ef90f0e2033fe5c7cce1c2928003530b379c1d262314c6a0442fd091e9f5352`.
  **159 core tests and 10 web tests**; runtime hashes match host; packaged frozen
  model bytes match the training artifact. Adds pulse-only advisory API and ships
  trained weights/envelope/provenance; no retraining or test-driven tuning.
- Receipts `docker/evidence/candidate-20261106-eta-ml.json` and
  `docker/evidence/candidate-20261106-eta-ml-v2.json` record image IDs, hashes and checks.
  Data: `output/docker/eta_ml_20261106_final`; logs:
  `output/eta_ml_validation_20261106`, `output/eta_ml_delivery_v2_20261106`.
- Test MAE: nominal 105.7 ms, pulse 98.5 ms, train-mean correction 18.1 ms,
  Ridge 15.4 ms (n=9). Shifted: Ridge 38.3 ms vs constant correction 28.5 ms
  (n=4). Constant reference added post hoc, uses training rows only. Recording
  audit finds only 16/4/4/9/4 distinct pairs within the splits, no cross-split
  overlap; duplicate friction variants are not independent observations.
- Empirical 65 ms calibration envelope is not a statistical coverage guarantee.
  No trained fault classifier, control-policy integration, PLC writes or physical
  validation. Paper/report updated separately from runtime build.
- User acceptance pending. No promotion/registry push. Accepted image remains
  `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.


## 2026-11-06 — Advisory learned event monitoring (candidate v2)

- Current tag `production-twin-dt:candidate-20261106-eta-monitor-v2`, ID
  `sha256:3cbaf0f3eade0662ad7554f061270e514d6edf2a2aa8d86d45f4de7de1d14069`.
  165 core tests, 10 web tests; runtime source hashes match host, prior runtime
  files from ETA-ML-v2 unchanged. All 62 input hashes verified; 465 replay
  summaries reproduce the initial pilot decisions. New model weights were NOT
  trained or tuned in this item. Calibration radii are separately frozen per method.
- Adds advisory EtaEventMonitor around PulseObserver: pre-target ETA windows,
  source-timed early/late/missing findings, data-availability reasons, shared domain
  gates and engineering fallback. v2 also rejects old empirical windows after a
  change of product length, sensor gap or sampling period. No central RuntimeCore
  policy integration, PLC writes or physical validation.
- Initial tag `production-twin-dt:candidate-20261106-eta-monitor`, ID
  `sha256:9f8237e7aceaf3997a2d05e839a3fc924e1e7308c3f7a68b9c5c15cbcf5e997a`,
  passed164/10, retained with its evidence. It predates the calibration-context
  guard; v2 is the version for review, not the initial tag.
- 31 recordings (13 existing normal/shift,18 new fault segments), three methods,
  five scheduled delivery cases. 465 replays are not independent trials. Nine
  missing-target/stalled-drive pairs have identical inputs. Both corrected methods
  flag18/18 faults under immediate and40ms delivery; no-delay normal findings0/9.
  Two delayed pulse cases lack a late confirmation window before recording end.
- Compared with constant correction, Ridge is equal in2 and20–40ms later in16
  immediate fault replays, earlier in0. Stale/gapped/bad-quality evidence is rejected;
  rejection is not credited as fault detection. No overall superiority claim.
- Receipts `docker/evidence/candidate-20261106-eta-monitor.json` and
  `docker/evidence/candidate-20261106-eta-monitor-v2.json`; final data
  `output/docker/eta_monitor_20261106_final_v2`, logs
  `output/eta_monitor_validation_v2_20261106`. Report:
  `docs/giam_sat_eta_ml_20261106.md`.
- User acceptance pending, no registry push or promotion. Accepted ID remains
  `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.


## 2026-11-06 — Focused event-monitoring delivery (candidate)

- Tag `production-twin-dt:candidate-20261106-monitoring-focus`, ID
  `sha256:e84f9fa4c7707a85daea79c0f6ea07be41cf4227bbe080230009d07f150ed8f3`.
- Explicit 32-file source context in research_scope.json; includes generic event
  kernel, predictor alternatives and MuJoCo case-study dependencies. Excludes web,
  CAD-authoring, RuntimeCore, full-cell reconfiguration and whole-cell forecasts.
  Full repository/core/profiles and historical evidence remain preserved.
- 13 focused tests in Docker, 168 full-core tests in WSL, 3 delivery-boundary tests
  on host. Runtime hashes match. All 61 original training-record results reproduce
  exactly; all 465 monitoring summaries AND complete decision logs match the prior
  monitoring-v2 study. This is refactor reproducibility, not additional independent
  experiments or a second-machine validation.
- Candidate adds process-independent EventWindow and reuses it from the optical
  adapter. Named-event contract checks are software checks only. Learned Ridge
  remains an ablation; no claim it improves warning timeliness over constant bias.
- Receipt: docker/evidence/candidate-20261106-monitoring-focus.json; run logs:
  output/monitoring_focus_validation_20261106; data:
  output/docker/monitoring_focus_ml_20261106 and output/docker/monitoring_focus_20261106.
- User acceptance pending. No image promotion or registry push. Accepted remains
  `sha256:0115d22bc509e55536ae4f2facc3e9812ce5540f0a4b5daa6099761d7424f3d8`.
