# SWCraft Vehicle Control Showcase

Standalone synthetic automotive project used to develop and demonstrate SWCraft workflows.

The repository is intentionally separate from the SWCraft product source. It is built with one
pinned SWCraft release — installed once per machine from the workstation archive, never into the
project — and is designed to run natively on both macOS and Windows without checkout-relative
imports.

## Status

The model on `main` is the **storefront**: one coherent vehicle-control story that uses every kind
and every field of the model contract of the SWCraft release it is pinned to, **SWCraft 0.24.0**
(model contract `12.7.1`). Enumeration values and rules are not coverage targets: not
every value of an enumeration is used, and a valid model breaks no rule — showing a rule is what
the rejected changes below are for.

**What the model shows.** 76 elements in the fifteen layers of contract `12.7.1`. Brake Thermal
Protection is the feature, committed, inside a three-level vehicle: `VehicleControl` holds
`Chassis`, which holds `BrakeSubsystem`, with boundary ports and delegations on the two nested
compositions; the root holds the connectors between its members. Seven components — six
application components and the platform's `NvM`, a stub for a platform file this project does not
have; the brake temperature sensor is placed twice, once inside the brake subsystem and once on
the chassis, so the 50 ms task and the two brake sequences name each occurrence by its path
(`instance:`) rather than by its type; ten interfaces — sender-receiver, a client-server
diagnostic service served through an operation event, and three platform interface stubs; nine
connectors. The data types fill the
seven data description layers: an application type with its unit, conversion and range, written
inline and by reference to a unit, a compu method and a data constraint, an enumeration, a record
and an array, the implementation types they map to — one platform implementation type,
`PlatformCounter16`, is a stub in the same way — two base types and one mapping set.
Ten requirements of the feature itself, each with a `version` and a `source`, among them an ASIL D safety goal
decomposed into two requirements written `B(D)` that name it in `derived_from`, and three design
constraints the architecture states and its own numbers meet — each core within its load budget,
the brake temperature's range and resolution, the ASIL B context both channels run in; the trace
links live in the elements that satisfy a requirement — in a component, one of its ports or one of
its runnables, and, allocating no level, in the composition holding both channels, the interfaces
carrying the temperature or the storage, the tasks and the hardware — as
`satisfies: [<id>@<version>]`; a processor with two cores and a partition on
each — `P_Brake`, ASIL B and declared `trusted`, on the core qualified to D, and `P_Vehicle`,
ASIL A with a coexistence argument for its QM member, on the core qualified to A — the 50 ms
task in `P_Brake` and two 100 ms tasks in `P_Vehicle`: `Task_100ms` running
mixed-criticality work with a coexistence argument of its own, and `Task_100ms_Low`, lower in
priority and still empty, so a runnable can move to another task without leaving its partition;
each task with an execution-time
budget and the thermal evaluation with a budget of its own, which the ARXML carries; three
sequence diagrams, the two
brake ones with a lifeline per sensor occurrence. Inside `BrakeThermalProtection` the start-up and
the 50 ms evaluation share two inter-runnable variables — `FilteredBrakeTemperature`, implicit, on
the application type, with its `init` and read-only calibration access, and `DerateStepCount`,
explicit, on `uint16` — and the evaluation runs inside the exclusive area `ThermalState`, which the
start-up may enter. `DiagnosticManager`'s `ProcessDiagnosticEvent` is also started by each arrival
of a thermal protection event, a data event beside its 100 ms poll, and keeps the last one in the
variable `LastThermalEvent`, which `ServeSnapshot` reads. The build writes ARXML that validates against the AUTOSAR 4.3.0
schema where the licensed schema is present, eleven views and the needs file
`dist/needs.json`: the architecture requirements and the elements that satisfy a requirement, each
with the path of its file, as a requirements team's Sphinx-Needs build reads them.
Exported on its own with `swcraft generate arxml --component`, each of `BrakeController`,
`BrakeTemperatureSensor`, `BrakeThermalProtection` and `VehicleStateManager` gives an XSD-valid
file, while `DiagnosticManager` and `InstrumentCluster` are refused by design: their closures reach
the platform stubs — definitions the project declares but does not own — that a file exported on
its own could not contain. `swcraft metrics --project swcraft.yaml` reports what state the
architecture is in and where it is heading — on this model one hub, `BrakeThermalProtection` — with
no overall score; it is no gate.

