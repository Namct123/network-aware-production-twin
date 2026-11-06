# Evidence and writing record — 2026-11-03

Status: assistant-inspected working draft; accountable human verification and author approval pending.
No source is marked human-verified. No manuscript was sent to an external drafting or typesetting service.

## Pre-hardware software rehearsal — E008

The final candidate evidence records eight combined groups, including 126 core and
eight web tests and three real loopback UDP fixtures. Input normalization and command
logs use existing recorded-input semantics; no hardware clock synchronization, S7
driver or PLC actuation is claimed. The initial local core-test failure from reused
fixture decision times is retained; the final complete Docker run passes. C024 binds
these software observations, not physical detection accuracy or process availability.

## Exploratory boundary grid — E007

Source: docker/evidence/candidate-20261103-boundary-study.json. The fixed 144-input
grid is distinct from full production cycles and from the earlier nominal snapshot
audit. C023 reports 138 agreements, three disagreements in each direction and zero
constraint-ablation invariant failures. Neither model is treated as physical truth.
The subsequent 24-input step-size study was selected after observing disagreements;
its 72 evaluations are post hoc sensitivity work, not independent validation or a
convergence proof. At one input, the sign changes between 1 and 2/4 ms. Reaction
cutoff quantization changes too. No stopping parameter is tuned or threshold chosen
from this grid. Source/result hashes and preserved image IDs are bound in E007.

## Offline model-decision audit — E006

Source: docker/evidence/candidate-20261103-model-audit.json, with runtime hashes
and separate background-cycle records. The native-optimization and earlier background
campaigns remain separate. C022 reports 24 complete pairs (22 admitted, 2 discarded),
82 excluded incomplete replies, and the retained 32.75 ms maximum in the incomplete
worker cycle (1/697 foreground calls above 20 ms). Offline 1D replay disables only
its computation clock. It is not the actual foreground decision trace, calibration,
physical accuracy, or a justification to apply old contact forecasts. Bibliography
remains 12 published papers; removed repository/API entries are not reinstated.

## Bibliography revision requested by the user — 2026-11-03

Removed former entries 7 (project software repository) and 8 (MuJoCo API documentation)
and their in-text citations. Internal experiment provenance is preserved; no unrelated
paper is substituted as proof of the native API implementation. Historical E107 below
is retained as a development note, not an active manuscript citation.
Added six published papers: Negri 2017, Uhlemann 2017, Cimino 2019, Jones 2020,
Fuller 2020 and Rasheed 2020. The bibliography now contains 12 published papers.
Crossref records are saved in literature_metadata_20261103.json; primary-source URLs,
locators, retrieval limitations and claim scope are in literature_sources_20261103.json.
New paragraph groups C019-C021 explain prior work and this project's narrower scope.
No unsupported universal literature-gap claim is made. Abstract, experimental results
and blank physical sections are preserved.
Public titles/URLs were used for literature verification; LaTeX runs locally and downloads only package resources.
The project was previously authorized by its owner for public GitHub publication; this remains an explicitly
unfinished, non-submission-ready draft. Authorship, funding and disclosure decisions remain unfilled.

## Local evidence

- E001: docker/evidence/candidate-20261102-qualification.json, copied here as qualification_20261102.json.
  The qualification object is the Docker study, distinct from local_qualification. It supports only finite-fixture
  timing/outcome claims: 24 runs, 18 completions, 6 supported holds, 15 measured calls per timing group.
- E002: implemented estimator, predictor, physics predictor, sequence, runtime, reconfiguration and study drivers.
  Equations describe the current history-enabled propagation and the reduced stopping surrogate, not an identified plant.
- E003: versioned reconfigurable profile and qualification plan. Dimensional entries are preliminary user reports;
  motion, friction, uncertainty allowances and test perturbations are design assumptions.
- Logic-check count: logic_checks.txt is copied from the completed container test log; 97 checks, not physical trials.
- SHA-256 identities are in source_manifest.json; paragraph-group hashes and support links are in claims.csv.
  These are draft traceability aids, not independent peer verification or a causal/statistical validation.

