# Evidence and writing record — 2026-11-03

Status: assistant-inspected working draft; accountable human verification and author approval pending.
No source is marked human-verified. No manuscript was sent to an external drafting or typesetting service.
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
