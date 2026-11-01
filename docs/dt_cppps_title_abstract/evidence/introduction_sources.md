# Introduction: sources, access scope and claim map

Prepared 2026-10-27 using scientific-writing, paper-lookup and citation-management. This is a targeted source check for an Introduction, not a systematic literature review or a proof of novelty. Assistant inspection is recorded below; **accountable human verification and author approval remain pending**. No source is marked human-verified.

## Retrieval record

Public web queries included exact-title lookups for Kritzinger's manufacturing classification, Hespanha's networked-control survey, Yates's age-of-information survey, Todorov's MuJoCo paper, and a scoped discovery query on digital-twin/network-aware manufacturing fault diagnosis. Publisher and institutional/author sources were opened; Crossref was used to reconcile identifiers and bibliographic fields. Only public paper titles and DOI identifiers were sent externally. The manuscript was processed locally.

The six Crossref `/works/{URL-encoded DOI}` requests and complete returned records are saved in `crossref_metadata.json`, including endpoint and access date. DOI identity, returned record type, title, authors and container were checked. Calls were sequential with 0.5 s spacing. The bundled citation converter/validator could not run because its `requests` dependency is absent; a standard-library HTTP retrieval reused the skill's dependency-free BibTeX renderer. No missing bibliographic field was invented. This fallback does not supply the unavailable validator's certification.

## Source scope

| ID / reference | Source actually inspected | Evidence used and limitation |
|---|---|---|
| E101 / Kritzinger2018 | https://repositum.tuwien.at/handle/20.500.12708/176517 ; Crossref DOI 10.1016/j.ifacol.2018.08.474 | Institutional record and author abstract only: classification into model, shadow, twin by integration level. Publisher requests were blocked. No detailed full-text claim or claim about the present-day scarcity of twins is made. The repository marks its migrated metadata as not quality-checked; bibliographic identity was cross-checked with Crossref and the publisher-indexed record. |
| E102 / Hespanha2007 | https://web.ece.ucsb.edu/~hespanha/published/ncs_v15p.pdf ; DOI 10.1109/JPROC.2006.887288 | Author-hosted manuscript, abstract and Sec. I, especially (b) Sampling and Delay and (c) Packet Dropout, pp. 1-2 of that file. Supports networked estimation/control limitations and variable delivery. No performance figure is transferred to this project. |
| E103 / Yates2021 | https://arxiv.org/pdf/2007.08564 ; https://arxiv.org/abs/2007.08564 ; https://dspace.mit.edu/entities/publication/ca039de7-e561-4a0f-bd3a-b92d0c436020 ; DOI 10.1109/JSAC.2021.3065072 | Author manuscript, title, author list, abstract and opening discussion of timestamped updates/timeliness. MIT links it to the published 2021 journal article. Limited to the shared high-level concept of information age; no version-specific theorem or numerical result is cited. |
| E104 / ElMahdy2024 | https://journals.sagepub.com/doi/10.1177/01423312241229493 | Publisher abstract only, explicitly restricted full text. Supports two LSTM networks, diagnosis/inverse-model reconfiguration, and a Factory I/O-MATLAB material-handling simulation. No claim about omitted network treatment, the detailed method, or measured advantage is made. Volume/issue/pages from Crossref, reconciled with publisher issue metadata. |
| E105 / Chen2026 | https://yiping514.github.io/chenyp.github.io/files/2025_JMD_RMPC.pdf ; https://arxiv.org/abs/2501.10337 ; DOI 10.1115/1.4069104 | Author-hosted **published journal version**, p. 1 abstract and Sec. 1 (pp. 1-3). Supports multistep quantile prediction, robust MPC and a directed-energy-deposition case. Cites the published 2026 volume 148(2), article 021702, not the 2025 preprint. The PDF records online publication in August 2025; that does not change its 2026 issue year. No quantitative transfer to conveyor handling is asserted. |
| E106 / Todorov2012 | https://roboti.us/lab/papers/TodorovIROS12.pdf ; DOI 10.1109/IROS.2012.6386109 | Author-hosted conference paper, p. 1 abstract, supports multibody/contact dynamics and model-based-control purpose. No speedup or absolute accuracy claim is used. The older Washington URL redirects to the laboratory home page; the direct author-archive PDF above was opened instead. |
| E107 / local implementation | `../../../mujoco/README.md`, `../../../mujoco/run_cell.py`, `../../../mujoco/production_cell.xml` | Physical cell simulation and commissioning sequence; direct access to ground truth and uncalibrated parameters remain limitations. Not evidence for completed network synchronization, estimator, fault diagnosis or predictive supervision. |
| E108 / local design | `../../huong_dan_loi_digital_twin.md` and user-approved software-only scope in this conversation | Proposed architecture, fault scenarios, baseline comparisons and response policies. These are design commitments/research questions, not implemented methods or measured findings. |

## Claim map

The corresponding paragraphs/items in `../introduction.tex` carry comment IDs.

| Claim ID | Support | Strength and interpretation |
|---|---|---|
| C101 | E101, E107-E108 | Integration classification plus this study's declared scope. |
| C102 | E107-E108 | Local application and qualitative fault-ambiguity examples; not experimental results. |
| C103 | E102-E103, E108 | Prior network/timeliness concepts followed by proposed timestamp/confidence design. |
| C104 | E104, E108 | Abstract-bounded prior sensor-fault approach, followed by this project's planned interpretable initial methods. |
| C105 | E105, E108 | Published predictive-control approach, followed by the handling-cell research question. No claim that the prior paper fails to address all aspects of the new question. |
| C106 | E108 | Problem formulation scoped to this project; no assertion of being the first or that the global literature lacks such work. |
| C107 | E106-E108 | Simulator purpose and actual model, followed by the explicitly proposed architecture. |
| C108 | E108 | Three **proposed** contributions; no completed-method or result claim. |
| C109 | E107-E108 | Existing-equipment capabilities, current implementation and validation limits. |

## Bibliographic enrichment and consistency

The raw Crossref record for Hespanha omits the accent in João and returns `Joo P.`; the BibTeX author spelling was restored from the author manuscript's heading. Crossref omits Brown's suffix; the Yates manuscript explicitly lists `D. Richard Brown III`, which is retained in both bibliography renderings. Chen is cited by the journal issue year 2026 after checking the published author PDF; the six-digit identifier is an article number, not a page interval. The MuJoCo case is protected in BibTeX.

`references.bib` is the reusable metadata source; `references_list.tex` is the IEEE-style bibliography used for this short extract. Citation keys and DOI sets must match before export. The manual list avoids relying on unavailable BibTeX tooling and is not a separate literature-review artifact. The draft contains no quotations and paraphrases only the material within each declared access scope.

The K-Dense procedural acknowledgment remains in `../draft_notes.md` as a software/writing-assistance record. It is not inserted as scientific evidence for the manufacturing-control claims.
