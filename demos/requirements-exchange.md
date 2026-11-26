# The requirements exchange

This walkthrough follows requirements from the team that writes them into the architecture and back
again. A synthetic **requirements team** keeps its software requirements in a Sphinx-Needs project
and hands the architect a delivery, a `needs.json` file. The architect imports it, links the new
requirements to the elements of the model that realise them, and builds the model: the build writes
the architecture as a `needs.json` of its own, which the team's Sphinx site shows beside its
requirements. Then the team changes one linked requirement and drops another, and both sides see the
link turn unconfirmed until the architect confirms it again.

Everything here runs on this project as it is committed, in VS Code and on the command line. The data
is synthetic: the team, its requirements and their texts are written against this showcase's own
element names and derived from no real project.

## What the project holds

The committed model is the state **before** the team's delivery 1.0. It carries eleven requirements:
the brake thermal protection feature's six architecture requirements, its four external requirements
from the team's earlier delivery `0.9` (`baseline: "0.9"`), and the stub `HAZ_BTP_BRAKE_FADE`, the
safety goal's parent from the hazard analysis. No software requirement of the team is in the model
yet, and nothing links to one.

`swcraft check-model --project swcraft.yaml` prints **4 warnings** by design: the stub's, and three
for the feature's one stale case (`REQ_BTP_TEMPERATURE_RANGE` at version 2, its three interfaces
still at `@1`), which this walkthrough leaves alone.

The scenario's files are under `demos/requirements-exchange/`:

| File | What it is |
|---|---|
| `deliveries/1.0/needs.json`, `deliveries/1.1/needs.json` | the team's two deliveries, as its Sphinx-Needs build wrote them |
| `team.needs-mapping.yaml` | the architect's mapping of the team's vocabulary onto SWCraft's |
| `answer-key.json` | the presenter's script for step 2: for each software requirement, the element its text was written against, or none for a distractor |
| `prepared-links.json` | step 2's prepared links: the whole answer key accepted and every distractor's row rejected, as a proposals file |
| `sites/1.0/`, `sites/1.1-unconfirmed/`, `sites/1.1-confirmed/` | the requirements team's site, ready-made, for steps 4 and 5; beside each, the architecture's `needs.json` it was built from (`sites/1.0.needs.json`, …) |
| `sites/1.0-original/` | the team's site of delivery 1.0 as the team built it, before any architecture was handed over: the requirements without a link to SWCraft, the "before" of step 4 |
| `team/` | the requirements team's Sphinx project: `conf.py`, `requirements.txt` and the sources of both deliveries |

The same exchange, told to an audience in ten slides (*Enrich, never change*), is
[`requirements-exchange-presentation-public.html`](requirements-exchange-presentation-public.html)
beside this page: open it in a browser.

The team writes in its own words: a software requirement is a `swreq`, a safety goal an `sgoal`, the
ASIL is `safety`, the revision `rev`, and a requirement names its parent with `parent`. Each delivery
also holds two of the team's test cases (`test`), which the architecture does not import. The mapping
says all of that once, and it also names the requirement's text: Sphinx-Needs writes a directive's body
as `content`, which the mapping states as the source of `description` instead of leaving it to
SWCraft's default. Its comments say, block by block, which side is SWCraft's and which the team's: a
key under `types` is a value of the team's `type` field, a key under `fields` is SWCraft's field and
its value the team's key. `.vscode/settings.json` names it in `swcraft.requirementsImport.mapping`, so
the editor offers it.

Delivery 1.0 holds 50 requirements: the 46 software requirements, 42 of them in four documents
(*SRS Brake Control*, *SRS Thermal Protection*, *SRS Diagnostics*, *SRS Driver Information*) and four
with none, and the feature's four external requirements, now at `1.0`. Eight of the 46 are
**distractors**: texts the architecture does not realise (*Pedal feel*, *Cooling estimate*, *Warning
lamp*, …), which should end up rejected or left alone, never linked.

