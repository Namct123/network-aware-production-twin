# Title, abstract and Introduction: drafting record

Date: 2026-10-27. Status: research-in-progress draft; `submission_ready = false`.

## Current scope and format

The deliverable contains an English title, a 223-word abstract, five keyword phrases, an Introduction and six scholarly references. Following the latest user request, the formatting reference is `D:/hoctap/hybird control system.pdf`: a published Results in Engineering article with a wide front-matter block and a two-column main text. This supersedes both the earlier LNCS and IEEE layouts. The abstract and Introduction prose are unchanged; reference entries now use a numeric Elsevier-style presentation while retaining their previously checked metadata.

### Typography and reference-layout audit

The sample was read locally for its layout. Its author names, affiliation, results, publisher masthead, article DOI and publication dates are not adopted. The user's answer was that author names and affiliation are not yet settled, so those fields are blank. The draft is marked as research in progress.

- Paper: **210 x 280 mm**, matching the reference page dimensions (approximately 595.276 x 793.701 PDF points).
- Body: **two columns**, 18 TeX pt column gap. Left/right margins: **13.26/13.2 mm**. Top/bottom margins: **19.5/20 mm**. The title starts higher than in the reference because its publisher banner is omitted.
- Font: **Charis SIL 6.200**, using the four bundled TTF faces, under the SIL Open Font License (`open_fonts/OFL.txt`). The embedded reference body font is CharisSIL. No proprietary system-font dependency is required.
- Title: **13.5 TeX pt**, 17.2 pt baseline, regular weight, left aligned. Body and section heading: **8 TeX pt**, 10.5 pt baseline; main headings are bold, sentence case and numbered, e.g. `1. Introduction`.
- Front matter: narrow **ARTICLE INFO** panel with vertically listed keywords on the left; **ABSTRACT** on the right, with horizontal rules. Abstract: **7.2 TeX pt**, 9 pt baseline, one justified paragraph. Keyword text: **6.4 TeX pt**. The authors/affiliation area is reserved and blank.
- References: numeric square-bracket citations, **7.2 TeX pt** bibliography text, DOI links. The final page columns are balanced.
- Abstract length: **223 whitespace-separated words**, excluding labels and keywords. The reference is a formatting example, not a rule establishing a venue-specific word limit. The target venue has not been selected.

The rendered output is inspected visually; `evidence/layout_comparison.json` records page dimensions and actual embedded font/size distributions from both PDFs. TeX points differ from PDF points: 8 TeX pt corresponds to approximately 7.970 PDF pt, 7.2 to 7.173, and 13.5 to 13.450. This is a production-style approximation using the public `cas-dc` class with local presentation overrides, **not** a publisher-issued proof or a certificate of submission compliance.

The official CAS v2.4 class/style files are bundled without modification. The custom layout changes are in `main.tex`. Asset provenance and checksums are in `evidence/layout_assets.json`. The previous unused Times font copies remain excluded from Git.

No author identities are inferred from account names, email addresses or the sample byline. No numerical experimental benefits are asserted by this reformatting task.

## Evidence and claim boundaries

The abstract is drafted from the local project and design discussion. The Introduction also uses six scholarly references, with bibliographic metadata and bounded source-access records in `evidence/introduction_sources.md` and `evidence/crossref_metadata.json`. Evidence was inspected by the assistant; **accountable human verification remains pending**. No record below is a certificate of scientific validity, novelty, journal fit or publication readiness.

| Claim group | Support / location | Status in the abstract |
|---|---|---|
| The project concerns a conveyor-based sorting and pick-and-place cell. | `../../mujoco/README.md`, component descriptions; `../../mujoco/build_cell.py`, world and moving-body construction. | Project scope. |
| A MuJoCo model includes two conveyors, pneumatic transfer, Cartesian robot and suction cup. | `../../mujoco/production_cell.xml`; `../../mujoco/run_cell.py`, Cell and commissioning. | Implemented simulation basis; not calibrated physical fidelity. |
| The present model is not yet a validated network-aware twin. | `../../mujoco/README.md`, limitations; `../../mujoco/run_cell.py` directly reads product pose. | Stated explicitly: estimator, supervisor and quantitative validation remain under development. |
| Sensor/ground-truth separation, hybrid estimation, residual diagnosis and bounded rollouts. | `../huong_dan_loi_digital_twin.md`, architecture, estimation and prediction sections. | Proposed architecture, not an implemented result. |
| Software reconfiguration respects current actuators and local interlocks. | Same guide, software reconfiguration section; user scope limits reconfiguration to software. | Design constraint; no claim that hardware interlocks have been tested. |
| Three controller baselines and the listed performance criteria. | Same guide, evaluation section. | Planned evaluation; no claim of completed matched experiments. |
| Continuity under sensing and communication disturbances. | Research objective selected from the project scope. | Question to evaluate, not a demonstrated performance benefit. |