**What SWCraft 0.24.0 changes for the project.** Nothing in the model: contract `12.7.1` is a patch
that adds, removes and renames nothing, and the build's ARXML, needs file and component exports are
the same bytes as 0.23.0's. Two things around it change:

- **The model guard refuses a path that names the model.** A path that holds the model folder's
  name as one of its parts (`notes/model/x.md`) or ends like a model file
  (`elsewhere/interfaces/INvStorage.yaml`, while `model/interfaces/INvStorage.yaml` exists) is
  denied for the paths each client's guard judges — Copilot's reads and searches, Kiro's file
  tools — as a direct reach into `model/` already was; `tests/test_chat_scenario.py` holds both
  rules under both guards.
- **A `.env` is read from the project only**: from the folder `swcraft` runs in and each folder
  above it up to the one holding `swcraft.yaml`. The install page's `.env`, beside `swcraft.yaml`,
  is in that place.

**Calls without waiting, and copies.** Since SWCraft 0.23.0 (contract `12.7.0`) a runnable can work
on copies and call without waiting, and the model uses each form where the story needs it. `DiagnosticManager`'s
`ProcessDiagnosticEvent` starts the snapshot write to the platform's non-volatile storage
**asynchronously** (`Call_StoreSnapshot`, `asynchronous: true`, a `timeout`) and goes on; a new
runnable, `ConfirmSnapshotStored`, is started by the **call-returned** event of that write
(`ASRT_SnapshotStored`, its result at `Result_StoreSnapshot`), runs in `Task_100ms` right after it
and is a step of the `thermal_status_display` sequence. `ProcessDiagnosticEvent` also fetches the
storage's error status the other way the standard allows, an asynchronous call it **polls** itself
(`GetErrorStatus`, a second operation of `INvStorage`, its result at `Result_NvErrorStatus`).
`BrakeThermalProtection`'s 50 ms evaluation reads the brake request and the operating state
**implicitly** (`by: implicit`) — one consistent pair of inputs per run — and writes the permitted
brake action implicitly, published once at the end; the brake temperature stays `by: value`,
because its port asks for an update flag, which an implicit read cannot have. Two of the rejected
changes below show the two implicit reads the rules refuse.

The ASIL levels, the measures and the coexistence text are illustrative declarations that exercise
SWCraft's checks. They are not a safety concept. A few declarations exist to show a field rather
than to model the function — `is_service` on two interfaces between application components, for
one; `docs/briefs/FB-SHOWCASE-001-brake-thermal-protection.md` § 5 names them.

**The coverage gate.** `tests/test_model_coverage.py` reads the model contract of the **installed**
SWCraft and fails when a kind or a field of it is absent from the model, or when the model carries a
key that contract does not declare. On SWCraft 0.24.0 the model carries 67 of 67 kinds and 359 of
359 fields, with no undeclared key, and passes `swcraft check-model` with no error and **exactly 4
warnings, by design**: `HAZ_BTP_BRAKE_FADE` is a stub, the placeholder the requirements import
writes for a parent it does not have — here the hazard the safety goal derives from — and every
stub is a warning; and three are one stale case:
`REQ_BTP_TEMPERATURE_RANGE` is at version 2 while its three interfaces still name version 1, the stale case: each of those links needs confirmation, a warning of its own. `check-model --warnings-as-errors` therefore
fails on exactly that set, and the gate asserts both, so that an unexpected warning still fails it.
The model holds 11 requirements: the feature's six architecture requirements, its four external
requirements and the stub. The external requirements carry the provenance a requirements team's
delivery would: a `revision` each, the delivery that holds them as their `baseline` — `0.9`, the
requirements team's earlier delivery (below) — and the two baseline requirements their document
(`BL-SHOWCASE-001`); like the rest of the model, the values are synthetic.

**The rejected changes.** `demos/` holds nine small edits, each breaking exactly one SWCraft rule —
an incompatible connector, a component below its requirement's level, a consumer without a measure,
a partition on an unqualified core, a period that is not a multiple of its task's, a RAM budget overrun,
an unmapped enumeration, an implicit read of a queued event and an implicit read of a value whose port
asks for an update flag. `demos/README.md` says how to apply and undo each one;
`tests/test_rejected_changes.py` checks that each is refused by exactly its rule.