`answer-key.json` is this walkthrough's script, not a claim about the search. `prepared-links.json` and
the sites were prepared from it in the repository (`scripts/generate_requirements_prepared.py`).

## 0. Setup

**From the kit:** unpack the zip into a **new, empty** folder and open that folder in VS Code. In the
SWCraft panel press *Model → Build*: green, with the **4 warnings** in the **Problems** panel. The kit
carries no build graph; on the command line the same is the four commands below, the first of which
empties the generated outputs, as the panel's Build does first:

```text
swcraft clean-outputs --project swcraft.yaml
swcraft validate --project swcraft.yaml
swcraft generate diagrams --project swcraft.yaml
swcraft generate needs --project swcraft.yaml
```

**From the repository**, at a clean checkout: `moon run :build`.

`swcraft generate needs` writes `dist/needs.json`, the architecture as the team's Sphinx-Needs build
reads it. Before delivery 1.0 it names the team's delivery `0.9`.

## 1. Import delivery 1.0

**In VS Code:** in the SWCraft panel, *Model → Import Requirements*.

1. The file dialog opens at the project folder: choose
   `demos/requirements-exchange/deliveries/1.0/needs.json`.
2. The list asks how the team's needs map to SWCraft's: choose
   `demos/requirements-exchange/team.needs-mapping.yaml`, marked *last used* (the committed setting).
3. The version box comes filled with `1.0`, the version the delivery names: press Enter.
4. The dry run's report opens in the tab *Requirements Import Report*. Its first lines say what was
   read:

   ```text
   Requirements import: baseline 1.0 (from the file)
   Mapping: demos/requirements-exchange/team.needs-mapping.yaml
   Not imported: 2 needs of a type the mapping ignores (test)
   Dry run: nothing was written.
   Summary: 46 added, 0 changed, 0 removed, 0 stubs created, 4 source updates
   ```

   The *Mapping* line names the mapping file relative to the project folder, in VS Code and on the
   command line alike.

   The 46 software requirements are added at version 1; the four external requirements the model
   already holds stay as they are, and only their `baseline` moves from `0.9` to `1.0` — the four
   *source updates*. The team's two test cases are left out because the mapping ignores their type.
5. Press **Write**. The import runs again, for real, and its report replaces the dry run's in the tab;
   the tab then offers **Check Model**.

A delivery is the complete set: a requirement an earlier delivery held and this one does not would be
in the report's *Removed* list. Delivery 1.0 removes nothing.

**On the command line:**

```text
swcraft import requirements --source demos/requirements-exchange/deliveries/1.0/needs.json --mapping demos/requirements-exchange/team.needs-mapping.yaml --project swcraft.yaml --dry-run
swcraft import requirements --source demos/requirements-exchange/deliveries/1.0/needs.json --mapping demos/requirements-exchange/team.needs-mapping.yaml --project swcraft.yaml
```

Without `--mapping` the import is refused: the team's types are not SWCraft's, and the error names the
first one it meets and says to map it under `types`.

`swcraft check-model --project swcraft.yaml` now prints **50 warnings**: the 4 by design and one for
each of the 46 new requirements, which nothing satisfies yet.

## 2. Link

The trace link search proposes, the architect decides, and **Apply** writes the links that were
accepted. On stage the architect links a few requirements by hand, in **Labelling** — linking by
hand, with the requirements that teach the search the most listed first — and then loads the rest of
the answer key in one step, from a proposals file prepared beforehand. `experiments/trace.yaml` is
not changed: each search names its mode.

### By hand: Labelling of every requirement

**In VS Code:** in the SWCraft panel, *Experiments → Trace Links → Labelling*. The list shows every
document: tick all five (the four SRS documents and `BL-SHOWCASE-001`) and *No document*, and press
Enter. Requirements with no document can be labelled only together with every document, which is why
all are ticked. The search runs, and the **Trace Links** view shows *Labelling · …*: each document
lists first the few requirements that teach the search the most, each saying why; nothing is ticked
for you and no band is shown.