## Public literature inspected (2026-11-03)

- E101 Kritzinger et al., DOI 10.1016/j.ifacol.2018.08.474:
  https://repositum.tuwien.at/handle/20.500.12708/176517 . Institutional abstract/metadata plus the prior project
  retrieval record. Scope: integration-level model/shadow/twin distinction. The migrated metadata caveat is retained;
  no detailed full-text claim is inferred.
- E102 Hespanha et al., DOI 10.1109/JPROC.2006.887288:
  https://web.ece.ucsb.edu/~hespanha/published/ncs_v15p.pdf . Author manuscript, abstract and introduction;
  sampling, communication delay and dropout limitations. No performance numbers imported.
- E103 Yates et al., DOI 10.1109/JSAC.2021.3065072:
  https://arxiv.org/abs/2007.08564 . Author preprint abstract; time-stamped update freshness only.
  Published metadata carried forward from the earlier reconciled project bibliography; no theorem is transferred.
- E104 Ademujimi and Prabhu, DOI 10.3390/s22041430:
  https://pure.psu.edu/en/publications/digital-twin-for-training-bayesian-networks-for-fault-diagnostics/ .
  Author institution abstract, lines 17–22: equipment/DES co-simulation, fault interventions and Bayesian structure learning.
  MDPI direct access initially rate-limited; institutional abstract used rather than assuming full-text access.
- E105 Fu et al., DOI 10.1109/TASE.2025.3563320:
  https://arxiv.org/abs/2506.07332 . Author preprint abstract supports monitoring, optimization and generated simulation
  for dynamic line reconfiguration. No claim about neglected delays or exact physical abstraction is repeated.
- E106 Todorov et al., DOI 10.1109/IROS.2012.6386109:
  https://roboti.us/lab/papers/TodorovIROS12.pdf . Author-hosted paper, p. 1 abstract; multibody/contact simulation
  for model-based control. Does not validate today's installed version, parameter choices or this cell.

## Template and incomplete requirements

Official guidance checked: https://link.springer.com/series/558/information-for-authors-and-editors
and the linked Instructions for Authors PDF, sections 4.1–4.6 (template, headings, fonts, equations/tables).
The existing unmodified LNCS class is reused; Computer Modern-style LaTeX typography and its normal single-column
margins are retained. This is template-based drafting, not final venue compliance. Authors must review the eventual
venue's rules, bibliographic style, disclosures and accessibility requirements. Conference eligibility/acceptance is
not inferred. The abstract word count is checked locally and recorded in audit.json. It has no citations or displayed equations.

## Physical evidence boundary

The four physical-validation subsections contain no measurements, methods purportedly performed, numeric outcomes,
or substituted synthetic data. They retain blank vertical space. Preliminary geometry and simulator settings are
identified as such outside that section. No new optimization result or hardware advantage is invented.

Method clarification: the study toggles reconfiguration.enabled, which includes health-triggered HOLD as well as the fixed speed cap. It is not an isolated cap-only ablation. Table headers use module on/off accordingly.

## Native optimization addendum — 2026-11-03

The later E005 background-observer evidence is separate from the native timing
campaign. It records three paced virtual cycles, one per condition, identical
compared traces, admitted observations and discarded incomplete output. Foreground
step timing excludes plant integration and I/O. Background results cannot actuate.
The worker-termination probe checks a foreground call, not a physical recovery.
Source hashes and candidate image ID are bound in source_manifest.json. Human
claim verification and submission approval remain pending.

E004: docker/evidence/candidate-20261103-native-physics.json, copied as native_20261103.json;
only the final-image optimization object is used in the new table. Its 12 fixtures are each checked
at 1/4/8 workers, not treated as independent physical trials. Prior 2 November timing/outcome tables
are retained as the earlier campaign. New times are not substituted into that earlier record.
The failed first native-profile integration and its shared unit-declaration fix remain in the project log.
E107: https://mujoco.readthedocs.io/en/stable/python.html#rollout , rollout section inspected on 2026-11-03;
installed MuJoCo 3.16.0 Python signatures and source inspected locally. Supports native stepping loops,
homogeneous model batches and separate MjData instances for configured workers. Numerical agreement,
timing and deadline outcomes are supported by local evidence, not inferred from the documentation.
Human source verification and author approval remain pending. Physical sections remain blank.


