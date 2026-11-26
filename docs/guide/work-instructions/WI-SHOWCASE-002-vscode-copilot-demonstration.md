# WI-SHOWCASE-002 — VS Code, Copilot and Kiro Demonstration Script

| Field | Value |
|---|---|
| Document ID | WI-SHOWCASE-002 |
| Revision | 6.4 |
| Status | **§§ 5–9 replaced by the storefront's scenarios** (revision 6.0): the chat segments are `demos/chat-with-the-model.md`, run the same way in Copilot and in Kiro; the refusals are the rejected changes of `demos/README.md`. The baseline script those sections held was rehearsed clean on `0.4.0` (2026-08-24) and run on Windows end to end with the corporate Copilot and XSD validation (2026-08-26); it is in this document's git history. No run has been made on the new scenarios yet |
| Owner | Vehicle Control Showcase project lead |
| Applies to | This repository on SWCraft `0.24.0` |
| Companion | `docs/presentations/swcraft-project-presentation.md` in the SWCraft repository (the deck) |
| Presenting machine | macOS (the corporate Windows installation is a separate, later leg) |
| Effective date | Not yet approved |

> **Replaced, revision 6.0 (2026-11-10).** The model on `main` is the *storefront*
> (FB-SHOWCASE-001): one vehicle-control model that uses every model feature of the SWCraft
> release it pins and already contains `BrakeThermalProtection`, its connectors and its
> requirements. §§ 5–9 were written for the five-component baseline and suspended since
> revision 4.0; this revision replaces them with pointers to what runs on the storefront:
>
> - the tags `showcase-baseline-001` and `showcase-feature-001` are **history**: they predate
>   later SWCraft releases and do not load at the release this project pins (`swcraft check-model`
>   refuses both), so the reset lines of § 4 do not run;
> - the chat segments — an architect's question, an impact question, a change proposed and
>   rejected in the review tab, the model guard — are `demos/chat-with-the-model.md`, the same
>   steps in Copilot and in Kiro;
> - the refusals are the nine rejected changes under `demos/` (`demos/README.md`): each one is a
>   small edit that `swcraft check-model` refuses by exactly the rule it names, the incompatible
>   connector and the RAM budget among them.

## 1. Purpose

This instruction is the script for showing the team *how an architect works with the model* —
in VS Code through GitHub Copilot Chat, and in Kiro through its own chat, on the installed SWCraft
product. It exists because the
2026-08-22 management discussion concluded that small real demonstrations beat any amount of
explanation, and that only what actually works should be shown.

It follows the **presentation deck's own argument** — the model reads as text; two releases give a
readable change set; invalid architecture stops before it reaches downstream tools; AI accelerates
and stays constrained — so that each of those slides can be backed by a live segment, on its own
or in sequence. The deck is the frame; the segments below are its evidence. **One command line
only**: since `0.4.0` every other command the script needs is in the SWCraft panel or its tabs. The
requirements exchange's prepared links (`demos/requirements-exchange.md` § *The prepared links*) are
applied by two lines pasted into VS Code's terminal (*Terminal → New Terminal*), because the panel's
**Apply…** writes the decisions of the last search, not a proposals file prepared beforehand.
Everything shown is in the product today; nothing is mocked.

## 2. The one-sentence explanation

Say this before touching anything, and say nothing longer:

> The architecture lives as YAML under git. From it SWCraft builds the AUTOSAR ARXML, the
> diagrams and the report. An assistant can change the model — but only through a reviewed,
> all-or-nothing change set that the model itself validates first.

Then show it.

## 3. Slide → segment map

| Deck slide | Claim | Segment | Model state needed |
|---|---|---|---|
| *The architecture model reads as text* | one file per element; the editor knows the model's shape | `demos/README.md` § *How to apply one* — a rejected change made by hand in the editor | committed |
| *Invalid architecture stops before it reaches downstream tools* | FAIL → findings, nothing written | `demos/README.md` — the nine rejected changes, each refused by the rule it names | committed, one edit applied and undone |
| *Two releases now produce a readable change set* | `swcraft diff release-A release-B` | no segment on the storefront: the two tags it compared are history and do not load | — |
| *AI accelerates the workflow — and stays constrained* | one change set, exact delta, human decides | `demos/chat-with-the-model.md` steps 4–5 — a change rejected in the review tab, and the guard — in Copilot and in Kiro | committed |
| (not on a slide: what the architect gets) | a question answered from the model, impact, test tables, the requirements exchange | `demos/chat-with-the-model.md` steps 2–3; `demos/test-tables.md`; `demos/requirements-exchange.md` | committed |
| *Migration feasibility is already proven* | Rhapsody round trip | no segment — the slide's evidence stands | — |