Link two requirements and reject one row:

- `SWR-THP-003`, the derating threshold: tick its third row, the port
  `BrakeThermalProtection.pPermittedBrakeAction`. That is the link step 5 turns unconfirmed.
- `SWR-BRK-008`, the brake pressure ramp: its element is not among the first three rows; open
  **More candidates** and tick its first row, the component `BrakeController`.
- `SWR-BRK-011`, *Pedal feel*, a distractor: ✕ on its first row, the runnable
  `BrakeTemperatureSensor.PublishBrakeTemperature`. A rejection records that the element does not
  belong there; it links nothing.

A requirement whose element the search does not list at all, such as `SWR-DIA-007` (the snapshot
content, realised by the runnable `DiagnosticManager.ProcessDiagnosticEvent`), is linked through
**Any element of the model…**; on stage it is left to the prepared links below.

Then **Apply…** (the row at the top of the **Trace Links** view): the dry run's report opens in the
tab *Trace Apply Report*, the same tab as the import's report — the report on top, **Write** and
**Cancel** under it, no question in a dialog. It says what Write would do: the two links, into
two files, and the one rejection to record. Press **Write**: it writes exactly what the report
showed, and its own report replaces the dry run's in the same tab. **Cancel**, or closing the tab,
writes nothing. The summary:

```text
Summary: 2 written, 0 confirmed, 1 rejected, 0 already done, 0 stale, 0 not written, 553 undecided; 2 files
```

`swcraft check-model --project swcraft.yaml` prints **48 warnings**.

**On the command line:** search, decide in the proposals file, look, write:

```text
swcraft experiment trace --project swcraft.yaml --config experiments/trace.yaml --labelling '"all"'
```

In `dist/experiments/trace/proposals.json`, set a row's `"decision"` to `"accept"` or `"reject"`, or
add `{"target": {"kind": "runnable", "owner": "DiagnosticManager", "name": "ProcessDiagnosticEvent"}}`
to a requirement's `"chosen"` list for an element that is not a row. Then

```text
swcraft experiment trace --project swcraft.yaml --apply dist/experiments/trace/proposals.json --dry-run
swcraft experiment trace --project swcraft.yaml --apply dist/experiments/trace/proposals.json --expect-plan sha256:…
```

The dry run prints what would be written and a `Plan:` line; passing that value to `--expect-plan`
writes exactly that, or refuses if anything changed in between. Adding `--report
dist/trace-apply.md` to either run also writes its report as a Markdown document with the tables the
tab shows; a path not ending in `.md` gets the text the run printed.

### The prepared links: the rest in one step

The rest of the answer key was prepared beforehand: `demos/requirements-exchange/prepared-links.json`
is the proposals file of a Review search of every requirement, made after importing delivery 1.0,
with every link of the answer key accepted — a row, or a `chosen` entry where the search does not
list the element — and every row of the eight distractors rejected. Apply marks what it did in the
file it applies, so the prepared file is applied from a copy in `dist/` and stays as it is.

In VS Code, open a terminal in the project folder (*Terminal → New Terminal*) and paste both lines at
once:

```text
cp demos/requirements-exchange/prepared-links.json dist/prepared-links.json
swcraft experiment trace --project swcraft.yaml --apply dist/prepared-links.json
```

VS Code's terminal on Windows is PowerShell, where `cp` works as written. In a Command Prompt, the
first line is `copy demos\requirements-exchange\prepared-links.json dist\prepared-links.json`.

Run them here, before any Build: a Build's first step empties `dist/`, the copy with it. The Apply
prints, first,

```text
Trace apply: proposals of the search 'trace' (the model has changed since the search)
Summary: 38 written, 0 confirmed, 73 rejected, 3 already done, 0 stale, 0 not written, 449 undecided; 10 files
```

