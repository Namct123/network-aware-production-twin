# Evidence and author-review record

Status: AI-assisted internal draft. Sources opened and compared by the assistant
on 2026-10-28; accountable human verification and final approval are **pending**.
No unpublished manuscript or local telemetry was submitted to external services.
Public title/DOI and publisher-template queries only were used for source lookup.

| ID | Locator | Bound claim |
|---|---|---|
| E1 | https://repositum.tuwien.at/handle/20.500.12708/176517, abstract and citation; local prior Crossref metadata `../dt_cppps_title_abstract/evidence/crossref_metadata.json` | Model/shadow/twin integration distinction. Institutional abstract only, not a claim about the entire contemporary literature. |
| E2 | https://web.ece.ucsb.edu/~hespanha/published/ncs_v15p.pdf, abstract and Sec. I(b,c), source PDF pp. 1–2 | Sampling, delay, drops and networked control. |
| E3 | https://arxiv.org/abs/2007.08564, author abstract; prior Crossref metadata and reference list for published 2021 version | Timestamped updates, freshness and information age; no theorem or numerical result transferred. |
| E4 | https://roboti.us/lab/papers/TodorovIROS12.pdf, p. 1 abstract | MuJoCo multibody/contact dynamics and model-based-control purpose, not absolute accuracy or a benchmark for this project. |
| E5 | `../../output/dt_web_acceptance_20261028_final/results.json` | Four acceptance cases / seven runs; nominal placement true for both at 15.46 s; matched PS2 HOLD at 6.76/6.72 s. Frozen baseline profile, not later measured CAD. |
| E6 | `../../mujoco/predictor.py`, `supervisor.py`, `experiment.py`, `estimator.py`, `network.py`, `sequence.py` and per-trial manifests referenced by E5 | 54 trajectories = 3 × 3 × 3 × 2, 0.5 s horizon, one-interval 20 ms advance, budget handling, separation from plant truth; current controls do not implement automatic recovery. |
| E7 | Official Springer instructions PDF and LaTeX ZIP linked from https://link.springer.com/series/558/information-for-authors-and-editors | LNCS class/template; samplepaper abstract length and class font/layout definitions. |

## Related-research revision, 2026-10-28

| ID | Locator | Bound claim and reading limits |
|---|---|---|
| E8 | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8874643/fullTextXML ; public full text retained at `../../tmp/literature_revision/Ademujimi2022.xml`, abstract and Section 7; DOI 10.3390/s22041430 | Equipment/DES co-simulation, four-robot laboratory cell, Bayesian-network structure learning via interventions. Authors explicitly propose plant validation and sensitivity to twin-parameter deviations as future work. Do not reinterpret graph-learning performance as the present project's detection accuracy. |
| E9 | https://arxiv.org/html/2506.07332v1 , Sections III-E, IV-A, V; published-version metadata at https://arxiv.org/abs/2506.07332 | Fu et al. integrate monitoring, capability data, optimization and simulation for task redistribution. Physical movement is abstracted in the discrete-event simulator; collection delay is treated as negligible versus operation duration. Spatial constraints and testbed validation are explicitly future work. Cite published 2025 T-ASE version DOI 10.1109/TASE.2025.3563320, vol.22 pp.14892-14905. No speed or throughput result is transferred to our cell. |
| E10 | https://iris.unimore.it/handle/11380/1249772 , institutional author abstract and full bibliographic record, DOI 10.1109/TII.2021.3067447 | Bellavista et al.'s ADTN middleware supports heterogeneous communication and SDN-based dynamic edge-network management. Full-text PDF retrieval blocked by publisher/repository protection; use only the explicitly supported abstract-level scope, no claims about omitted methods or experimental performance. |

Introduction mapping: opening E1 and explicit application; related research diagnosis
E8 plus clearly stated application requirements; reconfiguration E9 and our own
scope comparison; network paragraph E10/E2/E3 and physical reasoning. Gap is a
bounded synthesis of these selected works, not an exhaustive absence claim. Proposed
architecture and implemented contributions E4/E6; descriptive results E5; final
paragraph distinguishes planned calibration/recovery from completed evaluation.
Abstract numerical claims remain E5/E6; its text is unchanged in this revision.

Search scope: focused narrative update, not a systematic review. Public web searches
on 2026-10-28 used combinations of digital twin, manufacturing, fault diagnosis,
reconfiguration, network delay, and age of information; follow-up title searches
located primary author/publisher records. Selected E8/E9/E10 cover the three relevant
themes. Leng 2020 and Caesar 2023 appeared in discovery but are not cited because
this revision does not need unsupported full-text comparisons. Human verification
of all sources and scientific novelty remains pending. The assistant opened E8 full
text locally, E9 author HTML and publication record, and E10 institutional abstract.

Tool provenance is documented in README.md, with the verified Scientific Agent
Skills record https://arxiv.org/abs/2609.00065. This tool reference is not used as
scientific evidence for DT supervision.

This is an engineering simulation study, not a clinical or human-participant study;
no clinical reporting guideline is applied. The four cases are descriptive fixtures,
not a statistical sample establishing sensitivity, specificity or production safety.
The original project title is retained, but self-reconfiguration is a research goal;
only continue/hold supervisory adaptation is presently supported by the stated evidence.

Before submission: authors verify claims and references, settle authorship/affiliation,
select the actual proceedings venue and its instructions, reconcile the physical
measurements, and determine the required AI-use disclosure under the venue policy.
