# WI-SHOWCASE-001 — Cross-Platform Project Setup and Build

| Field | Value |
|---|---|
| Document ID | WI-SHOWCASE-001 |
| Revision | 0.31 |
| Status | Draft — not released for production use |
| Owner | Vehicle Control Showcase project lead |
| Applies to | This repository |
| Target platforms | macOS and native Windows |
| Effective date | Not yet approved |

## 1. Purpose

This work instruction defines how to prepare, build, verify, and record evidence for the
**Vehicle Control Showcase — Brake Thermal Protection** project on macOS and Windows.

Its purpose is to guarantee that both platforms use the same committed architecture model and
the same pinned SWCraft behavior. It does not qualify SWCraft, establish an ASIL capability, or
replace validation in a real downstream AUTOSAR toolchain.

## 2. Scope

This instruction covers:

- cloning and checking out the project;
- installing the SWCraft toolchain once per machine from the workstation archive, at the release
  this project pins;
- running the canonical model build;
- handling generated outputs and licensed XSD files;
- collecting macOS/Windows equivalence evidence;
- responding to setup and build failures.

It does not cover creation of SWCraft release artifacts, live AI credentials, presentation
operation, or a real corporate pilot. Those subjects require separate work instructions.

## 3. Cross-Platform Decision

The repository shall remain one project, not a macOS variant and a Windows variant.

The following files and behaviors are shared:

- architecture YAML and `swcraft.yaml`;
- requirements, scenarios, and expected semantic results;
- Moon build graph and toolchain version pins;
- deterministic SWCraft commands;
- generated ARXML, diagrams, the needs file `dist/needs.json`, and report semantics;
- acceptance criteria and evidence format.

Only machine-local concerns may differ:

- the platform's workstation archive (`swcraft-<version>-<platform>.zip`) and where its installer
  puts the installation (`%LOCALAPPDATA%\SWCraft` on Windows, `~/.swcraft` elsewhere);
- filesystem paths to licensed AUTOSAR XSDs;
- optional thin `.ps1` or `.sh` launchers;
- credentials and network configuration.

WSL may be useful for diagnosis, but it does not count as native-Windows acceptance evidence.

## 4. Mandatory Engineering Rules

1. Never import or execute SWCraft through a relative path into an SWCraft source checkout.
2. Install only the SWCraft release `toolchain_version` in `swcraft.yaml` pins, from that
   release's workstation archive. Every `swcraft` command checks the pin; a mismatch is not worked
   around by editing it.
3. One archive per platform. A macOS archive shall not be installed on Windows or vice versa; the
   installer refuses a foreign archive by its platform stamp.
4. Reach the toolchain as the bare `swcraft` on `PATH`, from the one installation per machine.
   The project carries no `.venv` and installs nothing; a leftover `.venv` activated in a terminal
   shadows the installation and shall be deleted, not worked around.
5. Keep one committed Moon build graph. Do not maintain platform-specific copies of
   `moon.yml`.
6. Use Moon for shared automation. The project carries no script a user runs: no Python entry
   point and no shell launcher. The maintainer's kit builder under `scripts/` and its tests are
   the one Python in the repository, and they run on the CI runner, never on a user's path.
7. Use `pathlib` or equivalent platform-aware path handling in that Python. Do not encode `/` or
   `\\` as business logic.
8. Do not introduce case-only filename differences, Windows-reserved names, symlink
   dependencies, or filenames invalid on Windows.
9. Commit source inputs only. Generated `dist/`, `views/`, virtual environments, local evidence,
   secrets, and licensed XSD files remain untracked.
10. A passing macOS run does not close a Windows gate, and a passing Windows run does not close a
    macOS gate.

## 5. Roles

| Role | Responsibility |
|---|---|
| Project lead | Approves this WI, toolchain pins, and release evidence |
| Developer | Follows the procedure and records deviations without local hidden fixes |
| Reviewer | Reviews model changes, semantic diff, and evidence independently of the author |
| Presenter | Uses only a tagged baseline that has passed the presentation gate |

One person may perform several roles during early development, but author and approving reviewer
shall be recorded separately before a showcase release is presented externally.

## 6. Preconditions

The operator shall have:

- Git, and network access to GitHub, where the open copy is published (§ 8.1);
- the SWCraft workstation archive for the current operating system, at the release
  `toolchain_version` pins, installed once on the machine (§ 8.3);
- VS Code at the version the archive's installer requires, and Kiro only where its chat is used
  (§ 8.3);
- Moon and proto versions pinned by the scaffold;
- sufficient access to a local working directory;
- the licensed AUTOSAR XSD only when full XSD validation is required.

