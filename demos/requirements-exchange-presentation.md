---
marp: true
title: "Architecture as Code in the Sphinx-Needs world"
author: "Konstantin Tarandevich"
description: "How SWCraft reads Sphinx-Needs requirements, enriches them with architectural decisions and links to model elements without changing them, and carries them into AUTOSAR and to testing"
paginate: true
theme: default
---

<style>
section {
  align-content: start;
  justify-content: flex-start;
  padding: 42px 70px 60px;
}

section.vcenter {
  align-content: center;
}

section.dense table {
  font-size: 0.85em;
}

section.compact {
  font-size: 26px;
}

section.compact h1 {
  font-size: 1.5em;
}
</style>

<!--
Audience: a colleague or a buyer who works with requirements in Sphinx-Needs; architects and testers
in the same chain.
Message: in the Sphinx-Needs world everyone works with requirements in one docs-as-code chain.
SWCraft, the architect's tool, joins that chain. As Architecture as Code it enriches the
requirements with architectural decisions and with links to model elements; it never changes them.
And it is the bridge from software requirements to AUTOSAR in the V-model: ARXML for the AUTOSAR
tools and test tables for testing.
Wording: no "requirements team". Say the Sphinx-Needs project, the requirements site, your conf.py;
where an owner must be named, the requirements' authors.
Form: SWCraft's own deck's. Each slide has a claim as its title, an excerpt or a flow, three or four
bullets and one bold takeaway.
Delivery: ten slides in about twelve minutes, then the showcase's walkthrough if there is time.
Every excerpt is from the showcase's requirements exchange (`demos/requirements-exchange.md`): the
Sphinx-Needs sources, the model after the walkthrough's linking, and the ready-made requirements
sites under `demos/requirements-exchange/sites/`. The data is synthetic: the requirements and their
texts.
-->

<!-- _class: vcenter -->

# Architecture as Code in the Sphinx-Needs world

## Enrich, never change

Konstantin Tarandevich · November 2026

<!--
Purpose: state the proposition.

Talk track:
1. "Your requirements already live as code: Sphinx-Needs, Git, a built site."
2. "SWCraft adds the architecture to your requirements; the requirements stay as their authors
   wrote them."
3. "It joins your chain: it reads the requirements and hands back where each one is realised."
4. "Two things to remember: the architect never changes a requirement, only enriches it; and SWCraft
   is the bridge from those requirements down into AUTOSAR and across to testing."

Transition: start where the requirements already are.
-->

---

# Requirements are code — the chain stops there

```rst
.. swreq:: Permitted action under fade
   :id: SWR-THP-003
   :status: approved
   :document: SRS Thermal Protection
   :rev: 1

   When the brake temperature exceeds 600 degC the permitted brake action shall be reduced.
```

- Sphinx-Needs: requirements as text in Git, reviewed like code
- The build turns them into a site and a `needs.json`
- What the requirements site cannot show: **where and how** each requirement is realised
- The architecture lives elsewhere, and the link is kept by hand, if at all

**Requirements as code already exist; the architecture is the missing link.**

<!--
Purpose: acknowledge what the chain already has, and name the gap.

Talk track:
1. This is a Sphinx-Needs source in the project's own vocabulary: a `swreq` directive, its status,
   its document, its revision.
2. The Sphinx-Needs build gives a site and a `needs.json`: requirements as code already exist.
3. The question every reviewer, tester and safety engineer asks is "what realises this?", and the
   requirements site has no answer.

Transition: SWCraft closes that gap, and goes further down the V.

[Sources] `demos/requirements-exchange/team/delivery-1.0/index.rst` (SWR-THP-003, as committed);
`demos/requirements-exchange.md` § *What the project holds*.
-->

---

<!-- _class: compact -->

# SWCraft bridges requirements to AUTOSAR