No numerical improvement, fault-detection accuracy, network latency, scenario throughput, statistical significance or safety guarantee has been inserted. The draft's initial problem statement is engineering motivation rather than a literature-wide empirical claim. The title uses “Framework” to identify the architectural contribution being proposed. Experiments and any final article must supply support for claims of benefit.

## Formatting sources inspected

- Latest visual reference: user-supplied `D:/hoctap/hybird control system.pdf`, inspected locally, 2026-10-27.
- Public CAS template: https://ctan.org/pkg/els-cas-templates (accessed 2026-10-27).
- SIL Charis font: https://software.sil.org/charis/ and the official 6.200 archive, with the bundled OFL license (accessed 2026-10-27).
- The following IEEE sources informed the earlier abstract baseline; they do not define the current layout.

- IEEE Author Center, “Structure Your Article”: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/ (accessed 2026-10-27).
- IEEE Industrial Electronics Society, “Abstract Description and Specifications”: https://www.ieee-ies.org/images/files/tie/guidelines/abstract-description-and-specifications-Final.pdf (accessed 2026-10-27). Used for the single-paragraph, 150-250-word abstract baseline; venue-specific rules still govern.
- CTAN, IEEEtran class, version 1.8b: https://ctan.org/pkg/ieeetran (accessed 2026-10-27).

The abstract contains no references, displayed equations, tables or unexplained initialisms. No unsupported novelty or comparative superiority claim is made. No human peer review or author approval is claimed.

## Writing assistance and software acknowledgment

The draft was prepared with AI writing assistance using the local `scientific-writing` skill and the `academic-research-suite` abstract workflow; LaTeX compilation and PDF inspection were performed locally. The responsible authors must verify the text and determine the disclosure required by the eventual journal. This note is a drafting record, not an author-approved submission disclosure.

As requested by the scientific-writing skill's software attribution guidance, the procedural source is recorded here rather than inserting an unrelated citation into the abstract:

Kassis, T., Agarwal, V., He, Y., Patel, D., and Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065. https://doi.org/10.48550/arXiv.2609.00065. Author list, title and year were checked against https://arxiv.org/abs/2609.00065 on 2026-10-27; the record showed a revision dated 2026-09-02. This is a software/procedural acknowledgment, not evidence for the proposed production-control method.

## Editing and compilation

`main.tex` is the editable source. Open this folder in Codex's LaTeX editor, or use XeLaTeX or Tectonic with the bundled, unmodified CAS files and the Charis SIL font files in `open_fonts/`. The source can also be uploaded to an authorized LaTeX editor by the user. Do not send unpublished text to an external editor without the authors' authorization.

The latest delivered PDF is `../../output/pdf/dt_cppps_title_abstract_introduction.pdf`. It contains the title, unchanged abstract, five keyword phrases, Introduction and six numbered references. The earlier title-and-abstract-only PDF remains at `../../output/pdf/dt_cppps_title_abstract.pdf`; the Vietnamese implementation guide is separate. `main.tex` now compiles the expanded extract through `introduction.tex` and `references_list.tex`.

## Vietnamese translation

A Vietnamese reading version was created on 2026-10-27 in main_vi.tex and introduction_vi.tex, using the same CAS layout and Charis SIL fonts. The English manuscript is retained. The six citation keys and their order, the three proposed contributions, the blank authorship fields, and the distinction between proposed work and completed simulation are preserved. Bibliographic titles remain in their original language. The Vietnamese abstract is a translation, not an independently shortened 223-word abstract. Output: ../../output/pdf/dt_cppps_title_abstract_introduction_vi.pdf (two pages). Export was compiled with Tectonic and both rendered pages were inspected for Vietnamese glyphs and layout. Human review of the translation remains pending.