Every segment starts from the committed model — `git status` clean in `model/` — and leaves it so;
any of them can be run alone to answer a question during the deck.

**No time box, and no rehearsed timing.** Questions are welcome at any point and the room decides
where the session goes; a script measured with a stopwatch would be spent the moment it went
somewhere else. What the order fixes is the *argument*, not the clock. If the session has to be cut
short, the two questions of the chat page (its steps 2–3) are what goes; the rejected change, the
review tab and the guard are the deck's argument and stay.

## 4. Preconditions (checked the day before, never on stage)

| Check | How |
|---|---|
| Toolchain installed at the pinned release | since 0.7.0 SWCraft is installed **once per machine** from the workstation archive (`swcraft-0.24.0-<platform>.zip`, installed per WI-SHOWCASE-001 § 8.3) and the project installs nothing: `swcraft.yaml` pins `toolchain_version: "0.24.0"`, `swcraft --version` in a **new** terminal must answer it, and `moon run :build` passed (WI-SHOWCASE-001 § 8.2 — the project carries no preflight script). No `.venv` may exist in the project — activated, it shadows the installation for that terminal |
| Model at the committed starting state | `git status` clean in `model/`; `dist/` and `views/` regenerated by the panel commands |
| VS Code ≥ 1.110.0, extension pack resolved | the archive's installer installs the extension (`swcraft-vscode-0.24.0.vsix`, from the unpacked archive by hand if it did not); the installer hands Red Hat YAML and Red Hat XML to VS Code out of the same archive just before SWCraft's own, so no Marketplace access is needed. Then **Check Editor Tooling** in the `…` menu at the top of the SWCraft view: the report must show two `[ok]` members, the workstation installation and its version `0.24.0`, all 16 schemas, **"No problems found"** — this one command is the whole tooling preflight. **If a member is reported `[problem]`** (the 2026-08-25 Windows run got Red Hat YAML only from the `.vsix`), install the named members by hand from the Extensions view and run the check again; record the exit code of the `.vsix` install if you can |
| XSD schema reachable | keep the licensed schema **inside the project**, in the git-ignored `schemas/` directory (`.gitignore` § *Local secrets and licensed schemas*) — a machine temp directory is emptied between sessions and takes the preflight with it. A git-ignored `.env` carries the absolute path, `SWCRAFT_AUTOSAR_XSD_PATH=<project>/schemas/AUTOSAR_4-3-0.xsd`, written without a BOM. The basename must be the one the declared version expects (`AUTOSAR_4-3-0.xsd` at `arxml_version: "4.3.0"`): a renamed copy is refused and validation silently stays structural. Confirm with `git check-ignore -v schemas/AUTOSAR_4-3-0.xsd`; panel *Build* must end with `ARXML validated against …` |
| `.vscode/settings.json` present | committed since 0.4.0 (the `.arxml` LemMinX filter); `git status` clean means it is there |
| The guide opens from the panel | since 0.5.2 the rendered user guide ships inside the `swcraft-tools` wheel, so the pinned toolchain already carries it. **Open Guide** in the `…` menu at the top of the SWCraft view must open it in VS Code's Simple Browser. Click it **once the day before**: the server binds `127.0.0.1` on a port the OS picks, and a first bind can raise a firewall prompt on Windows, where the command is unmeasured. No network is used, and there is nothing to download or unpack |
| Tool permissions granted | on first use VS Code asks to allow each `swcraft/*` tool — answer **Allow in this Workspace** the day before, so no prompt appears on stage |
| MCP server registered | since 0.7.0 nothing in the project configures it: the SWCraft extension registers one server per open folder whose root holds `swcraft.yaml`, from the workstation installation, with `SWCRAFT_REVIEW=panel`: a change set is reviewed in a SWCraft review tab, whichever client proposes it. There is no `.vscode/mcp.json` and no *Repair MCP Config* any more; a fresh clone needs nothing done to it |
| MCP server starts | Copilot Chat → agent **SWCraft Architect** → ask "which SWCraft version and baseline?" — it must answer through `discover` with the installed release (`0.24.0`) and a `rev1:…` token |
| Kiro, when it is shown | SWCraft's extension installed into Kiro from the archive's `swcraft-vscode-0.24.0.vsix` (Extensions view → `…` → *Install from VSIX…*; the installer hands it to VS Code only); the project folder opened, **trusted** and the window reloaded once (**Developer: Reload Window**); Kiro's MCP servers view shows `swcraft` connected, its hooks list **SWCraft model guard**, its chat `.kiro/steering/swcraft.md` under **Included Steering**. Ask the same version question once: Kiro asks **Allow** before every SWCraft tool call, on stage too (`demos/chat-with-the-model.md` § 1) |
| Copilot request budget | a full run uses ~4 requests (rehearsal 3); on the Free plan keep ≥ 10 of the month's 50; Pro removes the concern |
| Fresh chat | start a **new** chat for the presentation; the agent must find everything itself |
| Result of the last rehearsal **not committed** | *(history: `main` now holds the storefront, which commits the feature; the tag `showcase-feature-001` does not load at the pinned release)* |
| Deck synchronized with this script and with the installed release | walk the § 3 map once against the deck; refresh the deck's appendix *What runs today* and the *Pilot* slide to the release actually installed; record the deck revision in the presentation's evidence file |