## Learned ETA residual and later virtual controls — 2026-11-06

E009 binds trained Ridge weights and the 61-run 32/8/8/9/4 split to the training
candidate and frozen-model delivery v2. Features are upstream-only, targets sampled
PS3 edges. Constant-bias reference is post hoc and fitted on training rows only.
15.4 vs 18.1 ms test MAE is a small descriptive improvement; 38.3 vs 28.5 ms shifted
MAE is an adverse result. The empirical 65 ms envelope is not a probability guarantee.
Model and error envelope are advisory, not an active PLC policy. Train_00 failed in
the first data attempt due to inherited degraded-speed constraints; corrected only
the isolated fixture configuration, retained the failed attempt and same protocol.

E010 is the historical 144-run stopping comparison, not a full production campaign.
E011 uses the corrected qualification v2; the original max-speed boundary bug and
its rejected gate results remain documented. 24 identical-observation pairs expose
actuation ambiguity; zero releases is abstention, not perfect diagnostic accuracy.
These sources are distinct from E001's 24 earlier virtual cycles and its 97 tests.
New source/claim hashes are assistant-checked; human verification, authors, approval
and submission readiness remain pending. No physical results were supplied.

E009 recording audit: 16/4/4/9/4 unique observation-command hash pairs, no cross-split overlap; friction duplicates do not supply independent repetitions. See eta_ml_recording_audit_20261106.json.


E012 — Frozen advisory event monitoring (2026-11-06): source is candidate-eta-monitor-v2,
165 core/10 web checks,31 recordings/465 scheduled method replays,18 new MuJoCo
segments. Existing normal/shift test recordings are retrospectively reused. All
nine missing-target/stalled-drive input pairs are identical. Immediate ML and bias
findings18/18 each, normal0/9; ML equal in2/later in16, earlier in0. Two delayed
uncorrected-pulse records end before a confirmation window; censored, not proven
misses. Data rejection/engineering fallback is not credited as learned findings.
The original candidate predates the geometry/sample-period calibration-context guard;
v2 preserves model weights and original decisions with that additional boundary.
No central runtime policy authority, physical diagnostic accuracy or production gain.


## Focused methodological scope — 2026-11-06

Current draft replaces the broad resilience/reconfiguration narrative. E013 binds
plant-independent EventWindow, its optical adapter, the32-file focused delivery,
and exact reproduction of the original61 model records/465 full decision logs.
It does NOT provide a second process validation. Generic label contract tests are
software tests, not new device evidence. E009/E012 remain the empirical sources;
normal data reuse, duplication, post hoc reference and adverse ML outcomes remain
in the focused text. Previous broad manuscript is reproducible at Git7bbde4a.

E114/E115 are author-institution abstract/metadata checks recorded in
literature_scope_20261106.json. No claim of full-text verification, exhaustive
novelty search or guaranteed publication. The newly specified timestamp-naive
ablation, fresh conditions and second adapter remain pending. Human verification,
authorship, physical measurements and submission readiness remain unresolved.


E014 — Fresh-condition clock/age ablation: protocol/source committed at5a39fe5
before outcomes. Same frozen constant predictor and envelope, 36 recordings and
720 replays; only24 distinct admitted input pairs,12 identical fault pairs.
Six normal runs begin with occupied upstream beam; the remaining six include
2 normal findings under immediate/source-time monitoring, so the frozen zero-
finding target fails. Source/receiver comparison at80ms yields2/5 findings on
that same subset. Stale rejection removes all eligible inputs, not all errors.
The receiver comparator is intentionally timestamp-naive; never describe it as
best traditional PLC control. No post-result tuning, physical validation or
cross-machine evidence. Input-start audit is separately hashed; raw data retained.