The committed `swcraft.yaml` (`toolchain_version`) and `.prototools` (moon), not this prose, are
authoritative. The project pins no Python: since 0.11.0 the archive *carries* the interpreter the
installation is built on, so the machine needs none of its own — and none for Node.js or the VS
Code Marketplace either, both of which the archive also carries. Until revision 0.10 the
preflight launchers were the one exception; they are retired, and nothing a user runs in this
project needs a Python.

## 7. One-Time Project Scaffolding

This section is performed once by the project lead from an installed, versioned SWCraft artifact.
It is not repeated by every developer.

From the repository root:

```text
swcraft init . --name vehicle-control-showcase --integration moon --client copilot --client kiro
```

Since SWCraft 0.23.0 the scaffold writes the files of the chat clients it is given with `--client`,
and only theirs; without the option it writes Copilot's alone. This project is set up for GitHub
Copilot (`.github/`) and Kiro (`.kiro/`). A client file a later release changes is taken from a
fresh scaffold of that release made with the same options, never edited by hand; a client the
project does not use has no file in it, so the Codex guard `.codex/hooks.json`, which the
template carried from 0.20.0 to 0.22.0 whatever the client, is deleted.

The lead shall review every created file, confirm that no existing file was skipped in a way that
mixes integration profiles, and commit the scaffold as a distinct baseline change.

Do not copy template files from a neighboring SWCraft checkout. The purpose of this step is to
prove the same installed-artifact onboarding path expected of an external project.

## 8. Developer Setup Procedure

### 8.1 Clone and identify the baseline

macOS or PowerShell:

```text
git clone https://github.com/swcraft-dev/swcraft-vehicle-control-showcase.git
cd swcraft-vehicle-control-showcase
git status --short --branch
git rev-parse HEAD
```

The address is the open copy's: it is published on GitHub with each showcase release, and until the
first one is published it does not resolve. The maintainer's work repository is a separate one and
is not cloned here.

Expected result:

- the requested branch or tag is checked out;
- the worktree is clean;
- the commit identifier is recorded for any formal rehearsal or evidence run.

### 8.2 Preflight

The project carries no preflight script. The toolchain is already on the machine (§ 8.3), and
three commands say whether the workstation is ready, identically on both platforms:

```text
swcraft --version
moon --version
moon run :build
```

Expected result:

- `swcraft --version` reports exactly the release `toolchain_version` pins in `swcraft.yaml`.
  Every `swcraft` command checks that pin itself before it does anything else; on a mismatch the
  commands that write or gate refuse in one sentence naming both versions, and the six read-only
  ones print it and answer anyway; the remedy is that release's archive (§ 8.3),
  never an edit of the pin;
- `moon --version` reports the version `.prototools` pins;
- the canonical build exits with status 0 (§ 8.4).

For a presentation preflight, identify the effective validation mode with the gate itself. Since
0.20.0 the build graph never serves `validate-arxml` from moon's cache (`cache: false`), so every
build prints the mode; the gate alone is:

```text
swcraft validate --project swcraft.yaml
```

`ARXML validated against …` is XSD mode; `Note: XSD validation is skipped (…)` is structural mode,
which is acceptable for ordinary early development and is a failed preflight when XSD mode is
required (§ 8.5). In VS Code, **Check Editor Tooling** in the `…` menu at the top of the SWCraft
view reports the installation, its version and the editor side.

Until revision 0.10 this section was an automated entry point — `setup-showcase` and
`setup-showcase.ps1` over a stdlib Python script that performed the checks above and wrote
`.evidence-local/setup-summary.json`. It was retired because it was the last thing in the project
that asked a workstation for a Python, which the toolchain itself has not needed since 0.11.0. The
hashes and versions a formal record needs (§ 12) are now taken by hand. As of revision 0.11 the
macOS path had been exercised at **0.14.0** in XSD mode — the CLI and the seven moon tasks on the
bare `swcraft`, from the workstation installation rather than a checkout (§ 12); the three commands
above are those same commands without the wrapper.

### 8.3 Installing the toolchain, and recovering an installation

Performed once per machine, not per project or per clone. Download the workstation archive for this
operating system at the release `toolchain_version` pins, with its `SHA256SUMS-<platform>`, from
the Releases page of `https://github.com/swcraft-dev/swcraft`. Compute the archive's SHA-256 —
`shasum -a 256 <zip>` on macOS, `sha256sum <zip>` on Linux, `Get-FileHash <zip>` in Windows
PowerShell — compare it with the archive's line in `SHA256SUMS-<platform>`, and record it; on a
mismatch stop and download again. A match proves the file arrived whole, not who made it: nothing is
signed. Unpack it and run the one installer file inside it. The macOS archive is not signed, so on
macOS the quarantine flag is cleared on the unpacked folder first; an installer started on a folder
that still carries it installs nothing and names this command:

macOS:

```text
xattr -dr com.apple.quarantine <unpacked folder>
./swcraft_install.sh
```

Windows PowerShell:

```text
.\swcraft_install.cmd
```

Then put the installation on `PATH`: on Windows the installer has edited the user `PATH`, so open
a **new** terminal; on macOS it printed one `export PATH=…/current/bin:$PATH` line and edited no
file, so add that line to the shell profile first. Confirm with `swcraft --version`. Quit VS Code
and start it again, so that its chats and the model-guard hooks find the new `swcraft`; an older
one on their path makes the guards block the assistant's file tools.

The installer hands SWCraft's extension to VS Code only. On a machine that also runs **Kiro**,
install the extension into Kiro by hand, once per release: Kiro's Extensions view → `…` →
*Install from VSIX…* → `swcraft-vscode-<version>.vsix` from the unpacked archive. Then open the
project in Kiro, choose **Trust**, and run **Developer: Reload Window** once: until that reload
Kiro reads none of the project's `.kiro/` files.

Expected result:

- `swcraft --version` reports the pinned release in a new terminal;
- no `.venv` exists in the project (delete one left by an earlier release — activated, it shadows
  the installation for everything typed in that terminal, which the editor's health check cannot
  see);
- no SWCraft source-checkout path appears on `PATH`.

Repair is the same archive's installer again; updating is the next archive's; rollback is the
previous archive's. There is no per-project step in any of the three beyond raising or keeping
`toolchain_version`.

### 8.4 Run the canonical build manually

On both platforms:

```text
moon run :build
```

Expected result:

- model consistency checks pass before generation;
- ARXML, diagrams, and the needs file are regenerated from a clean output state;
- ARXML validation reports whether it used structural or XSD mode;
- the command exits with status 0;
- a failed build leaves no stale generated artifact that could be mistaken for current output.

### 8.5 Enable full XSD validation when required

Set `SWCRAFT_AUTOSAR_XSD_PATH` to the approved local schema entry point using the operating
system's normal environment mechanism, then rerun the canonical build.

The schema identity, source, and applicable AUTOSAR version shall be recorded in evidence. The
schema itself shall not be committed. A presentation configured to require XSD validation shall
fail preflight if only structural validation is available.

### 8.6 Finish a development change

Before requesting review:

1. run the canonical build from a clean output state;
2. inspect the semantic change and generated reports;
3. confirm `git status --short` contains only intended source/documentation changes;
4. confirm no secret, licensed file, generated artifact, virtual environment, or local evidence is
   staged;
5. record the platform used for the run.

## 9. Platform Equivalence Gate

A candidate showcase baseline is cross-platform only after the same commit passes on both native
platforms.

| Check | macOS | Native Windows | Required evidence |
|---|---:|---:|---|
| Toolchain installed from the platform archive at the pinned release | Required | Required | Archive filename and SHA-256, `swcraft --version`, exit status |
| `moon run :build` | Required | Required | Concise log and exit status |
| Model checks | Required | Required | Finding count and verdict |
| ARXML generation | Required | Required | SHA-256 and semantic/XSD verdict |
| Diagram generation | Required | Required | SHA-256 of `views/index.html` or documented rendering delta |
| Needs file generation (`dist/needs.json`) | Required | Required | SHA-256 |
| Failure removes stale outputs | Required | Required | Negative-test result |
| Component export scenario | Required before demo release | Required before demo release | Closure summary and hash |

Byte-identical hashes are expected for deterministic text artifacts. If an artifact differs, the
reviewer shall classify the difference as an approved presentation-only rendering difference or
as a defect. Newline or path-separator drift is a defect, not an accepted operating-system delta.

Store formal evidence outside the repository until the evidence-package structure is approved.
Commit only sanitized summaries explicitly required by this instruction.

### 9.1 Current evidence status

The runs below are recorded in the maintainer's evidence records, one per run, which are kept in
the work repository and are not part of the open copy; this section names each by what it
recorded. The first macOS installed-artifact run is the evidence record of 2026-08-15, and the
subsequent clean-clone automated run is the second record of that day.