**The requirements exchange.** `demos/requirements-exchange.md` follows requirements from the team
that writes them into the architecture and back. A synthetic requirements team keeps its software
requirements in a Sphinx-Needs project (`demos/requirements-exchange/team/`) — brake requirements
written against this model's own element names, derived from no real project — and hands the
architect a delivery, a `needs.json`. Delivery 1.0 holds 50 requirements: the feature's four
external ones and 46 software requirements, 42 in four documents (*SRS Brake Control*, *SRS Thermal
Protection*, *SRS Diagnostics*, *SRS Driver Information*) and four with none, eight of them
distractors the architecture does not realise. The walkthrough imports it with *Model → Import
Requirements* and the team's mapping (`team.needs-mapping.yaml`), links the new requirements with
the trace link search — two by hand in Labelling, then the rest of the answer key from a prepared
proposals file (`prepared-links.json`), each written by **Apply** — and builds `dist/needs.json`,
which the team's Sphinx site shows beside its requirements, each architecture need linking to its
file in VS Code (a `vscode://` link SWCraft's extension opens); the team's site comes ready-made in
three states under `demos/requirements-exchange/sites/`. Delivery 1.1 changes one linked requirement
and drops a distractor; the link turns unconfirmed on both sides until the architect confirms it.
The warnings go 4 → 50 → 48 → 12 → 12 → 11, in VS Code and on the command line; the page says how
to start over, and `demos/requirements-exchange/answer-key.json` is the presenter's script. None of
it is committed in the model: `tests/test_requirements_exchange.py` holds the shipped state and
walks the page on the command line on a temporary copy, and holds each ready-made site's needs file
to the walk's; `scripts/generate_requirements_prepared.py` writes the prepared links and the sites.
Building the team's site yourself needs Python 3.11 or later and `pip` access to PyPI for the team's
Sphinx; the project itself still installs nothing.

**Diagrams in VS Code.** *Model → Diagrams* opens the eleven views in a tab of VS Code, where a
Ctrl+click on a drawn element opens its model file at its line and *Show in Diagram* leads back;
`demos/README.md` walks it on `ConfirmSnapshotStored` in `thermal_status_display`, and
`tests/test_diagram_navigation.py` holds the marks the tab reads on the generated pages.

**Test tables.** `swcraft generate test-tables` writes what a test team verifies — the components,
where each one runs, each runnable's task, period and budget — as CSV tables, and joins the team's
own columns to them by row. A synthetic test team's review of last week's model is committed under
`demos/test-tables/annotations/` (written by `scripts/generate_test_annotations.py` from a copy of
the model with this week's two changes undone), so the *Test Tables* tab shows every review state —
accepted, one rejected with the team's comment, not reviewed, stale and an orphaned annotation.
`demos/test-tables.md` reads it; `tests/test_test_tables.py` holds every state.

**Chat with the model, in GitHub Copilot and in Kiro.** The project carries both clients' files
as the pinned release's onboarding writes them, copied from a fresh
`swcraft init --integration moon --client copilot --client kiro` scaffold — Copilot's agent,
instructions and model guard under
`.github/`, Kiro's server settings, instructions and model guard under `.kiro/` — and
`demos/chat-with-the-model.md` runs one scenario in both: a question about how each runnable on
`INvStorage` gets its result, the impact of a change to `INvStorage`, a change proposed and rejected
in the SWCraft review tab, and each client's guard refusing a direct reach into `model/` (Copilot's
a read, Kiro's an edit). `tests/test_chat_scenario.py` holds the facts the page quotes from the
command line and both guards' decisions, and `tests/test_client_files.py` holds every client file
to a fresh scaffold of the pinned release. `WI-SHOWCASE-002`'s chat segments now point at that page.
Cross-platform verification (`WI-SHOWCASE-001` § 9) has not yet been run on a native Windows host.

## Documentation

- `docs/briefs/FB-SHOWCASE-001-brake-thermal-protection.md` — bounded feature brief and complexity
  budget for the synthetic from-scratch model.
- `docs/briefs/BL-SHOWCASE-001-synthetic-starting-model.md` — historical: the exact pre-feature model
  inventory and baseline acceptance contract of the five-component baseline the storefront replaced.
- `docs/guide/work-instructions/WI-SHOWCASE-001-cross-platform-project-setup-and-build.md` — controlled
  setup, build, and platform-verification procedure.
- `docs/guide/work-instructions/WI-SHOWCASE-002-vscode-copilot-demonstration.md` — the demonstration
  script in VS Code with Copilot and in Kiro, its chat segments pointing at the scenario pages.
- `demos/README.md` — the demonstrations' index; the diagrams in VS Code, from a drawn element to
  its model file and back; and the nine rejected changes: what each edit is, the rule it breaks,
  what the build says, and how to undo it.
- `demos/chat-with-the-model.md` — one chat scenario in GitHub Copilot and in Kiro: a question, an
  impact question, a change proposed and rejected in the review tab, and the model guard.
- `demos/test-tables.md` — the test tables in VS Code with a synthetic test team's annotations,
  every review state shown.
- `docs/guide/install-on-a-workstation.md` — the one page a colleague follows to install SWCraft and
  this demo on a Windows workstation from two zip files; `kit/README.md` and
  `scripts/build_colleague_kit.py` are how the demo's zip is produced.
- `demos/requirements-exchange.md` — the requirements exchange: a requirements team's delivery
  imported, linked with the trace link search, published as `dist/needs.json` to the team's Sphinx
  site, the next delivery's change confirmed on both sides, and how to start over.
- `demos/requirements-exchange-presentation.md` — the requirements exchange told to an audience in
  ten slides (*Enrich, never change*), the speaker notes as comments; `demos/build_public.py`
  renders it as the presenter's `demos/requirements-exchange-presentation.html` and the public
  `demos/requirements-exchange-presentation-public.md` and `.html`. The kit ships the public HTML
  only, linked from the exchange's page and the demos' index.

The open copy of this repository holds the project, its guide and its design records. The
migration evidence and the engineering plans are the maintainer's records in the work repository
and are not part of it; a record path that a design record under `docs/briefs/` cites names one of
them.

The project contains no customer data and makes no production-readiness, ASIL, AUTOSAR-toolchain,
or ISO 26262 qualification claim.

## Setup and build

**This project installs nothing.** The SWCraft toolchain is installed **once per machine** from
the workstation archive. Download `swcraft-0.24.0-<platform>.zip` (`linux-x64`, `windows-x64` or
`macos-arm64`) and its `SHA256SUMS-<platform>` from the Releases page of SWCraft's repository,
<https://github.com/swcraft-dev/swcraft/releases/tag/v0.24.0>, check the zip's SHA-256 against its
line in that file (`WI-SHOWCASE-001` § 8.3 has the commands), and unpack it. On macOS, clear the
quarantine flag on the unpacked folder once before the installer, since the archive is not signed:

```text
xattr -dr com.apple.quarantine <unpacked folder>
```

Then run the one installer file inside it (`swcraft_install.cmd` on Windows,
`./swcraft_install.sh` elsewhere) and put the installation's `current/bin` on `PATH` (the
installer edits the user `PATH` on Windows and prints the one `export PATH=` line for a shell
profile on macOS and Linux).
Since 0.11.0 that archive carries everything the installation runs on — the Python it is built
on, the Node.js the diagram layout runs on, and the two companion VS Code extensions — so a
workstation needs no Python, no Node.js and no access to the VS Code Marketplace.
`toolchain_version` in `swcraft.yaml` names the release this project is built with, and every
`swcraft` command checks that pin before it does anything else. moon is the other per-machine
tool; `.prototools` pins its version for `proto use`. There is no `.venv`, no bootstrap and no
requirements file of the project's own (`demos/requirements-exchange/team/requirements.txt` is the
requirements team's, for its Sphinx site) — a leftover `.venv` activated in a terminal shadows the installation, so delete
one if you find it.

The build is the committed graph:

```text
moon run :build
```

### Checking a machine before a build

The project carries no preflight script and needs no Python on the machine. Three commands say
whether a workstation is ready, on every platform:

```text
swcraft --version
moon --version
moon run :build
```

`swcraft --version` must answer the release `toolchain_version` pins in `swcraft.yaml` — every
`swcraft` command checks that pin itself; on a mismatch the commands that write or gate refuse in
one sentence naming both versions, and the six read-only ones print it and answer anyway — and `moon --version` the one `.prototools` pins. In VS Code, **Check Editor Tooling** in the `…`
menu at the top of the SWCraft view reports the installation, its version and the editor side in one place.

For a presentation, confirm the validation mode. The build's gate, `validate-arxml`, is never served
from moon's cache (since 0.20.0 the build graph sets `cache: false` on it), so every build prints
it; the gate alone is:

```text
swcraft validate --project swcraft.yaml
```

The run must print `ARXML validated against …`; `Note: XSD validation is skipped (…)` means the
licensed schema was not found and the check was structural.

### The maintainer's tooling

`scripts/build_colleague_kit.py` and `tests/` are Python, and they are the maintainer's: they
build and pin the colleague kit and the two workflows (the work repository's
`verify.yml` and `.github/workflows/release.yml`) and check the model, on the CI
runner or a maintainer's machine, with any Python 3.11 or newer. Nothing a user of the project
runs to build it is Python. The one Python member of the kit is the requirements team's
`demos/requirements-exchange/team/conf.py`, which only the team's own Sphinx reads, in step 4 of the
requirements exchange.

Run the tests with a Python of the machine named by its path (`/usr/bin/python3.12`, `py -3.12`),
not with the `python3` the setup above puts on `PATH`: that one is the SWCraft installation's own
interpreter, and the tests should check the installation from outside it, importing nothing of
SWCraft's own. Below, `python3` stands for that system Python.

```text
python3 -m unittest discover -s tests -v
```

Several of the tests run the installed SWCraft: `tests/test_model_coverage.py`, the coverage gate,
`tests/test_rejected_changes.py`, which applies each rejected change to a temporary copy of the
model, `tests/test_requirements_exchange.py`, which walks the requirements exchange on one,
`tests/test_requirements_deliveries.py`, which imports the team's two deliveries into one, and the
tests of the demonstration pages — `tests/test_test_tables.py`, `tests/test_chat_scenario.py`,
`tests/test_diagram_navigation.py` and `tests/test_client_files.py`. They find `swcraft` on `PATH`;
the coverage gate runs the probe `tests/model_coverage_probe.py` under the installation's own
Python. Without SWCraft on `PATH`, or with a release other than the one
`swcraft.yaml` pins, they **skip** and say why; with `SHOWCASE_REQUIRE_SWCRAFT=1` in the environment
either case is a **failure** instead — set it on a maintainer's machine, where a skip would hide the
model's check:

```text
SHOWCASE_REQUIRE_SWCRAFT=1 python3 -m unittest discover -s tests -v
```

`tests/test_user_facing_wording.py` keeps roadmap references out of the files a user opens.
`tests/test_open_copy.py` holds `public-paths.txt` to a partition of the tracked files into open
and closed paths, the legal files to their texts, and the open files to a scan for private
addresses, home paths, e-mail addresses, dead relative links and, in the README and
`docs/guide/`, closed paths.
`scripts/generate_requirements_deliveries.py` writes the requirements team's two sources from one
table; `tests/test_requirements_deliveries.py` holds the committed sources to it (`--check`), the
two deliveries and the answer key to that table, and the team's `conf.py` to the showcase's address
and the handover path.

Three more scripts write committed files. The first two take `--check`, which writes nothing and
exits 1 when a committed file differs from what the script would write:

- `scripts/generate_requirements_prepared.py` writes the requirements exchange's prepared links and
  the three needs files, and with `--sphinx-build <venv>/bin/sphinx-build` the team's four sites (the
  three states and delivery 1.0 before the handover, `sites/1.0-original/`). It
  needs the pinned SWCraft on `PATH` and, for the sites, the team's Sphinx: a virtual environment
  made from `demos/requirements-exchange/team/requirements.txt`. Without `--sphinx-build` it refuses
  to change a needs file, since the site built from it would go stale; `--check` compares the sites
  with Sphinx-Needs' random container ids (`SNCB-…`) masked. `tests/test_requirements_exchange.py`
  runs its `--check` without Sphinx, and `tests/test_requirements_sites.py` holds each committed site
  to its needs file.