<svg viewBox="0 0 1140 290" width="1140" height="290" role="img" style="display:block;margin:6px auto 4px;font-family:inherit" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="rx-arrow-bridge" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0969da"/></marker></defs>
<rect x="100" y="0" width="320" height="180" rx="10" fill="#f6f8fa" stroke="#d0d7de" stroke-width="1.5"/>
<text x="260" y="32" font-size="19" text-anchor="middle" font-weight="bold" fill="#1f2328">Sphinx-Needs project</text>
<line x1="100" y1="48" x2="420" y2="48" stroke="#d0d7de" stroke-width="1.5"/>
<text x="124" y="94" font-size="18" text-anchor="start" font-weight="normal" fill="#1f2328">software requirements</text>
<text x="124" y="140" font-size="18" text-anchor="start" font-weight="normal" fill="#1f2328">requirements site</text>
<text x="124" y="164" font-size="16" text-anchor="start" font-weight="normal" fill="#59636e">“satisfied by”</text>
<rect x="620" y="0" width="420" height="180" rx="10" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="830" y="32" font-size="19" text-anchor="middle" font-weight="bold" fill="#1f2328">SWCraft: architecture as YAML in Git</text>
<line x1="620" y1="48" x2="1040" y2="48" stroke="#0969da" stroke-width="1.5"/>
<text x="644" y="80" font-size="17" text-anchor="start" font-weight="normal" fill="#1f2328">components · ports · runnables</text>
<text x="644" y="106" font-size="17" text-anchor="start" font-weight="normal" fill="#1f2328">tasks · interfaces</text>
<text x="644" y="134" font-size="15" text-anchor="start" font-weight="normal" fill="#1f2328" font-family="SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace">satisfies: [SWR-THP-003@1]</text>
<text x="644" y="162" font-size="15" text-anchor="start" font-weight="normal" fill="#1f2328" font-family="SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace">check-model · validate · build</text>
<path d="M422,94 H616" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-bridge)"/>
<text x="520" y="84" font-size="15" text-anchor="middle" font-weight="normal" fill="#1f2328" font-family="SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace">needs.json</text>
<path d="M618,140 H424" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-bridge)"/>
<text x="520" y="130" font-size="15" text-anchor="middle" font-weight="normal" fill="#1f2328" font-family="SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace">needs.json</text>
<path d="M830,180 V204 M720,204 H940" fill="none" stroke="#0969da" stroke-width="2"/>
<path d="M720,204 V228" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-bridge)"/>
<path d="M940,204 V228" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-bridge)"/>
<rect x="620" y="230" width="200" height="58" rx="10" fill="#f6f8fa" stroke="#d0d7de" stroke-width="1.5"/>
<text x="720" y="254" font-size="18" text-anchor="middle" font-weight="bold" fill="#1f2328">ARXML</text>
<text x="720" y="277" font-size="16" text-anchor="middle" font-weight="normal" fill="#59636e">AUTOSAR tools</text>
<rect x="840" y="230" width="200" height="58" rx="10" fill="#f6f8fa" stroke="#d0d7de" stroke-width="1.5"/>
<text x="940" y="254" font-size="18" text-anchor="middle" font-weight="bold" fill="#1f2328">test tables</text>
<text x="940" y="277" font-size="16" text-anchor="middle" font-weight="normal" fill="#59636e">testers</text>
</svg>

- **In:** a delivery's `needs.json`, imported into the model as versioned requirements
- **Out to AUTOSAR:** the same model generates ARXML, schema-checked
- **Out to testing:** test tables (components, placement, scheduling) as CSV files testers review
- **Back to the requirements:** the architecture and its links, as a `needs.json` the site loads

**SWCraft is the bridge from software requirements to AUTOSAR in the V-model.**

<!--
Purpose: the V-model picture: SWCraft sits where software requirements turn into AUTOSAR
architecture, and connects both sides of the V.

Talk track:
1. Left branch of the V: the software requirements come in as a `needs.json`.
2. The architecture is the model; each element says which requirement it satisfies, at which
   version.
3. Down the V: the model generates the ARXML the AUTOSAR toolchain consumes; `swcraft validate`
   checks it before it leaves.