**Model states** *(history — neither tag loads at the pinned release; see the note above § 1).*
*Baseline* is tag `showcase-baseline-001` (BL-SHOWCASE-001): five SWCs, six
sender-receiver interfaces, two tasks on `Core0`, one sequence (`baseline_50ms_cycle`), two
requirements, **no connectors** — the unconnected ports are the endpoints the feature will
connect. Budgets: `RAM` 32768 B / 0.75 strict with 10240 B used; `Core0` 0.7 strict with 22 %
used. *Feature* is tag `showcase-feature-001`: the baseline plus `BrakeThermalProtection`
(FB-SHOWCASE-001), as the old § 7 produced it.

Reset to the baseline: `git checkout showcase-baseline-001 -- model && git clean -fd model`,
then *Build* from the panel, which regenerates every artifact in one press. To start at the
feature state instead:
`git checkout showcase-feature-001 -- model`.

### 4a. Where things are (VS Code)

Since 0.4.0 the product answers this itself: **Welcome → Open Walkthrough → "The first hour with
SWCraft"** is the guided version of this table, and a newcomer in the audience can be pointed at
it. For the presenter:

- **SWCraft panel**: the two-blocks-and-connector icon in the Activity Bar. Three sections —
  **Model** (Build, Check Model, Diagrams, Change Report, Resource Report, Architecture Metrics,
  Export Component, Import Component, Import Requirements), **Experiments** (Allocation, Trace
  Links) and
  **Setup** (Install Toolchain, Update Toolchain, Onboard Project), which folds away once the
  toolchain is installed and the project onboarded. **Open Guide** and **Check Editor Tooling** are
  in the `…` menu at the top of the SWCraft view; **Impact** is no panel item — it is asked from an
  element's file. Every item shows `built HH:MM`-style status that clears itself.
  **Do not use *Check Model* on stage in place of *Build*.** It is the fast edit-loop check —
  the same model checks with no ARXML written and no schema compiled — and the whole point of
  the rejected changes is that the gate is what refuses; say `Build` wherever it matters, and
  `swcraft validate` is the gate it ends in.
- **Chat mode**: in the Copilot Chat input, the mode dropdown lists **SWCraft Architect** —
  select it; plain *Agent* answers from files and never calls the server. **The selection does
  not persist**: every new chat, and every reopening of the folder, starts in plain *Agent*.
  Since § 4 requires a fresh chat, selecting the mode is a step of the run, not a setting made
  the day before — do it before the first prompt and after any reload. Kiro has no such choice:
  its chat reads SWCraft's instructions from `.kiro/steering/swcraft.md` by itself.
- **Import tabs**: *Import Requirements* and *Import Component* each run their import as a dry run
  first and open its report in a tab — *Requirements Import Report*, *Component Import Report* —
  with **Write** and **Cancel** under it; nothing is written before **Write**. The requirements
  exchange segment (`demos/requirements-exchange.md`) uses *Import Requirements* twice; no other
  step of this script uses either tab, and none uses *Import Component*.
- **Review tab**: a change set opens a SWCraft review tab beside the editor, with the exact delta
  and two buttons, **Approve** and **Reject**; one click decides, and typing in the chat does
  nothing. The question waits until it is answered, and the assistant shows progress every
  minute meanwhile. A tab closed unanswered is reopened from the **Pending Change Sets** view.