- `scripts/generate_test_annotations.py` writes the test team's folder
  `demos/test-tables/annotations/` from last week's model; it needs the pinned SWCraft. Run it again
  when the model changes and `tests/test_test_tables.py` fails, which runs its `--check`.
- `demos/build_public.py` renders the presentation's presenter and public copies; it needs `marp`
  on `PATH` and has no `--check`. Run it after every edit to the deck;
  `tests/test_requirements_presentation.py` holds the public copies to the source.

The two SWCraft generators share `scripts/pinned_swcraft.py`, which refuses a `swcraft` other than
the release `swcraft.yaml` pins before any work starts.

## Releasing the demo

A release of the demo is one file: the colleague kit
`vehicle-control-showcase-kit-<swcraft version>.zip`, with a `SHA256SUMS` beside it.
`docs/guide/install-on-a-workstation.md` is the page a colleague follows; it is also what the kit
carries as its own `README.md`.

**Accepting a migration to a new SWCraft release.** A routine migration is accepted on the tests
(`SHOWCASE_REQUIRE_SWCRAFT=1`, none skipped) and the maintainer's evidence record of it. The
maintainer walks the showcase by hand in VS Code, on the colleague kit unpacked into a new, empty
folder, only when a release changes a demonstration scenario or its steps in the panel (the
maintainer's rule of 2026-11-08).

**The gate, which publishes nothing.** The showcase is developed in the maintainer's work
repository, whose workflow `verify.yml` runs on a Linux runner on every push to `main`, on every
`v*` tag and on demand. It runs this repository's unit tests and builds the kit at the SWCraft
release `swcraft.yaml` pins -- read from the manifest with the repository's own parser, never
written into the workflow -- with `--tagged` on a tag only, and prints the kit's `SHA256SUMS`. It
then does both again in a tree made of the open paths alone (`public-paths.txt`), so a test or a
build step that needs a file the open copy does not carry fails there first. It uploads nothing
and reads no secret. `tests/test_verify_workflow.py` holds it, and skips where the workflow is not
present, as in the open copy.

**The open copy, one commit per release.** The open copy is published from the work repository by
the maintainer's publish step: it assembles the paths `public-paths.txt` lists into one commit,
checks it, and publishes it only on a green run of `verify.yml` on the commit it publishes.

**The GitHub release.** In the open copy, a pushed `v*` tag runs `.github/workflows/release.yml`
on GitHub: the unit tests, the kit built with `--tagged` at the pinned release, and the zip and
its `SHA256SUMS` attached to the tag's GitHub Release, whose text names the tag, the SWCraft
release and the sums line. The tag push creates the release final. A run dispatched on a tag is
the re-run: with `draft` (the default) it creates a draft when there is no release yet, uploads
into an existing draft again, and refuses a release that is already published, naming the tag;
without `draft` it does what the tag push does, re-uploading into the existing release and making
it final. Runs on the same tag wait for one another. Every action is pinned by its commit, and
the run holds no secret beyond its own token. `tests/test_release_workflow.py` holds the workflow. The
install page links both Releases pages.

The tag names the *showcase* release; the kit's filename names the *SWCraft* release it is pinned
to. They coincide when the showcase is tagged at a migration, and nothing requires them to.

What neither workflow does: build the model. There is no SWCraft toolchain on their runners --
this project installs nothing and the toolchain is one installation per machine -- so
`moon run :build` and `swcraft validate` do not run there, the coverage gate and the
rejected-change test skip, and a model defect is not caught by a tag. A release's model is
exercised on a workstation, and the record is the maintainer's evidence record of the migration.

## Licence

The showcase is licensed under the Apache License, Version 2.0: the text is in `LICENSE`, and
`NOTICE` carries the copyright line that goes with it. The requirements exchange's ready-made sites
and its presentation carry third-party code (Sphinx and its theme and extensions, jQuery, Marp),
which stays under its own licences; `THIRD-PARTY-NOTICES.md` names each, where it sits, and its
licence text. The colleague kit carries all three files. The name "SWCraft" is not licensed (the
Apache License's section 6).