4. Across the V: `swcraft generate test-tables` (the panel's *Test Tables*) writes what testers
   verify: which component runs where, in which task, how often, on which core. One row per thing to
   verify, every value computed from the model, nothing written by AI.
5. And back: the architecture goes into the Sphinx-Needs build as a `needs.json`, the next slides.

[Sources, checked against the SWCraft 0.24.0 guide]
- `docs/guide/index.md` (ARXML, diagrams and the requirements file are what SWCraft generates)
- `docs/guide/reference/requirements-interchange.md` (`swcraft import requirements` reads a
  Sphinx-Needs `needs.json`)
- `docs/guide/test-tables.md` (the command, the three tables, CSV, computed from the model)
-->

---

<!-- _class: compact -->

# One block in your conf.py

```python
# --- SWCraft's architecture: the need types, fields and link types its needs.json uses ---
needs_types = [ ..., {"directive": "arch_element", "title": "Architecture element", ...} ]
needs_links = {
    "satisfies": {"outgoing": "satisfies", "incoming": "satisfied by", ...},
    "satisfies_unconfirmed": {"incoming": "satisfied by (unconfirmed)", ...},
    ...
}
needs_external_needs = [{"json_path": "swcraft/needs.json", "target_url": ".../{{need.swcraft_path}}", ...}]
# --- end of SWCraft's declarations ---
```

- SWCraft **reads** your `needs.json`; a mapping file translates your vocabulary once
- SWCraft **writes** its own `needs.json`; your Sphinx-Needs build loads it as external needs
- No tool changes: Sphinx, Sphinx-Needs and Git stay; nothing is installed in your pipeline

**SWCraft joins your chain as it is.**

<!--
Purpose: show that joining the chain costs the Sphinx-Needs project almost nothing.

Talk track:
1. The import: `swcraft import requirements --source needs.json --mapping ...`, or the panel's
   *Import Requirements*. The project keeps its own vocabulary (`swreq`, `sgoal`, `safety`, `rev`,
   `parent`), and the architect's mapping file says once how it maps onto SWCraft's.
2. The export: `swcraft generate needs` writes `dist/needs.json`, the architecture and its links.
3. In the Sphinx-Needs project: one block in `conf.py`, SWCraft's declarations, shortened here.
4. Optional: a section with a `needtable` lists the architecture on the requirements site; the
   "satisfied by" lines on each requirement come from the `conf.py` block alone.

[Sources] `demos/requirements-exchange/team/conf.py` (the block between the two markers);
`demos/requirements-exchange/team.needs-mapping.yaml`; `demos/requirements-exchange.md` §§ 1, 3, 4.
The requirements sites were built with Sphinx-Needs 9.2.0 and Sphinx 9.0.4 only.
-->

---

<!-- _class: compact -->

# Requirements stay as written

```yaml
id: SWR-THP-003
title: Permitted action under fade
description: When the brake temperature exceeds 600 degC the permitted brake action
  shall be reduced.
version: 1
source: external        # the authors': a re-import overwrites it
document: SRS Thermal Protection
baseline: '1.0'         # the delivery
revision: '1'           # the authors' revision
```

- Requirements arrive **as delivered**, each with its delivery and its revision
- Texts, statuses and versions stay the authors': the next delivery overwrites them
- The architect's work lives beside them: architecture requirements, and the elements' links

**The architect never changes a requirement, only enriches it.**

<!--
Purpose: accent (a): the architect does not touch the requirements.

Talk track:
1. This is the requirement after the import, in the model: `source: external` means its authors own
   it; `baseline` names the delivery, `revision` the authors' own revision.
2. A re-import of the next delivery overwrites it, and removes it when the delivery no longer holds
   it. A status is read, not stored: a `rejected` status removes the requirement.
3. So the architect has nothing to edit here. Everything the architect adds sits on the architecture
   side: architecture requirements, and `satisfies` links on elements.
4. Be precise if asked: SWCraft does not lock the file. "Nothing refuses an edit of an external
   requirement; the importer's workflow is what keeps it read-only", in the guide's words. Review and
   the next import make an edit pointless.

[Sources, checked against the SWCraft guide]
- `docs/guide/reference/model/requirements.md` (`source`: external or architecture; the read-only
  sentence)
- `docs/guide/reference/requirements-interchange.md` (a status read and not stored; `rejected`
  removes)
- The YAML: `model/requirements/SWR-THP-003.yaml` after importing delivery 1.0 (shortened: `req_type`
  left out; the comments are the slide's, not the file's)
-->

---

<!-- _class: compact -->

# Enrichment 1: architectural decisions

```text
Safety goal: Prevent brake fade from thermal overload   REQ_BTP_SAFETY_GOAL
status: approved   safety: D   rev: 4
satisfied by: COMP-Chassis
derives:      REQ_BTP_DECOMP_MAIN, REQ_BTP_DECOMP_MONITOR
```

- The safety goal is a requirement of the Sphinx-Needs project, ASIL D
- The architect decomposes it into two architecture requirements, each ASIL B(D)
- In the model: `source: architecture`, `derived_from: [REQ_BTP_SAFETY_GOAL@1]`
- On the requirements site: "derives" under the goal, the goal itself unchanged

**The architect's decisions appear where the requirements are read.**

<!--
Purpose: the first enrichment: the architect's decisions become visible where requirements are read.

Talk track:
1. The excerpt is the safety goal on the requirements site. The goal is a requirement of the
   Sphinx-Needs project (`sgoal`, ASIL D). The architect decomposes it: two architecture
   requirements, each ASIL B(D), a main channel (`REQ_BTP_DECOMP_MAIN`) and a monitor channel
   (`REQ_BTP_DECOMP_MONITOR`).
2. Those are `source: architecture`: the architect's own requirements, in the model, derived from
   the goal at its version.
3. The requirements site shows them under the goal, "derives: REQ_BTP_DECOMP_MAIN,
   REQ_BTP_DECOMP_MONITOR", and the architecture, its six requirements with it, in a table of its own.
4. The goal itself is unchanged: the "derives" line is the incoming side of the architecture's link.

[Sources] the ready-made requirements site of delivery 1.0, `demos/requirements-exchange/sites/1.0/`
(the goal's text left out; `parent: HAZ_BTP_BRAKE_FADE` left out);
`model/requirements/REQ_BTP_DECOMP_MAIN.yaml` (`source`, `derived_from`, `asil`);
`demos/requirements-exchange.md` § 3 (the six architecture requirements in `dist/needs.json`).
-->

---

<!-- _class: compact -->

# Enrichment 2: links to model elements

```yaml
- name: pPermittedBrakeAction
  satisfies:
  - REQ_SHOWCASE_FEATURE_001@1
  - SWR-THP-003@1
  direction: provide
  interface: IPermittedBrakeAction
```

- In the model, the port lists the requirement, at its version, under `satisfies`
- The trace link search proposes candidates; the architect decides
- The build writes each linked element into `needs.json`, with its YAML file
- On the requirements site: "satisfied by: PORT-BrakeThermalProtection-pPermittedBrakeAction"

**Every requirement shows the element that realises it, one click from its file.**

<!--
Purpose: the second enrichment: the trace from a requirement to the element that realises it.

Talk track:
1. The architect links in the model: the port lists the requirement, at its version, under
   `satisfies`. A component, a port, a runnable, a composition, an interface, a task or a hardware
   element can.
2. SWCraft's trace link search proposes candidates and the architect decides; nothing is linked
   without a decision. In the walkthrough, two links are made by hand and one wrong row rejected;
   the rest of the answer key comes from a prepared file, applied in one step. 38 of the 46 software
   requirements end up linked; the 8 others are distractors the architecture does not realise.
3. The build writes the element into `dist/needs.json` with its file, `swcraft_path`
   (`swc/application/BrakeThermalProtection.yaml`). On the requirements site SWR-THP-003 lists it
   under "satisfied by", and a click leads to that YAML file in the showcase repository.

[Sources] `model/swc/application/BrakeThermalProtection.yaml` after the walkthrough's step 2;
the ready-made requirements site of delivery 1.0 (SWR-THP-003's "satisfied by" line);
`demos/requirements-exchange.md` §§ 2–4 (two by hand and one rejection, the prepared links, 38
linked, 8 distractors; `swcraft_path` `swc/application/BrakeThermalProtection.yaml`).
-->

---

<!-- _class: compact -->

# Links stay live

```text
Summary: 0 added, 1 changed, 1 removed, 0 stubs created, 48 source updates
Links now needing confirmation:
SWC 'BrakeThermalProtection' (port 'pPermittedBrakeAction') satisfies 'SWR-THP-003@1'
```

- Delivery 1.1 raises SWR-THP-003's threshold from 600 to 650 °C
- The requirements site shows "satisfied by (unconfirmed)" until the architect has looked
- The architect reads the new text and confirms: `SWR-THP-003@2`, confirmed on both sides
- `swcraft check-model` names every link to confirm and every requirement nothing satisfies

**A changed requirement never keeps a silent link.**

<!--
Purpose: the trace does not rot: a changed requirement turns its link unconfirmed on both sides
until the architect has looked at it.

Talk track:
1. The excerpt is the import report of delivery 1.1. The authors change one linked requirement
   (rev 2, 600 to 650 °C) and drop one. The import says exactly that: one changed, one removed, and
   the 48 others only move to delivery 1.1.
2. The link was made against version 1. SWCraft does not silently carry it over: the report lists it
   as needing confirmation, `check-model` warns, and the architecture's `needs.json` puts it under
   `satisfies_unconfirmed`, so the requirements site says "satisfied by (unconfirmed):
   PORT-BrakeThermalProtection-pPermittedBrakeAction".
3. The architect reads the new text and confirms, with the quick fix on the warning or in the trace
   view. The link becomes `SWR-THP-003@2`, and after the next build the requirements site shows it
   confirmed.
4. `check-model` is the running list: one warning per requirement nothing satisfies ("Requirement
   'SWR-BRK-011' is satisfied by no element: add `satisfies: [SWR-BRK-011@1]` ..."), one per link to
   confirm.

[Sources] `demos/requirements-exchange.md` § 5 (the report's summary and its *Links now needing
confirmation* line, the confirmation); the ready-made requirements sites `sites/1.1-unconfirmed/`
and `sites/1.1-confirmed/`; `swcraft check-model` after step 2 (12 warnings).
-->

---

<!-- _class: compact -->

# One chain, three roles

<svg viewBox="0 0 1140 190" width="1140" height="190" role="img" style="display:block;margin:6px auto 4px;font-family:inherit" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="rx-arrow-chain" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0969da"/></marker></defs>
<rect x="20" y="10" width="240" height="56" rx="10" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="140.0" y="45" font-size="19" text-anchor="middle" font-weight="bold" fill="#1f2328">requirement authors</text>
<rect x="450" y="10" width="200" height="56" rx="10" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="550.0" y="45" font-size="19" text-anchor="middle" font-weight="bold" fill="#1f2328">architects</text>
<rect x="880" y="10" width="240" height="56" rx="10" fill="#f6f8fa" stroke="#d0d7de" stroke-width="1.5"/>
<text x="1000.0" y="45" font-size="19" text-anchor="middle" font-weight="bold" fill="#1f2328">AUTOSAR tools</text>
<rect x="880" y="100" width="240" height="56" rx="10" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="1000.0" y="135" font-size="19" text-anchor="middle" font-weight="bold" fill="#1f2328">testers</text>
<path d="M260,38 H446" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-chain)"/>
<text x="353" y="28" font-size="15" text-anchor="middle" font-weight="normal" fill="#1f2328" font-family="SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace">needs.json</text>
<path d="M650,38 H876" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-chain)"/>
<text x="763" y="28" font-size="15" text-anchor="middle" font-weight="normal" fill="#1f2328" font-family="SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace">ARXML</text>
<path d="M600,66 V128 H876" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-chain)"/>
<text x="740" y="118" font-size="16" text-anchor="middle" font-weight="normal" fill="#1f2328">test tables</text>
<path d="M500,66 V178 H140 V70" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-chain)"/>
<text x="320" y="168" font-size="15" text-anchor="middle" font-weight="normal" fill="#1f2328" font-family="SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace">needs.json: coverage</text>
</svg>