and below it each link written and each rejection recorded. *(the model has changed since the
search)* is expected: the file was prepared before the two links and the one rejection made by
hand, and Apply checks every decision against the model as it is now, so those three count as
*already done*. Adding `--dry-run` to the second line shows the same without writing anything;
running the second line again writes nothing — *0 written, … 114 already done … No change.*

Now the 38 requirements the answer key links are linked, and `swcraft check-model` prints **12
warnings**: the 4 by design and the 8 distractors — a rejection records the decision, it does not
satisfy the requirement. A link made by hand to another element than the key's stays beside the
key's: remove it from the element's file, or start over (step 6).

## 3. Build

**In VS Code:** *Model → Build*: green, the 12 warnings in the **Problems** panel. Its first step
empties `dist/`, the last search's proposals file and the copy of the prepared links with it; the
applied decisions stay in `trace-decisions.yaml`.

**On the command line:** in the kit, the setup's four commands — `clean-outputs` first, which empties
`dist/` as the panel's Build does — or `swcraft generate needs --project swcraft.yaml` alone for the
needs file, which leaves the rest of `dist/` as it is; in the repository, `moon run :build`.

`dist/needs.json` now names `current_version` `1.0` and holds 52 needs: the six architecture
requirements and the 46 elements linked to a requirement, each with `swcraft_path`, its file
relative to `model/`. `PORT-BrakeThermalProtection-pPermittedBrakeAction`, for one, has
`swcraft_path` `swc/application/BrakeThermalProtection.yaml` and lists `REQ_SHOWCASE_FEATURE_001` and
`SWR-THP-003` under `satisfies`; the stale case's three interfaces list `REQ_BTP_TEMPERATURE_RANGE`
under `satisfies_unconfirmed`. The team's requirements are not in it: the file holds the
architecture and its links.

## 4. The team's site

The requirements team builds its site with its own tool, Sphinx-Needs, from its sources and the
architecture's `needs.json`. The project carries that site **ready-made**: open
`demos/requirements-exchange/sites/1.0/index.html` in a browser (in VS Code's Explorer, *Reveal in
File Explorer* or *Reveal in Finder* on the file, then open it).

To show what SWCraft added, open `demos/requirements-exchange/sites/1.0-original/index.html` beside
it: the same delivery as the team built it before the handover, with the same requirements and no
*satisfied by* and no section *Architecture requirements (SWCraft)*: the team's `conf.py` shows that
section only once the architecture's `needs.json` is there.

It was prepared from the state the steps above reach — exactly the `dist/needs.json` of step 3,
which lies beside it as `demos/requirements-exchange/sites/1.0.needs.json` — not from the
presenter's copy: if the presenter's links differ from the answer key, the ready-made site does not
show them.

- each of the team's requirements lists the elements that satisfy it under *satisfied by* —
  `SWR-THP-003` lists `PORT-BrakeThermalProtection-pPermittedBrakeAction`;
- the section *Architecture requirements (SWCraft)* lists the architect's own requirements, the six
  decisions no requirement of the team's asks for (the decomposition of the safety goal, the
  execution context, the temperature range, …), each with what it derives from and the elements
  that satisfy it — the ones that satisfy no requirement of the team's are listed only here;
- a click on an element under *satisfied by* opens its YAML file in VS Code, in the project open there — the unpacked
  kit, or the repository. The link is a `vscode://` address that SWCraft's extension answers: the
  browser asks to open VS Code, and VS Code asks once before handing the link to the extension. It
  needs VS Code with SWCraft's extension installed, and no network.

### To build it yourself

Optional: this runs the requirements team's tool, not the project's. It needs **Python 3.11 or
later** and **`pip` access to PyPI** on the presenter's machine; the project itself still installs
nothing. Once, in a folder outside the project:

```text
python3.11 -m venv <venv>
<venv>/bin/pip install -r demos/requirements-exchange/team/requirements.txt
```

(On Windows, `py -3.11 -m venv <venv>`, and `<venv>\Scripts\pip`, `<venv>\Scripts\sphinx-build`.)

**The handover.** Copy `dist/needs.json` to `demos/requirements-exchange/team/swcraft/needs.json` — in
the Explorer, or in a terminal:

```text
mkdir -p demos/requirements-exchange/team/swcraft
cp dist/needs.json demos/requirements-exchange/team/swcraft/needs.json
```

(In a Command Prompt: `mkdir demos\requirements-exchange\team\swcraft` and `copy dist\needs.json
demos\requirements-exchange\team\swcraft\needs.json`.)

How the file travels to a real team is the architect's choice; the folder is git-ignored. Then build
the team's site of delivery 1.0 into a folder `<out>` outside the project:

```text
<venv>/bin/sphinx-build -W -c demos/requirements-exchange/team -D version=1.0 -b html demos/requirements-exchange/team/delivery-1.0 <out>
```

It prints no warning (`-W` would turn one into a failure). `<out>/index.html` shows the presenter's
own links. Without `demos/requirements-exchange/team/swcraft/needs.json` the team's `conf.py` leaves
the architecture out: that is how the team built its deliveries.

## 5. Delivery 1.1

The team raises `SWR-THP-003`'s derating threshold from 600 to 650 °C (`rev` 2) and drops
`SWR-BRK-011`, *Pedal feel*, one of the distractors.

**In VS Code:** *Model → Import Requirements* again; choose
`demos/requirements-exchange/deliveries/1.1/needs.json`, the mapping
`demos/requirements-exchange/team.needs-mapping.yaml` marked *last used*, and keep `1.1` in the
version box. The report:

```text
Requirements import: baseline 1.1 (from the file)
Mapping: demos/requirements-exchange/team.needs-mapping.yaml
Not imported: 2 needs of a type the mapping ignores (test)
Dry run: nothing was written.
Summary: 0 added, 1 changed, 1 removed, 0 stubs created, 48 source updates
```

and under it the sections *Changed* (`SWR-THP-003 v1 → v2 (description, baseline, revision)`, with
`text: numbers 600 → 650`), *Removed* (`SWR-BRK-011 (was v1; absent from this delivery)`), *Source
information updated* (the 48 requirements whose `baseline` moves to `1.1`) and *Links now needing
confirmation*:

```text
SWC 'BrakeThermalProtection' (port 'pPermittedBrakeAction') satisfies 'SWR-THP-003@1'
```

Press **Write**.

**On the command line:**

```text
swcraft import requirements --source demos/requirements-exchange/deliveries/1.1/needs.json --mapping demos/requirements-exchange/team.needs-mapping.yaml --project swcraft.yaml --dry-run
swcraft import requirements --source demos/requirements-exchange/deliveries/1.1/needs.json --mapping demos/requirements-exchange/team.needs-mapping.yaml --project swcraft.yaml
```

`swcraft check-model` prints **12 warnings**: one distractor fewer, and one link to confirm more —

```text
WARNING: SWC 'BrakeThermalProtection' (port 'pPermittedBrakeAction') satisfies 'SWR-THP-003@1', but requirement 'SWR-THP-003' is at version 2: confirm the link against version 2 and write 'SWR-THP-003@2'.
```

Then **Model → Build** (step 3), so that `dist/needs.json` names delivery `1.1`: the team's site is
built from that file, and one built before this Build shows the state before the import.

**The team's site of delivery 1.1:** open `demos/requirements-exchange/sites/1.1-unconfirmed/index.html`,
prepared from the needs file beside it, `demos/requirements-exchange/sites/1.1-unconfirmed.needs.json`. `SWR-THP-003` now lists
the port under *satisfied by (unconfirmed)*: the architecture's `dist/needs.json` puts the link under
`satisfies_unconfirmed` and names `current_version` `1.1`. `SWR-BRK-011` is in neither file. To build
it yourself, copy the new `dist/needs.json` over the team's (step 4) and run