- **Diagrams**: panel → *Model → Diagrams* draws the views into `views/` and opens
  `views/index.html` in a tab of the editor — plain files, no viewer process and no browser; a
  Ctrl+click (Cmd+click on macOS) on a drawn element opens its YAML file beside the diagram. On the storefront the index
  lists eleven views: the internal block diagram and the overview of each of the three
  compositions (*VehicleControl*, *Chassis*, *BrakeSubsystem*), the nesting view, the deployment
  view and three sequence diagrams (*brake_thermal_cycle*, *thermal_protection_fast_path*,
  *thermal_status_display*); each page has a search box for a name.
- **Source Control**: the branch icon in the Activity Bar.

## 5–9. The segments, on the storefront

These five sections held the script for the five-component baseline, suspended since revision 4.0
because neither of its tags loads at the release this project pins; revision 6.0 replaced them. The
old text is in this document's git history. The segments that run today, each from the committed
model and leaving it so (the § 3 map places them against the deck):

- **The assistant, constrained** — `demos/chat-with-the-model.md`: an architect's question answered
  from the model, an impact question (what a change to `INvStorage` affects), one change proposed
  and **rejected** in the SWCraft review tab with nothing written, and the model guard refusing the
  assistant's own file tools — Copilot a direct read of a model file, Kiro a direct edit. The same
  steps in Copilot and in Kiro; the page says where the two differ.
- **The model refuses** — `demos/README.md`: the nine rejected changes, each a small edit by hand
  that **Build** (or `swcraft check-model`) refuses by exactly the rule it names, the incompatible
  connector and the RAM budget among them.