- **Requirement authors:** coverage and the links awaiting confirmation, on their site
- **Architects:** the requirements, versioned, in the model; every change and every open link named
- **Testers:** what runs where and how often; a reviewed row turns `stale` on change

**One docs-as-code chain: requirements, architecture and tests, linked and kept live.**

<!--
Purpose: the benefit per role in one chain, not per team.

Talk track:
1. Requirement authors get coverage on the site they already read, from their own build, without
   opening the architecture tool.
2. Architects get the requirements under version control in the model, and a list of what is open
   (the import report, `check-model`) instead of a spreadsheet.
3. Testers get the test tables: components (with the requirements they satisfy), component
   placement, runnable scheduling. They fill their own columns (verification method, comment,
   accepted); SWCraft regenerates the tables from the model and joins those columns back by each
   row's identity, and a row whose facts changed since it was accepted is marked `stale`. The
   testers' files are never written.
4. If asked: the tables are a view of the model, not verification evidence; an accepted row is the
   testers' statement, not SWCraft's.

[Sources] the slides before; SWCraft's guide `docs/guide/test-tables.md` (the three tables and
their columns, the round trip with the testers' folder, `stale`, what the tables do not say).
-->

---

<!-- _class: vcenter -->

# Try it on the showcase

<svg viewBox="0 0 1140 52" width="1140" height="52" role="img" style="display:block;margin:10px auto 18px;font-family:inherit" xmlns="http://www.w3.org/2000/svg">
<defs><marker id="rx-arrow-flow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0969da"/></marker></defs>
<rect x="34" y="4" width="124" height="44" rx="22" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="96" y="32" font-size="17" text-anchor="middle" font-weight="normal" fill="#1f2328">import 1.0</text>
<path d="M162,26 H188" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-flow)"/>
<rect x="192" y="4" width="218" height="44" rx="22" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="300" y="32" font-size="17" text-anchor="middle" font-weight="normal" fill="#1f2328">2 links by hand, 1 ✕</text>
<path d="M414,26 H440" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-flow)"/>
<rect x="444" y="4" width="162" height="44" rx="22" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="524" y="32" font-size="17" text-anchor="middle" font-weight="normal" fill="#1f2328">prepared links</text>
<path d="M610,26 H636" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-flow)"/>
<rect x="640" y="4" width="77" height="44" rx="22" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="678" y="32" font-size="17" text-anchor="middle" font-weight="normal" fill="#1f2328">build</text>
<path d="M720,26 H746" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-flow)"/>
<rect x="750" y="4" width="68" height="44" rx="22" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="784" y="32" font-size="17" text-anchor="middle" font-weight="normal" fill="#1f2328">site</text>
<path d="M822,26 H848" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-flow)"/>
<rect x="852" y="4" width="124" height="44" rx="22" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="914" y="32" font-size="17" text-anchor="middle" font-weight="normal" fill="#1f2328">import 1.1</text>
<path d="M980,26 H1006" fill="none" stroke="#0969da" stroke-width="2" marker-end="url(#rx-arrow-flow)"/>
<rect x="1010" y="4" width="96" height="44" rx="22" fill="#ddf4ff" stroke="#0969da" stroke-width="1.5"/>
<text x="1058" y="32" font-size="17" text-anchor="middle" font-weight="normal" fill="#1f2328">confirm</text>
</svg>

- **The Vehicle Control showcase**: a synthetic model and requirements
- **Delivery 1.0:** 50 requirements, 46 of them software requirements, 8 of those distractors
- **After linking:** 38 linked, 12 warnings: 4 by design, 8 distractors
- Runs in VS Code and on the command line; the requirements sites come ready-made

**One page is the script; the kit carries everything it needs.**

<!--
Purpose: the close: how to see it for yourself.

Talk track:
1. The flow is the walkthrough: import delivery 1.0; two links by hand and one ✕, the rest from
   the prepared links in one step; build; open the ready-made requirements site; import delivery
   1.1; confirm the changed link.
2. The showcase's colleague kit holds the model, both deliveries, the prepared links, the Sphinx-Needs
   project and its three ready-made sites, and the page `demos/requirements-exchange.md`, which is
   the script. This deck's public copy is in the kit too.
3. Every step runs where SWCraft runs. Building a requirements site yourself, instead of opening the
   ready-made one, needs Python 3.11 or later and `pip` access to PyPI.
4. The data is synthetic: the requirements and their texts.

[Sources] `demos/requirements-exchange.md` (the steps; delivery 1.0's counts; 38 linked and 12
warnings after step 2; the ready-made sites and what building one yourself needs).
-->