```text
<venv>/bin/sphinx-build -W -c demos/requirements-exchange/team -D version=1.1 -b html demos/requirements-exchange/team/delivery-1.1 <out>
```

**Confirm the link.**

- **In VS Code:** the **Problems** panel's quick fix on the warning, *Confirm link to SWR-THP-003
  (version 2)*, writes `SWR-THP-003@2` in the file. Or, through the search: *Experiments → Trace
  Links → Review*, every document and *No document* ticked, Enter. The Build removed the proposals
  file, so this searches again (or **New Search…**). Under `SWR-THP-003` the link awaiting
  confirmation has a checkbox: read the new text, tick it, then **Apply…** → **Write**. Leave the
  stale case's three links to `REQ_BTP_TEMPERATURE_RANGE`, which await confirmation too, unticked:
  they are part of the 4 warnings by design.
- **On the command line:** the search with `--labelling '[]'`; in the proposals file, under
  `SWR-THP-003`'s `"linked"`, set the entry with `"confirmed": false` to `"decision": "confirm"`; the
  dry run and the applied run — *0 written, 1 confirmed* in 1 file.

`swcraft check-model` prints **11 warnings**: the 4 by design and the 7 distractors left. **Model →
Build** again; the site `demos/requirements-exchange/sites/1.1-confirmed/index.html` (from
`demos/requirements-exchange/sites/1.1-confirmed.needs.json`) shows `SWR-THP-003` with the port under *satisfied by*, confirmed
on both sides. To build it yourself: copy and build the site of delivery 1.1 again, as above.

## 6. Start over

**From git**, in the repository:

```text
git restore --source=HEAD --staged --worktree -- model .vscode/settings.json
git clean -f -- model/requirements trace-decisions.yaml
rm -rf demos/requirements-exchange/team/swcraft
swcraft clean-outputs --project swcraft.yaml
```

The import rewrites `swcraft.requirementsImport.mapping` in the tracked `.vscode/settings.json`, so
the first line restores it too. `demos/requirements-exchange/team/swcraft/` is git-ignored, so `git clean -f` leaves it; the
third line removes it. `clean-outputs` empties the generated outputs, the copy of the prepared links
with them; `prepared-links.json` and the ready-made sites are never changed by the walkthrough. The
virtual environment and `<out>` are outside the project; delete them when you no longer need them.

**From the kit:** unpack the zip into a new, empty folder.

## What this does not show

- The bands are not probabilities. A *strong* element has strong evidence; it is not likely to be
  right because of its colour.
- The data is synthetic: the team, its requirements and their texts. The answer key is this
  walkthrough's script, not a measure of the search, and the prepared links are that script.
- The ready-made sites show the answer key's links, not the presenter's: they were prepared from the
  state the steps reach when they follow the key.
- The team's site is measured with Sphinx-Needs 9.2.0 and Sphinx 9.0.4 only, the versions
  `demos/requirements-exchange/team/requirements.txt` pins.
- The link on the team's site opens the element's file in the project open in VS Code, so it shows
  the presenter's copy, while the ready-made site shows the answer key's links. With VS Code open on
  another folder, the link goes to what is open there. In a window with no SWCraft project it opens
  nothing and shows one notification, *SWCraft: a model link was not opened — no SWCraft project is
  open in this window.* In another SWCraft project it opens that project's file of the same name, if
  the project has one — the link names a file of the model, not a project — and otherwise opens
  nothing and leaves one line in the **SWCraft** output channel. Without VS Code and SWCraft's
  extension it opens nothing at all.
- Building the team's site yourself needs Python 3.11 or later and `pip` access to PyPI; without
  them, the ready-made sites still open, and every other step runs.
