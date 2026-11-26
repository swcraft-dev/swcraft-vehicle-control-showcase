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

<!-- _class: vcenter -->

# Architecture as Code in the Sphinx-Needs world

## Enrich, never change

Konstantin Tarandevich · November 2026

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