It establishes that the scaffold, offline bootstrap, clean install, and empty AUTOSAR 4.3.0
structural build worked on the recorded macOS ARM64/Python 3.11 configuration. Both records predate
0.7.0: the bootstrap and wheelhouse they describe are retired, and § 8.3 is what replaces
them. The 0.7.0 migration itself was exercised on macOS (revision 0.5) and is recorded in
the migration's evidence record: `moon run :build` with the bare `swcraft`, seven
tasks, XSD mode, the colleague kit rebuilt byte-identical, and the ARXML byte-identical under 0.6.0
and 0.7.0 on this model. The 0.8.0 migration's record (revision 0.6) adds what its predecessor
left open on this host — the toolchain installed by the workstation archive's own installer, from
`~/.swcraft/current/bin` and not from a source checkout — and repeats the byte-identity
measurement across 0.7.0 and 0.8.0. The 0.9.0 migration's record (revision 0.7) holds the root
composition written by hand, the ARXML that moves for the first time and by exactly what the
release note says. The 0.11.0 migration's record (revision 0.8) holds the two primitives split as
the release note's recipe prescribes, the ARXML that moves and by exactly what, `moon run :build`
green on all seven tasks in XSD mode, and the first install from an archive that carries its own
Python, Node.js and LikeC4. The 0.12.0 migration's record (revision 0.9) holds the diagrams drawn
by SWCraft into plain files, the `c4:` output and the empty `systems/` layer removed, the ARXML
byte-identical, and the same seven tasks green. The 0.13.0 migration's record (revision 0.11)
holds the empty `mapping_sets/` layer added, the ARXML and the RST byte-identical to 0.12.0, a
fifth view (`deployment`) drawn, and the same seven tasks green. The 0.14.0 migration's record
(revision 0.12) holds the data types moved into their seven layers, the interface elements naming
their side, every component declaring how it may be stopped, the ARXML moved by exactly those five
declarations, the RST and every view byte-identical, and the same seven tasks green. The
storefront that replaced the baseline (revision 0.14) has its own record, on macOS only: the seven
tasks green in XSD mode with eleven views, and the component export exercised for this model —
four components exported XSD-valid, and `DiagnosticManager` and `InstrumentCluster` refused by
design because their closures reach the platform stubs, which is the expected outcome for this
model. None of the records
closes:

- native-Windows execution;
- 4.3.0 XSD validation;
- cross-platform byte equivalence;
- the negative stale-output test;
- component export;
- downstream AUTOSAR-tool acceptance;
- SWCraft tool qualification.

## 10. Windows Status

### 10.1 The build finding — closed 2026-08-25

The finding this section carried from 2026-08-14 is resolved. Moon 2.3.5 defaults its `shell` task
option to **true on Windows and false on other platforms**, and on Windows alone it handed the
POSIX-spelled command to PowerShell, which parsed it as an expression and failed before Python
started.

The resolution was made in the SWCraft project template and its tests, not as a private patch here,
as this section required: all six command tasks declare `options: shell: false` and spell the
interpreter `./.venv/bin/python`. Both halves were measured on the failing host — the quoting is
what breaks the parse, and without a shell the bare `.venv/bin/python` does not resolve on Windows
while the `./` form does, which is also the ordinary POSIX spelling. One build graph, both
platforms, no per-OS fork. Shipped in `0.4.1`.

**Verified on a native Windows host on 2026-08-25:** `moon run :build` completed all seven tasks,
exit 0, ARXML at AUTOSAR 4.3.0, structural validation. The same session exercised the VS Code and
Copilot path of WI-SHOWCASE-002 §§ 6–7 end to end, which found and closed a second defect
(`model_diff` hung under the MCP server; its git subprocesses inherited the server's JSON-RPC
stdin). Record: the maintainer's evidence record of that Windows run.

### 10.2 What is still open

Native Windows remains an open release gate — for different reasons than the one above:

- **Section 9 has not been executed.** No artifact hashes have been compared between platforms. The
  macOS evidence on file predates this work, at an older commit and an empty model, so the gate
  needs a fresh macOS run of the *same* commit before any comparison means anything.
- **XSD validation is untested on Windows.** Every run there has been structural; no licensed
  schema is on that host.
- **`setup-showcase.ps1` was never verified, and is retired.** The 2026-08-25 session reached its
  environment by other means; revision 0.10 removed the launcher with the Python preflight, so
  this item closes without a measurement.
- **The bare `swcraft` under moon is unmeasured on Windows.** Since 0.7.0 every task runs
  `command: 'swcraft'` with `options.shell: false`; whether moon resolves a bare name from `PATH`
  without a shell there is the observation the SWCraft release notes record as owed on Windows. The
  2026-08-25 verification was of the path-spelled `./.venv/bin/python` command, which no longer
  exists.
- **A failing build reports no reason on Windows.** Moon does not forward a failed task's stderr
  there. The validator's message is present when the CLI is run directly, so this is a defect in
  the runner integration and not in the model gate — but until it is fixed, the negative case
  shall not be demonstrated, and a Windows operator hitting an inconsistent model gets an exit
  code and nothing else. Tracked in the SWCraft repository.
- **Sections 3.1 and 3.2 of the showcase's evidence expectations are unaffected**: no one shall
  claim cross-platform verification until Section 9 passes on a real Windows host.

## 11. Failure and Deviation Handling

When a step fails:

1. stop and preserve the command, exit status, relevant tool versions, and first complete error;
2. confirm the checked-out commit and worktree state;
3. determine whether the failure is project data, SWCraft, platform integration, licensed XSD,
   or local environment;
4. open a tracked issue in the owning repository;
5. do not bypass validation, loosen acceptance criteria, or commit a machine-specific build graph;
6. rerun the complete affected gate after the approved fix.

Any temporary diagnostic command shall be identified as diagnostic and removed before release.

## 12. Records

For each formal rehearsal or platform gate, record:

- showcase commit and branch/tag;
- SWCraft artifact version and hashes;
- operating system, architecture, Moon, and proto versions;
- workstation archive identity (filename and SHA-256);
- validation mode and XSD identity when applicable;
- command results and artifact hashes;
- deviations, issue links, reviewer, and disposition.

## 13. Revision History

| Revision | Date | Description | Author/approver |
|---|---|---|---|
| 0.1 | 2026-08-14 | Initial cross-platform setup and build WI | Draft / not approved |
| 0.2 | 2026-08-15 | Recorded first macOS installed-artifact scaffold/build and remaining gates | Draft / not approved |
| 0.3 | 2026-08-15 | Added one-command setup/preflight; macOS exercised, Windows pending | Draft / not approved |
| 0.4 | 2026-08-25 | Section 10 rewritten: the PowerShell build finding is closed and verified on a native Windows host; what remains open is restated and separated from it | Draft / not approved |
| 0.5 | 2026-09-05 | Migrated to SWCraft 0.7.0: the toolchain is one installation per machine from the workstation archive, the project pins it in `swcraft.yaml` and installs nothing; bootstrap, wheelhouse and `.venv` retired from §§ 2–4, 6, 8, 9, 12; § 8.3 is now the archive install; § 10.2 gains the unmeasured bare-`swcraft` case on Windows | Draft / not approved |
| 0.6 | 2026-09-06 | Migrated to SWCraft 0.8.0: the pin, § 8.2's exercised release and § 12's evidence pointer. § 8.3's install procedure is exercised for the first time on macOS — the archive's own installer, `~/.swcraft/current/bin` on `PATH` — which revision 0.5 left open. Nothing in the procedure itself changed: 0.8.0 adds ARXML the model does not declare, and the generated document is byte-identical to 0.7.0's | Draft / not approved |
| 0.7 | 2026-09-07 | Migrated to SWCraft 0.9.0 (contract major `4.3.0`): the pin, one hand-written root composition `model/compositions/VehicleControl.yaml`, `model/containers/` deleted, § 8.2's exercised release and § 12's evidence pointer. The procedure itself is unchanged; the generated ARXML is **not** byte-identical to 0.8.0's for the first time — the invented `SwCraftComposition` is replaced by the declared root — and § 12's record says by what. The archive install and the moon graph at 0.9.0 wait for the tag's archive | Draft / not approved |
| 0.9 | 2026-09-17 | Migrated to SWCraft 0.12.0 (contract major `6.0.0`): the pin; the `c4:` output line and the empty `model/systems/` layer removed; `moon.yml`'s `generate-c4` task is `generate-diagrams` with `views/` as its output, the graph's edges unchanged. The generated ARXML does not move. § 6 names two companion extensions rather than three, § 10's diagram row hashes `views/index.html`, § 12 carries the macOS measurement at 0.12.0 | Draft / not approved |
| 0.8 | 2026-09-15 | Migrated to SWCraft 0.11.0 (contract major `5.0.0`): the pin, and the two `kind: primitive` data types split into a `value_type` each over a new `base_type`, following the release note's recipe — `uint8`/`uint16` keep their names, so no interface changed. § 6's preconditions drop the machine's own Python, Node.js and Marketplace access, which the archive now carries; § 8.2 and § 12 carry the macOS measurement at 0.11.0. The generated ARXML moves: the invented `uint8_impl`/`uint16_impl` twins are gone and every data element points at the value type | Draft / not approved |
| 0.15 | 2026-10-10 | Migrated to SWCraft 0.15.0 (contract `9.2.0`, a major over 0.14.0's `8.0.0`): the pin; two partitions written into `model/hardware/` (`P_Vehicle` on `Core0`, `P_Brake` on `Core1`) and both tasks' `core:` replaced by `partition:` — the release note's recipe, done on this project; beyond the recipe, the brake temperature sensor placed a second time on the chassis (`RearBrakeSensor`, feeding the brake controller over a ninth connector) so that the 50 ms task and the two brake sequences name an occurrence by `instance:`, and the two decomposed requirements written `B(D)`. The generated ARXML moves by the controller's new port and the connector; the deployment view draws the partitions; the retired `safety.task-on-unqualified-core` demo is replaced by `safety.partition-on-unqualified-core`. Evidence: the migration's evidence record. | Draft / not approved |
| 0.16 | 2026-10-13 | Migrated to SWCraft 0.16.0 (contract `10.1.0`, a major over 0.15.0's `9.2.0`): the pin; both tasks' `wcet_us: N` written `wcet: Nus` — the release note's recipe; beyond the recipe, `EvaluateThermalProtection` declares `wcet: 3500us` with `wcet_type: gross`, so the model keeps carrying every field, and the generated ARXML gains exactly that component's `SWC-TIMING`. The RST and the eleven views are byte-identical. The Copilot files follow the release's template and the project gains the model-guard hook `.github/hooks/swcraft.json`; `experiments/rebalance.yaml` asks the allocation experiment its question. Evidence: the migration's evidence record. | Draft / not approved |
| 0.17 | 2026-10-14 | Migrated to SWCraft 0.16.1, a patch over 0.16.0 (contract `10.1.0` unchanged): the pin alone — the release note's recipe. The model's format, the Copilot files and the hook are the same as 0.16.0's. The generated ARXML, RST and eleven views are byte-identical to what 0.16.0 generates from the same model. Evidence: the migration's evidence record. | Draft / not approved |
| 0.18 | 2026-10-15 | Migrated to SWCraft 0.16.2, a patch over 0.16.1 (contract `10.1.1`, a prose change to one field's description): the pin alone — the release note's recipe. The model's format, the Copilot files and the hook are the same as 0.16.1's. The generated ARXML and RST are byte-identical to what 0.16.1 generates from the same model; the views are redrawn by the release (hit areas on every port, the lit colour blue, the `NvM` stub's port a bare square and its connector dashed as not judged). Evidence: the migration's evidence record. | Draft / not approved |
| 0.19 | 2026-10-19 | Migrated to SWCraft 0.17.0 (contract `11.1.0`, a major over 0.16.2's `10.1.1`): the pin; `outputs.rst` now names the export folder `dist/needs` (the release refuses a `.rst` file there) and `moon.yml`'s `generate-rst` declares its four files; every requirement's `links` moved into the elements as `satisfies: [<id>@1]` entries — on the components, three ports and two runnables, so each component keeps the requirements and the level it had — and its `status` deleted; `version: 1` and a `source` written on every requirement — the release note's recipe, done on this project. Beyond the recipe, the two decomposed requirements name the safety goal in `derived_from`, `Chassis` satisfies the goal, and three design constraints (`source: architecture`: each core within its load budget, the brake temperature's range and resolution, the ASIL B context of both channels) are added and satisfied by the processor, the cores, the partition, the memory, the tasks and the interfaces whose own values meet them — and, so that every field of contract `11.1.0` is shown, a synthetic `revision` on the external requirements, `document` and `baseline` on the two baseline ones, and one stub, `HAZ_BTP_BRAKE_FADE`, the safety goal's hazard — 75 elements. `check-model` prints exactly one warning, the stub's, by design, and fails under `--warnings-as-errors` on it. The generated ARXML and the eleven views are byte-identical to what 0.16.2 generates from the previous model; the RST is the Sphinx-Needs export under `dist/needs/`. The Copilot files follow the release's template. Evidence: the migration's two evidence records. | Draft / not approved |
| 0.20 | 2026-10-19 | Migrated to SWCraft 0.17.1, a patch over 0.17.0 (contract `11.1.0` unchanged): the pin alone — the release note's recipe. The model's format, the Copilot files and the hook are the same as 0.17.0's. The generated ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to what 0.17.0 generates from the same model. Evidence: the migration's evidence record. | Draft / not approved |
| 0.21 | 2026-10-21 | Migrated to SWCraft 0.18.0 (contract `12.0.0`, a major over 0.17.1's `11.1.0`: the rule that a component must satisfy a requirement is retired; no model file needed an edit): the pin, and the Copilot agent profile and instructions from the release's template, which now describe the requirement's direction only; the hook is unchanged. Beyond the recipe, the trace link demonstration: 46 synthetic requirements imported with `swcraft import requirements` from `demos/trace-links/requirements.json`, 15 links made with `swcraft experiment trace --apply` and recorded in `trace-decisions.yaml`, `experiments/trace.yaml` and the editor setting that names it, and the walkthrough `demos/trace-links.md` — 121 elements. `check-model` prints exactly 32 warnings by design, the stub's and one per requirement the demonstration leaves unlinked, and fails under `--warnings-as-errors` on that set. The generated ARXML and the component exports are byte-identical to what 0.17.1 generates; the Sphinx-Needs export carries the 46 requirements and their links. Evidence: the migration's evidence record. | Draft / not approved |
| 0.22 | 2026-10-21 | Migrated to SWCraft 0.18.1, a patch over 0.18.0 (contract `12.0.0` unchanged): the pin alone — the release note's recipe. The model's format, the Copilot files and the hook are the same as 0.18.0's. `check-model` still prints the 32 warnings by design. The generated ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to what 0.18.0 generates from the same model. Evidence: the migration's evidence record. | Draft / not approved |
| 0.23 | 2026-10-23 | Migrated to SWCraft 0.19.0 (contract `12.0.0` unchanged): the pin, and the Copilot agent profile and instructions from the release's template, which carry the model's schema and the new question forms; the hook is unchanged. `check-model` still prints the 35 warnings by design. The generated ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to what 0.18.1 generates from the same model. Evidence: the migration's evidence record. | Draft / not approved |
| 0.24 | 2026-10-23 | Migrated to SWCraft 0.19.1, a patch over 0.19.0 (contract `12.0.0` unchanged): the pin, and the Copilot agent profile from the release's template, which bounds `impact_of`'s summary to a page, adds the unconnected-ports recipes with a limit of twenty and states `find`'s bound; the Copilot instructions and the hook are unchanged. `check-model` still prints the 35 warnings by design. The generated ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to what 0.19.0 generates from the same model. Evidence: the migration's evidence record. | Draft / not approved |
| 0.25 | 2026-10-25 | Migrated to SWCraft 0.19.2, a patch over 0.19.1 (contract `12.0.0` unchanged): the pin, and the Copilot agent profile from the release's template, whose listing recipes answer a page of twenty rows (the sender-receiver table five) and give the components per level as one count per level; the Copilot instructions and the hook are unchanged. `check-model` still prints the 35 warnings by design. The generated ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to what 0.19.1 generates from the same model. Evidence: the migration's evidence record. | Draft / not approved |
| 0.26 | 2026-10-29 | Migrated to SWCraft 0.20.0 (contract `12.0.0` unchanged): the pin; the Copilot agent profile, instructions and hook from the release's template (the change sets reviewed in a SWCraft review tab, `SWCRAFT_REVIEW=panel`), and the template's new Codex hook `.codex/hooks.json`; and the template's build graph `moon.yml`, whose gate `validate-arxml` now writes `dist/build-report.md` and is never served from moon's cache — so § 8.2's preflight no longer warns of a cached gate. *Check Editor Tooling* moved to the `…` menu of the SWCraft view. `check-model` still prints the 35 warnings by design. The generated ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to what 0.19.2 generates from the same model. Evidence: the migration's evidence record. | Draft / not approved |
| 0.27 | 2026-11-03 | Migrated to SWCraft 0.21.0 (contract `12.0.0` unchanged): the pin, and the Copilot agent profile and instructions from the release's template (the review question waits in the review tab until it is answered; the profile sends a question about the architecture's state to the new `architecture_metrics` tool). `moon.yml`, the hooks and the model are unchanged. `check-model` still prints the 35 warnings by design. The generated ARXML, the Sphinx-Needs export, the build report and the component exports are byte-identical to what 0.20.0 generates from the same model; the views carry, in a port's and a data message's text, what the interface carries, their drawing unchanged. Evidence: the migration's evidence record. | Draft / not approved |
| 0.28 | 2026-11-08 | Migrated to SWCraft 0.22.0 (contract `12.6.0`, a minor over 0.21.0's `12.0.0`: 66 kinds and 349 fields): the pin; the Sphinx-Needs export is one file, `outputs.needs: dist/needs.json`, in place of the folder `dist/needs` — `outputs.rst` is a key the release no longer declares, an error — and the template's `moon.yml` names `generate-needs` in place of `generate-rst`, so §§ 3, 8.4 and 9 name the needs file; the Copilot agent profile and instructions from the release's template (the assistant reads the guide); `swcraft.yaml`'s header states that `clean-outputs` moves the previous ARXML aside as `model_old.arxml`, as the template's does. The model shows the release's new elements — `BrakeThermalProtection`'s two inter-runnable variables and its exclusive area, `DiagnosticManager`'s data event and its variable `LastThermalEvent` — and holds one requirements source: the trace link demonstration's 46 imported requirements, their links and `trace-decisions.yaml` leave the model (76 elements), the four external requirements name the team's earlier delivery `0.9`, and the walkthrough becomes the requirements exchange, `demos/requirements-exchange.md`. `check-model` prints the 4 warnings by design (the stub's and the stale case's three). Evidence: the migration's evidence record. | Draft / not approved |
| 0.29 | 2026-11-10 | Migrated to SWCraft 0.23.0 (contract `12.7.0`, a minor over 0.22.0's `12.6.0`: 67 kinds and 359 fields): the pin. The release writes the files of the chat clients a project is set up for, chosen with `swcraft init --client`; § 7's scaffold command names Copilot and Kiro, the project's two clients, their files are taken from a fresh 0.23.0 scaffold (Copilot's agent profile changed; Kiro's three files under `.kiro/` are new), and the Codex guard `.codex/hooks.json` is deleted, as the release's upgrade steps say for a project that does not use Codex. § 6 names VS Code and, where its chat is used, Kiro; § 8.3 adds restarting VS Code after an install and Kiro's own step — the installer serves VS Code only, so the extension's `.vsix` goes into Kiro by hand, then the project is trusted and the window reloaded once. `moon.yml` is unchanged; *Diagrams* opens the views in a tab of VS Code instead of the browser, which no step of this instruction depends on. The model gains the release's asynchronous calls, call-returned event and implicit accesses; `check-model` still prints the 4 warnings by design. Evidence: the migration's evidence record. | Draft / not approved |
| 0.12 | 2026-10-08 | Migrated to SWCraft 0.14.0 (contract `8.0.0`, a major over 0.13.0's `7.4.0`): the four data-type files moved into `model/data_types/base/` and `model/data_types/implementation/`, the empty `mapping_sets/` moved under `data_types/`, the three empty application-side directories added, every interface element renamed `type:` → `implementation_type:`, and `handle_termination_and_restart: no_support` written into all five components — the release note's recipe, done on this project; the Copilot instructions and the agent profile refreshed from the 0.14.0 template; the pin. Evidence: the migration's evidence record. | Draft / not approved |
| 0.13 | 2026-10-08 | Wording only: § 9 asks for the summaries this instruction itself requires, and § 10.2 states the owed Windows observation as the one the SWCraft release notes record instead of citing a file of the SWCraft repository by path. No line of this instruction describes the model's content — the model on `main` is now the storefront (68 elements, every kind and field of contract `8.0.0`), and the evidence records it names stay the history they are. No procedure, pin or generated output changed | Draft / not approved |
| 0.14 | 2026-10-08 | Wording only: § 9.1 names the storefront's evidence record and what it contributes on macOS — the XSD-mode build with eleven views, and the component export with `DiagnosticManager` and `InstrumentCluster` refused by design for the platform stubs their closures reach. No procedure, pin or generated output changed | Draft / not approved |
| 0.11 | 2026-09-23 | Migrated to SWCraft 0.13.0 (contract `7.4.0`, a major over 0.12.0's `6.0.0`): the pin and one empty `model/mapping_sets/` layer, which is all the release note asks of a model whose interfaces speak no application type and no enumeration. The generated ARXML and RST do not move; `views/` gains the `deployment` view. The colleague kit now carries the repository's `.gitattributes`. § 8.2 and § 12 carry the macOS measurement at 0.13.0 | Draft / not approved |
| 0.10 | 2026-09-17 | The Python preflight is retired: `scripts/setup_showcase.py`, its test and the two launchers `setup-showcase` / `setup-showcase.ps1` are deleted, because they were the last thing in the project that asked a workstation for a Python. § 8.2 is three commands (`swcraft --version`, `moon --version`, `moon run :build`) plus `swcraft validate` for the validation mode; § 4 rules 6–7, § 6, § 10.2 and § 12 follow. The manifest parser the publish workflow used moved into `scripts/build_colleague_kit.py`, the maintainer's tool, and the kit is byte-identical. No model, pin or generated output changed | Draft / not approved |
| 0.30 | 2026-11-13 | The open copy: § 6 asks for Git and network access to GitHub, and § 8.1 clones `https://github.com/swcraft-dev/swcraft-vehicle-control-showcase.git`. The evidence records are the maintainer's records in the work repository and are not part of the open copy, so § 9.1, § 10.1 and the revision rows name each by what it recorded instead of by its path. No procedure step changed | Draft / not approved |
| 0.31 | 2026-11-26 | Migrated to SWCraft 0.24.0 (contract `12.7.1`, a patch over 0.23.0's `12.7.0`: 67 kinds and 359 fields, unchanged): the pin. The release's archives, a macOS one among them, are downloaded from the Releases page of SWCraft's repository on GitHub, so § 8.3 names that page and the sums file, checks the archive's SHA-256 against its line, and adds the macOS step that clears the quarantine flag on the unpacked folder before the installer. The client files are taken from a fresh 0.24.0 scaffold as § 7 says (Copilot's agent profile and instructions and Kiro's steering changed); `moon.yml` follows the template's comment. The release reads a `.env` from the project's folder only; § 8.5's environment variable is unaffected. The generated ARXML, the Sphinx-Needs export and the component exports are byte-identical to what 0.23.0 generates from the same model; `check-model` still prints the 4 warnings by design. Evidence: the migration's evidence record. | Draft / not approved |