- **What the architect gets** — `demos/test-tables.md` (the test tables with a test team's review)
  and `demos/requirements-exchange.md` (requirements in, links out).

## 10. Known deviations and what to do

| What you see | Cause | Do |
|---|---|---|
| Agent answers from files, never calls the server | plain *Agent* mode selected — the mode does not persist across chats or window reloads, so this is the expected starting state, not a fault | switch to **SWCraft Architect**; say nothing, it is a mode switch |
| Kiro's chat says it has no SWCraft tools, or a direct edit of the model is not refused | the folder is not trusted, or trusted without the reload: Kiro has read neither `.kiro/settings/mcp.json` nor the guard's hook | trust the folder, run **Developer: Reload Window** once, and check the MCP servers view and the hooks list (§ 4) |
| Kiro asks **Allow** before every SWCraft call, and calls `tool_load` first | Kiro's own permission step and its way of loading a server's tools — not the review | answer **Allow**; the review still comes in the SWCraft review tab |
| "result too large for inline view", or the agent opens a saved tool output with `view` | full `discover` is ~20 KB, and Copilot saves an answer above about 8 KB to a temporary file; since 0.16.0 the agent reads that file in parts | let it; costs nothing visible. A `view` or a search of `model/` refused by the model guard (`.github/hooks/swcraft.json`) is the guard working: the agent asks SWCraft instead |
| A QuickPick falls back to typing a name | the project venv predates 0.4.0 (`swcraft list` missing) | the fallback works; install the pinned release's archive after the demo |
| Red Hat XML notification about Java / binary server | its own runtime choice, once | dismiss; not SWCraft's |
| Red marker on a **valid** `.arxml` | `.vscode/settings.json` (the LemMinX filter) missing — pre-0.4.0 checkout | re-run *Onboard Project*; the filter is scaffolded since 0.4.0 |
| No SWCraft icon | Activity Bar entry hidden on this machine | right-click the Activity Bar → tick *SWCraft*; or `⇧⌘P` → `SWCraft: Build` |
| SWCraft view absent entirely, "Restricted Mode" in the status bar | the folder is untrusted; the extension declares why (visible on its Extensions page) | trust the folder |
| Review tab never opens, nothing is written | `SWCRAFT_REVIEW` not `panel` (a server started by hand starts fail-closed: it does the work and writes nothing), or no VS Code window open on the project with the SWCraft extension — the review waits until it is answered, and without such a window nobody can answer it, so the assistant goes on waiting | stop; use the server the SWCraft extension registers, with VS Code open on the project — check this the day before |
| Anything that needs the contract, the protocol, the tool set or ARXML bytes to change | architectural finding | stop the demo there, keep your own record of it, decide on `main` |

## 11. Records

Every rehearsal and the presentation itself leave one record, kept by whoever runs it, with the
configuration table, the run, the observations and the request count. Rehearsals 1–2
(2026-08-23) ran on `0.3.x` with the pre-2.0 segment order; the first `0.4.x` rehearsal starts
the count again for the entry condition.

The entry condition for scheduling the team presentation is **one clean pass over every segment
on the release that will be presented**, from a fresh chat and a reset model. Nothing about it is
timed: the presentation is expected to be interrupted, so a measured run would not predict it.
A later change to the script re-runs only the segment it touched; a later change to the product
re-runs the whole script. On that rule the segments that replaced §§ 5–9 in revision 6.0 owe one
run on the presenting host, in Copilot and in Kiro; none has been made yet.

Met by the Windows run of 2026-08-26 (the maintainer's evidence record of that run)
— every segment, on the presenting host, with the corporate Copilot and XSD validation — on
`0.5.0`. The rehearsals before it: 1–2 on `0.3.x` (2026-08-23), 3 on `0.4.0` (2026-08-24), and a
partial Windows run of 2026-08-25 that covered §§ 6–7 only. That condition was met by the baseline
script, which revision 6.0 replaced; it is not met by the storefront's segments.

## 12. Revision History

| Revision | Date | Change |
|---|---|---|
| 0.1–0.10 | 2026-08-23 | First script and its same-day refinements on `0.3.x` (see git history) |
| 1.0 | 2026-08-23 | Segments reordered to follow the presentation deck; slide → segment map |
| 3.3 | 2026-09-06 | Applies to 0.8.0: § 4's toolchain, extension and MCP rows carry the new release — the archive and `.vsix` filenames, the pin, the version *Check Editor Tooling* reports and the release `discover` answers. The schema count is unchanged at 11, and nothing the script's segments click has changed |
| 3.4 | 2026-09-07 | Applies to 0.9.0: § 4's toolchain, extension and MCP rows carry the new release — the archive and `.vsix` filenames, the pin, the version *Check Editor Tooling* reports and the release `discover` answers. The model gains `model/compositions/VehicleControl.yaml` (the root the release requires) and loses `containers/`; the C4 the script opens now has a composition level. Two preflight facts learned on 2026-09-07 on corporate Windows hosts: VS Code below 1.110 refuses the `.vsix`, and the C4 preview needs a Node.js ≥ 22.22 (`likec4.node.path`), which the install page now states |
| 5.1 | 2026-10-25 | Applies to 0.19.2: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile is re-copied from the release's template: every listing recipe answers a page of twenty rows with the total and the cursor for the rest, the sender-receiver table five, and the number of components per level comes as one count per level; the instructions and the hook are unchanged. §§ 5–9 stay suspended |
| 5.2 | 2026-10-29 | Applies to 0.20.0: § 4's toolchain, extension and MCP rows carry the new release; the MCP row's registration is `SWCRAFT_REVIEW=panel`, and *Check Editor Tooling* and *Open Guide* are in the `…` menu of the SWCraft view (the guide opens in VS Code's Simple Browser). The project's Copilot files are re-copied from the release's template. § 4a's panel lists the Model and Setup sections as 0.20.0 has them, and the review prompt is the SWCraft review tab with **Approve** and **Reject**. Every step is re-read against the release: § 5's failing *Build* ends in Problems with the rule name linking to the guide and the passing one in the build report; § 7 approves in the review tab and its *Build* ends in the build report; § 8 C reads the **Resources** view; § 9's *Impact* is asked from `IBrakeTemperature`'s file and answered in the **Impact** view, *Export Component* opens the exported file, and *Open Guide* is in the `…` menu; § 10's review row names `panel`, the ten-minute wait, and no longer *Repair MCP Config*. §§ 5–9 stay suspended |
| 5.3 | 2026-11-03 | Applies to 0.21.0: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot files are re-copied from the release's template: the review question waits until it is answered, and a question about the architecture's state goes to the new `architecture_metrics` tool. § 4a's *Model* section gains **Architecture Metrics**, which no step of this script uses, and its review tab waits until answered; § 10's review row loses the ten-minute wait — without a VS Code window on the project nobody can answer, and the assistant goes on waiting. Nothing else the script clicks has changed. §§ 5–9 stay suspended |
| 6.0 | 2026-11-10 | Applies to 0.23.0: § 4's toolchain, extension and MCP rows carry the new release, and § 4 gains a row for Kiro — SWCraft's extension installed into Kiro from the archive's `.vsix`, the folder trusted and the window reloaded once. The title and § 1 name Copilot and Kiro: the project now commits Kiro's three files beside Copilot's. **§§ 5–9, suspended since revision 4.0, are replaced by pointers** to what runs on the storefront — `demos/chat-with-the-model.md` (a question, an impact question, a change rejected in the review tab and the model guard, the same steps in both clients), the rejected changes of `demos/README.md` and the test tables and requirements exchange pages — because the baseline they scripted does not load at the pinned release; § 3's map, its paragraph on cutting a session short, § 11's entry condition and the note above § 1 follow. The note said *seven* rejected changes; there are **nine** since the two implicit-access refusals of 0.23.0. § 4a: *Diagrams* opens a tab of the editor, not the browser; the agent is named as the dropdown shows it, **SWCraft Architect**. § 10 gains two Kiro rows |
| 6.1 | 2026-11-10 | § 1's *No command line anywhere* is corrected: the requirements exchange, which revision 6.0 brought into the script, applies its prepared links by two lines pasted into VS Code's terminal, because the panel's **Apply…** writes the decisions of the last search, not a proposals file prepared beforehand; every other step stays in the SWCraft panel or its tabs (a rejected change is checked by *Model → Check Model*, the test tables open in their own tab) |
| 6.2 | 2026-11-10 | § 4a's *Import tabs* no longer says no step of this script uses them: the requirements exchange segment, which revision 6.0 brought into the script, uses *Import Requirements* twice; no other step uses either tab, and none uses *Import Component* |
| 6.3 | 2026-11-13 | The open copy: the evidence records are the maintainer's records in the work repository and are not part of the open copy, so § 10's architectural-finding row and § 11 ask whoever runs the script to keep their own record of the run, and § 11 and revision 5.4 name a record by what it recorded instead of by its path. No step of the script changed |
| 6.4 | 2026-11-26 | Applies to 0.24.0 (contract `12.7.1`, a patch): § 4's toolchain, extension, MCP and Kiro rows carry the new release; the toolchain row points at WI-SHOWCASE-001 § 8.3, which names where the archive comes from and how it is checked and installed. The XSD row is unchanged: the release reads a `.env` from the project's folder only, which is where this row keeps it. The client files are taken from a fresh 0.24.0 scaffold; Kiro's steering now sends a question about SWCraft to `guide` first. No step of the script changed |
| 5.4 | 2026-11-08 | Applies to 0.22.0: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot files are re-copied from the release's template: the assistant reads the guide's How-to pages through the new `guide` tool, and the instructions name the needs file `dist/needs.json` in place of the RST. § 4a's panel is re-read against the release: its *Model* section gains **Import Component** and **Import Requirements**, whose dry-run reports open in the tabs *Component Import Report* and *Requirements Import Report* with **Write** and **Cancel** — no step of this script uses them — and the *Experiments* section, which the table had left out, is named. The trace link demonstration's requirements left the model for the requirements exchange (`demos/requirements-exchange.md`); nothing else the script clicks has changed. §§ 5–9 stay suspended. Evidence: the migration's evidence record. |
| 5.0 | 2026-10-23 | Applies to 0.19.1: § 4's toolchain, extension and MCP rows carry the new release, and the extension row's version, left at 0.18.1 by revision 4.9, now names it too. The project's Copilot agent profile is re-copied from the release's template: `impact_of`'s summary of a large walk answers a page with its `next` cursor, the unconnected ports are asked as a count and then twenty at a time, also for one component, and `find` with more than three names answers fewer candidates per name; the instructions and the hook are unchanged. §§ 5–9 stay suspended |
| 4.9 | 2026-10-23 | Applies to 0.19.0: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile and instructions are re-copied from the release's template: the profile now carries the model's schema, so the agent changes the model without first asking `discover` for it, and a project-wide `discover` answers the baseline token and the passport; the hook is unchanged. The two port-checking tools are withdrawn from the MCP server, so § 6 step 2's narration names staging, which checks each connector, instead of a check per pair. §§ 5–9 stay suspended |
| 4.8 | 2026-10-21 | Applies to 0.18.1: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile, instructions and model-guard hook are already the release's template files, byte for byte. The Change Report's verdict line now adds, in brackets, the findings the model already had — on this model `(32 already in the model)`, the warnings by design — so § 7 step 4 says so; the preview is redrawn on every run, and `swcraft change-report` also writes `change-report-pr.md` (the report without its *Diagrams* section, for a pull request), which no step of this script opens. §§ 5–9 stay suspended |
| 4.7 | 2026-10-21 | Applies to 0.18.0: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile and instructions are re-copied from the release's template, which links a new component to a requirement only when the user names the requirement it realises, and no longer calls a component without a link a warning; the hook is unchanged. The model now carries the trace link demonstration's 46 synthetic requirements and 32 warnings by design, which no step of this script reads; the panel's *Import Requirements* (no ellipsis since this release) asks one question, and *Experiments* gains *Trace Links*, which no step of this script uses. The panel's *Diff* is gone: **Change Report** (palette *SWCraft: Change Report*) compares the working tree with `HEAD` and opens a Markdown report, so § 4a's list and § 7 step 4 name it; `swcraft diff`, which § 6 types, is unchanged. §§ 5–9 stay suspended |
| 4.6 | 2026-10-19 | Applies to 0.17.1: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile, instructions and model-guard hook are already the release's template files, byte for byte. The release fills the Problems panel after *Check Model* at once on a project with thousands of findings; this model has one, and no step of this script waits on it. §§ 5–9 stay suspended |
| 4.5 | 2026-10-16 | Applies to 0.17.0: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile and instructions are re-copied from the release's template, which writes a trace link as the component's `satisfies` entry (`"satisfies": ["REQ_001@1"]`) and calls a component that satisfies no requirement a warning, not a refusal, and names the Sphinx-Needs export under `dist/needs/` among the generated artifacts; the hook is unchanged. The panel gains *Import Requirements…*, which no step of this script uses. The § 7 prompt's "linked to the new SWC" still states the intent; the link the assistant writes is now a `satisfies` member of the component, not a `links` entry of the requirement; this script has not been run on 0.17.0. §§ 5–9 stay suspended |
| 4.4 | 2026-10-15 | Applies to 0.16.2: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile, instructions and model-guard hook are already the release's template files, byte for byte. The line of links above an element's `name:` reads a plain `references`, whose click is Find All References; no step of this script reads its count. §§ 5–9 stay suspended |
| 4.3 | 2026-10-14 | Applies to 0.16.1: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile, instructions and model-guard hook are already the release's template files, byte for byte, and nothing the script's segments click has changed. §§ 5–9 stay suspended |
| 4.2 | 2026-10-13 | Applies to 0.16.0: § 4's toolchain, extension and MCP rows carry the new release. The project's Copilot agent profile and instructions are the release's template files, and the project carries the model-guard hook, so the agent may `view` a saved SWCraft answer and is refused a read of `model/`; § 10's large-answer row says so. §§ 5–9 stay suspended |
| 4.1 | 2026-10-10 | Applies to 0.15.0: the *Applies to* row carries the new release. The model gains two partitions, a second occurrence of the brake temperature sensor and `B(D)` levels (FB-SHOWCASE-001 revision 0.3); the deployment view the script would click draws the partitions. §§ 5–9 stay suspended; the re-scripting onto the storefront is the next revision |
| 4.0 | 2026-10-08 | `main` holds the storefront (FB-SHOWCASE-001 revision 0.2): the two tags are marked as history that does not load at the pinned release, §§ 5–9 are **suspended until re-scripted onto the storefront**, and `demos/` is named as the refusals that run today. § 4's toolchain and *Check Editor Tooling* rows name `0.14.0` — revision 3.9 moved the rest of § 4 and left those two at `0.13.0`. The *Check Editor Tooling* row counts 16 editor schemas — fifteen layers and the manifest — where it still said 11, and § 4a's *Diagrams* bullet lists the storefront's eleven views in place of the baseline's. No segment was re-scripted |
| 3.9 | 2026-10-08 | Applies to 0.14.0: § 4's toolchain, extension and MCP rows carry the new release. The model moved to the seven data-type layers under `data_types/` (two base types, two value types, the empty `mapping_sets/` beside them), every interface element says `implementation_type:`, and every component declares `handle_termination_and_restart: no_support`; the editor schemas and the panel are 0.14.0's. The script itself is unchanged. |
| 3.8 | 2026-09-23 | Applies to 0.13.0: § 4's toolchain, extension and MCP rows carry the new release. The model gains the empty `mapping_sets/` layer, so the editor schemas are 11 again (0.12.0 shipped 10; this row's figure was not moved then). *Diagrams* draws a fifth view, `deployment`, and a save no longer redraws anything — every step of the script already presses *Build* or *Diagrams* after an edit, so no click changed. The generated ARXML is unchanged. **Not yet rehearsed at 0.13.0** |
| 3.7 | 2026-09-17 | § 4's toolchain row and § 10's QuickPick row no longer name `setup-showcase`: the Python preflight and its two launchers are retired (WI-SHOWCASE-001 revision 0.10), and the toolchain check is `swcraft --version` plus `moon run :build`. No click of the script changed |
| 3.6 | 2026-09-17 | Applies to 0.12.0: § 4's toolchain, extension and MCP rows carry the new release, and the extension row names two companion members (Red Hat YAML, Red Hat XML) — the LikeC4 extension left the pack with the viewer. *Diagrams* now draws the views into `views/` as SVG and HTML files and opens `views/index.html` in the browser; there is no viewer process, no `views/model.c4` and no CodeLens, so § 4's *LikeC4 preview* bullet is *Diagrams*. The model loses its empty `systems/` layer and its manifest the `c4:` line; the generated ARXML is unchanged. **Not yet rehearsed at 0.12.0** |
| 3.5 | 2026-09-15 | Applies to 0.11.0: § 4's toolchain, extension and MCP rows carry the new release. The panel's *Validate*, *Generate C4* and *Open Generated C4* are gone from the product — § 4a, § 5 and § 7 now click **Build** (clean-outputs → check-model → the three generators → validate, in one output channel) and **Diagrams** (the views in the browser, in LikeC4's own viewer, on the Node.js the archive carries). The archive needs no Python, no Node.js and no Marketplace access on the host, so § 4's preflight loses those. The model's `uint8`/`uint16` are value types over new base types (contract `5.0.0`) and the generated ARXML moves with it: no `_impl` twins. **Not yet rehearsed at 0.11.0** — the clicks above are the release note's item names, not an observed run |
| 3.2 | 2026-09-05 | Applies to 0.7.0: § 4's toolchain, extension and MCP rows follow the workstation archive — one installation per machine, the project pins it and installs nothing, the extension registers the server itself and the `mcp.json` row is gone. Nothing the script's segments click has changed |
| 3.1 | 2026-08-27 | § 9 gains the guide: 0.5.2 ships the rendered site inside the `swcraft-tools` wheel and *Open Guide* is the panel's thirteenth item, so the documentation is shown where the architect already is — no terminal, no archive, no network, and no way for it to describe another release. § 4 gains the day-before click, § 4a the item |
| 3.0 | 2026-08-26 | **All timing removed** — the 30-minute box, the per-segment estimates and the "timed" half of the entry condition. The presentation is interrupt-driven by decision: questions are welcome at any point, so a stopwatch-verified run predicts nothing and costs a rehearsal to produce. § 9 still shortens first, on content grounds |
| 2.10 | 2026-08-26 | § 4a: the panel gained *Check Model* in 0.5.1, with the one line the presenter needs — it is the edit loop, *Validate* stays the gate and the script's clicks are unchanged |
| 2.9 | 2026-08-26 | From the Windows 0.5.0 full pass: selecting `swcraft-architect` is a step of the run, not a setting — the mode resets to plain *Agent* in every new chat and on every window reload |
| 2.8 | 2026-08-26 | § 4 corrected against the Windows 0.5.0 update: `discover` answers the installed release, not `0.4.x`; the licensed schema lives in the project's git-ignored `schemas/`, not in a machine temp directory |
| 2.7 | 2026-08-26 | Applies to 0.5.x (the documentation release; nothing the script exercises changed) |
| 2.6 | 2026-08-26 | `mcp.json` is generated and git-ignored (0.5.0); the skip-worktree workaround row replaced by "run Repair MCP Config once after cloning" |
| 2.5 | 2026-08-26 | Entry condition restated: one clean timed rehearsal on the presented release; status *Ready to schedule* (the timing half was dropped again in 3.0) |
| 2.4 | 2026-08-26 | From the Windows first run: manual completion of the pack when a member is missing; the Windows `mcp.json` rewrite; the by-hand refusal is safe on Windows through the panel, not through moon |
| 2.3 | 2026-08-24 | 30-minute time box; § 9 is the segment to shorten under time pressure |
| 2.2 | 2026-08-24 | Segment times set to rehearsal 3's narrated measurements (~25 min total); request budget corrected to ~4 per run |
| 2.1 | 2026-08-24 | § 6: the panel *Diff* on an unchanged model dropped (rehearsal 3 finding — a dead moment); it stays in § 7 where it has content |
| 2.0 | 2026-08-24 | Rewritten for `0.4.x`: editor completion/hover/diagnostics in § 5; panel Diff/Impact/Resource Report and the QuickPicks replace the terminal moment and typed names; named C4 views and automatic Sequence mode in § 7; Check Editor Tooling as the tooling preflight; walkthrough referenced for newcomers; deviations table updated |
