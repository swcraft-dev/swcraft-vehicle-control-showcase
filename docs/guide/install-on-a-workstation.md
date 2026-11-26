# Installing SWCraft and the showcase on a Windows workstation

You need two zip files, each from its project's Releases page on GitHub; neither page asks you to
sign in:

| File | Where it comes from | What it is |
|---|---|---|
| `swcraft-0.24.0-windows-x64.zip` | <https://github.com/swcraft-dev/swcraft/releases/tag/v0.24.0> | SWCraft itself: the `swcraft` command, the VS Code extension and everything they need. Installed once per machine. |
| `vehicle-control-showcase-kit-0.24.0.zip` | <https://github.com/swcraft-dev/swcraft-vehicle-control-showcase/releases> | The demo project: a small vehicle-control architecture model. Unpacked anywhere; it installs nothing. |

Each zip has its sums file beside it on the same page: `SHA256SUMS-windows-x64` for SWCraft's,
`SHA256SUMS` for the demo's. To check a download, run `Get-FileHash <zip>` in PowerShell and compare
the hash with the zip's line in its sums file; the case of the letters does not matter. On a
mismatch, download the zip again and do not unpack it. A match proves that the file arrived whole,
not who made it: nothing is signed. Take SWCraft's Windows zip, not another platform's; the
installer refuses an archive made for another system.

The SWCraft zip is a large file — well over a hundred megabytes — because it carries
everything the installation runs on rather than asking your workstation for it. That is what makes
the list below as short as it is.

The two versions must match. The project is pinned to SWCraft 0.24.0 and every `swcraft` command
checks that pin before doing anything else. Against another release, the commands that write,
check or start the assistant refuse with a sentence naming both versions; the six read-only ones
(`diff`, `impact`, `list`, `metrics`, `query`, `resource-report`) print that sentence and answer
anyway.

## Before you start

- **Windows 10 or 11, 64-bit.** No administrator rights: everything lands under your own user
  profile (`%LOCALAPPDATA%\SWCraft`).
- **VS Code 1.110 or newer.** Below that the installer stops before handing the extension over,
  in one sentence naming your version and the one it needs; the toolchain is installed either way.
- **GitHub Copilot** signed in inside VS Code, with Copilot Chat enabled and MCP servers not
  switched off by an organisation policy. Copilot Chat itself is built into VS Code; the assistant
  half of the demo runs through it.
- **Kiro, if you want the chat in it too** — optional. Kiro is an editor built on the same base as
  VS Code, with a chat of its own; step 12 sets it up, and nothing else on this page needs it.
- **Nothing else — and that is the whole list.** No Python, no Node.js, no access to the VS Code
  Marketplace, no git, no moon, no SWCraft source checkout. The zip carries the Python the
  installation is built on, the layout engine the diagrams are drawn with, and the two companion
  extensions the editor uses — *Red Hat YAML* and *Red Hat XML* — which the installer hands to VS
  Code itself. A Python already on this machine is neither used nor changed, and a workstation
  that cannot reach the Marketplace gets completion and hover in the model files and structure in
  the generated ARXML all the same. (The requirements walkthrough of step 15 opens a requirements
  team's site that comes ready-made; building it yourself with that team's own tool needs Python
  3.11 or later and `pip`; the walkthrough says so there, and nothing else depends on it.)
- **An anti-virus exclusion helps.** The installation is thousands of small files, and a scanner
  that inspects each one as it lands makes the install take minutes rather than seconds. If your
  scanner lets you exclude a folder, exclude `%LOCALAPPDATA%\SWCraft` before step 2; if not, wait
  — the install finishes, it only takes longer.
- **The one thing the zips do not carry** is the AUTOSAR XSD schemas: they are licensed, and
  validation runs without them. Step 9 says how to point SWCraft at one if you hold it.

## Install SWCraft — once per machine

1. Unpack `swcraft-0.24.0-windows-x64.zip` anywhere, Downloads is fine. Nothing installs *into*
   that folder.
2. Double-click `swcraft_install.cmd`. If SmartScreen interposes, choose *More info → Run anyway*.
   The window waits for a key press at the end, so read what it says: it installs the toolchain
   under `%LOCALAPPDATA%\SWCraft`, adds it to your user `PATH` and hands the extension to VS Code
   when it finds it. It asks your machine for nothing: the Python it runs on comes out of the zip.
   A refusal is one sentence.
3. Open a **new** terminal — one opened before the install still has the old `PATH` — and run:

   ```text
   swcraft --version
   ```

   Expected: `swcraft 0.24.0`. The installation also brings `swcraft-specimens` at the same
   version, installed beside `swcraft`, which writes example projects; the steps below do not use
   it.
4. If the installer said it could not find VS Code, it installed none of the three extensions;
   install them yourself from the unpacked folder: Extensions view → the `…` menu → *Install from
   VSIX…*, first the two companions, `extensions\redhat.vscode-xml.vsix` and
   `extensions\redhat.vscode-yaml.vsix`, then `swcraft-vscode-0.24.0.vsix`. Nothing is fetched.

## Unpack the demo

5. Unpack `vehicle-control-showcase-kit-0.24.0.zip` where you keep projects. You get one folder,
   `vehicle-control-showcase`: the manifest `swcraft.yaml`, the model under `model\` (one YAML
   file per element, one directory per layer — 76 elements that between them use every kind and
   every field of SWCraft 0.24.0's model contract, though not every value of every enumeration),
   the demonstrations under `demos\` — the rejected changes and the diagrams in VS Code
   (`demos\README.md`), the chat with the model in Copilot and in Kiro, the test tables with a test
   team's folder, and the requirements exchange: the walkthrough, a synthetic requirements team's
   two deliveries, its Sphinx project, its ready-made sites, the architect's mapping, the prepared
   links and a ten-slide deck that tells the exchange to an audience — the trace link search's
   configuration under `experiments\`, the files the two chat clients read, already in place as
   SWCraft's onboarding writes them (taken from a `swcraft init --client copilot --client kiro`
   scaffold), so that nothing has to be set up — the Copilot agent, its instructions and the guard
   that keeps Copilot's file tools off the model under `.github\`, and Kiro's SWCraft server
   settings, instructions and guard under `.kiro\` — and this page as its `README.md`. A folder with no
   `demos\` is an earlier kit that the steps below do not describe — ask for the current one
   rather than continuing with it.
6. In VS Code, *File → Open Folder…* and pick that folder. When asked whether you trust the
   authors, answer **Yes** — in Restricted Mode the SWCraft panel does not appear at all, because
   the extension runs a program against the folder's content. The symptom, if the prompt was
   dismissed: the SWCraft icon was in the Activity Bar before you opened the folder and is gone
   after. Click *Restricted Mode* in the status bar and choose *Trust*; the icon returns without a
   restart.
7. Click the SWCraft icon in the Activity Bar (two blocks joined by a connector) and run
   **Check Editor Tooling** from the `…` menu at the top of the SWCraft view (it shows when the
   pointer is over the view). Expected: the installation and its version `0.24.0`, the two
   companion extensions marked `[ok]`, and `No problems found.` A companion marked `[problem]` is
   one the installer could not hand over; install its `.vsix` from the unpacked folder's
   `extensions\` folder as in step 4, or run the installer again, and run the check afterwards.

## Eight things to try

8. **Check Model** — panel → *Model → Check Model*. The SWCraft output channel shows
   `Validation passed (no artifacts generated).`; when the check finishes, VS Code moves to the
   **Problems** panel, which lists the warnings below, and the status bar shows
   `SWCraft: 0 errors · 4 warnings`. A finding's rule name in Problems is a link that opens the
   guide at that rule. The same from a terminal opened in the folder:

   ```text
   swcraft check-model --project swcraft.yaml
   ```

   The check also lists warnings, each a `WARNING:` line before that last line — a requirement
   that no element satisfies is one. A warning does not fail the check, and
   `--warnings-as-errors` makes any warning fail it. This model prints 4, by design. One is
   `WARNING: Requirement 'HAZ_BTP_BRAKE_FADE' is a stub: named as a parent, never imported.` —
   the placeholder for a parent requirement that has not been received, which the model keeps to
   show the field. The other three are one stale case: `REQ_BTP_TEMPERATURE_RANGE` moved to version 2 and its three interfaces still name
   version 1, each `WARNING: Interface '…' satisfies 'REQ_BTP_TEMPERATURE_RANGE@1', but requirement
   … is at version 2: confirm the link …`. The check's last finding line counts them,
   `0 error(s), 4 warning(s).`. Under `--warnings-as-errors` the check
   fails on them.

9. **Build** — panel → *Model → Build*. This is the whole build in one press and one output
   channel: `clean-outputs`, `check-model`, then the ARXML, the diagrams and the needs file, then
   `validate`. The first step that fails ends the run. A green run leaves
   `dist\model.arxml` (AUTOSAR 4.3.0), the diagrams under `views\` and `dist\needs.json` (the
   architecture requirements and the elements that satisfy a requirement, as a requirements team's
   Sphinx-Needs build reads them), and ends
   with `Validation passed.`, then opens the build report, `dist\build-report.md`, in the
   Markdown preview: the verdict with its mode stated, what was built, the findings, and each
   core's and memory's use against its limit. (A model check that stops the build with an error
   takes you to the Problems panel instead, and no report is written.) Before that line it prints
   `Note: XSD validation is skipped (requires the licensed AUTOSAR_4-3-0.xsd schema).` — the
   schema is AUTOSAR-licensed and in neither zip. If you have it, copy it to
   `schemas\AUTOSAR_4-3-0.xsd` inside the project folder and create a file named `.env` beside
   `swcraft.yaml` with one line, the full path and no quotes:

   ```text
   SWCRAFT_AUTOSAR_XSD_PATH=C:\path\to\vehicle-control-showcase\schemas\AUTOSAR_4-3-0.xsd
   ```

   *Build* then reports `ARXML validated against …`. The same gate from a terminal is
   `swcraft validate --project swcraft.yaml`, and it is the authoritative one: no diagram, no
   preview and no marker in the editor says anything about whether the model is valid.

   Exported on its own with `swcraft generate arxml --project swcraft.yaml --component <name>
   --output <file>`, each of BrakeController, BrakeTemperatureSensor, BrakeThermalProtection and
   VehicleStateManager gives a file that validates against the AUTOSAR schema, while
   DiagnosticManager and InstrumentCluster are refused by design: their closures reach the
   platform stubs — definitions the project declares but does not own — that a file exported on
   its own could not contain. *Model → Import Component*, directly under *Export Component*, reads
   such a file back: pick it, and the dry run's report opens in the tab *Component Import Report*
   with **Write** and **Cancel** under it — nothing is written before **Write**. For the file
   `BrakeController` exports, the report says `SWC BrakeController: unchanged`.

   *Model → Architecture Metrics*, under *Resource Report*, writes `dist\metrics\metrics.md` and
   opens it in the Markdown preview: what state the architecture is in and where it is heading,
   computed from the model alone, with no overall score — it is not a gate. On this model its
   overview counts the 4 warnings, all from trace rules, and names `BrakeThermalProtection` as
   the one component with far more dependencies than the rest. It compares the working tree with
   git's last commit; the unpacked folder is not a git repository, so the report says `Nothing to
   compare: the project is not in a git repository.` and shows the state all the same. The same report in a
   terminal is `swcraft metrics --project swcraft.yaml`.

10. **Diagrams** — panel → *Model → Diagrams*. It redraws the model's diagrams into `views\` and
    opens their index, `views\index.html`, in a tab of VS Code; every later press reuses that tab.
    They are plain files — an SVG and a page per view — so nothing is served, nothing is fetched and
    nothing keeps running. The index lists eleven
    views: for each of the three compositions — `VehicleControl`, `Chassis` inside it and
    `BrakeSubsystem` inside that — an internal block diagram with every port of every member and
    the connectors and delegations between them, and an overview; the nesting of the
    compositions; the deployment — the processor, its two cores `Core0` and `Core1`, the partition
    on each (`P_Vehicle`, ASIL A, and `P_Brake`, ASIL B and trusted), and in each partition its
    task and the components that task runs; and three sequence diagrams,
    `brake_thermal_cycle` and `thermal_protection_fast_path` on the 50 ms task and
    `thermal_status_display` on the 100 ms task. The platform's `NvM` is the one component no
    task runs, so the deployment does not draw it, and `views\report.txt` says so in one line. A
    page has a search box for a port or a component by name, and for the data elements,
    operations, arguments and types the interfaces carry; pointing at a line lights it together
    with the two ports it joins, pointing at a port lights it and its lines, and the text of what
    you point at shows at once beside the pointer. On a port, and on a sequence diagram's data
    message, that text lists what its interface carries — the data elements with their types, or
    the operations with their arguments — up to eight lines; on a port with more, a click opens
    the whole list beside the picture. The one dashed line,
    `NvMToDiagnostics` on `VehicleControl`, joins the platform's `NvM`, whose port declares no
    interface: the model check cannot judge that connection, and the line's text says so.

    The tab leads to the model and back: **Ctrl+click** a drawn component, port, connector or task
    and its YAML file opens beside the diagram, at its line. The `diagram` link on the line above
    the file's top-level name shows that element's diagram; for a port or another element inside the
    file, put the cursor in its name and choose **SWCraft: Show in Diagram** from the editor's
    context menu, which brings the diagram back with that element selected. **← Back** and
    **Forward →** in the tab's header walk the pages you opened. `demos\README.md`, section *Diagrams in VS Code*, walks it on one runnable.
    Saving a model file does not redraw anything: the tab says its diagrams are out of date and
    offers **Generate**, which runs the press again; `views\report.txt` names anything that could
    not be drawn. The same files open in a browser from `views\index.html` too — everything but the
    way to the model files works there.

11. **Ask the assistant** — open Copilot Chat (`Ctrl+Alt+I`). In the chat box, open the mode
    dropdown and pick **SWCraft Architect**; the default mode answers from files and never talks
    to the model. Then ask, for example:

    ```text
    Which SWCraft version and model baseline are you serving, and which software components does the model contain?
    ```

    VS Code asks once per tool whether the assistant may run it; answer *Allow in this
    Workspace*. Expected: the assistant calls `discover` and `read` and answers with version
    0.24.0 and the model's components. The model holds seven — BrakeController,
    BrakeTemperatureSensor, BrakeThermalProtection, DiagnosticManager, InstrumentCluster,
    VehicleStateManager and the platform stub NvM — which is what `swcraft list swc --project
    swcraft.yaml` prints in a terminal; how the assistant words its answer, and whether it counts
    the stub among the components, varies. If you then ask for a change, VS Code opens a SWCraft review tab beside the
    editor with the exact before/after delta and two buttons, **Approve** and **Reject**; nothing
    is written until you click **Approve** there. The question waits in the tab until you answer
    it; if the assistant cancels it or its session ends first, nothing is written.
    `demos\chat-with-the-model.md` runs a whole short scenario this way: a question, an impact
    question, a change proposed and rejected, and the guard that keeps the assistant's own file
    tools out of `model\`.

12. **The same in Kiro** — optional, and only if Kiro is on this machine. SWCraft's installer hands
    the extension to VS Code, not to Kiro, so in Kiro install it yourself, once: Extensions view →
    the `…` menu → *Install from VSIX…* → `swcraft-vscode-0.24.0.vsix` from the unpacked SWCraft
    folder. Kiro takes the two companion extensions from its own extension store with it. Then
    *File → Open Folder…* and pick the project folder itself, choose **Trust** when Kiro asks, and
    run **Developer: Reload Window** from the command palette, once: until that reload Kiro reads
    none of the project's `.kiro\` files — no SWCraft server, no guard, no instructions. After it,
    Kiro's chat lists `.kiro\steering\swcraft.md` under **Included Steering**, and the question of
    step 11 gets the same answer there; Kiro asks before every SWCraft tool call, and **Allow** runs
    it. A change it proposes opens the same SWCraft review tab. Before you use Kiro on a real
    project: by default, on its free tier and for individual subscribers, Kiro collects what you
    and its assistant send for service improvement; `demos\chat-with-the-model.md` says where to
    switch that off.

13. **Watch the model refuse a change** — open `demos\README.md`. It lists nine small edits,
    each of which breaks exactly one of SWCraft's rules: make one in the file it names, save, and
    run `swcraft check-model --project swcraft.yaml` in a terminal opened in the folder (or
    **Check Model** in the panel). The command fails and prints the `ERROR:` line the page quotes.
    Undo the edit and save, and the model passes again; if you lose track of an edit, unpack the
    zip again.

14. **Test tables** — panel → *Model → Test Tables*, directly under *Diagrams*. It writes the
    tables a test team verifies the architecture against — the components, where each one runs,
    and each runnable's task, period and budget — as CSV files under `dist\test-tables\`, and opens
    them in a read-only tab, one sub-tab per table. The project already holds a synthetic test
    team's review of last week's model, `demos\test-tables\annotations\`, and the project's
    settings name that folder, so the first press asks nothing: each row is coloured by its review
    state — accepted, rejected, not reviewed, or `stale` where the model changed since the team
    accepted it. `demos\test-tables.md` reads the tab row by row. The same tables from a terminal:
    `swcraft generate test-tables --project swcraft.yaml --annotations demos\test-tables\annotations`.

15. **Exchange requirements with a requirements team** — open `demos\requirements-exchange.md` and
    follow it. It imports a synthetic requirements team's delivery, a `needs.json`, with *Model →
    Import Requirements* and the team's mapping; the dry run's report opens in the tab
    *Requirements Import Report* with **Write** and **Cancel**, and nothing is written before
    **Write**. It then links a few of the new requirements by hand in the panel's *Experiments →
    Trace Links* — *Labelling*, writing the links with **Apply…** — and the rest from a prepared
    file in one command, builds `dist\needs.json` for the team, opens the team's ready-made site,
    imports the team's next delivery and confirms the one link it changed. Building the team's
    site yourself is the one optional part that needs more than this page installs: Python 3.11 or
    later and `pip` access to PyPI, for the team's tool, not the project's; every step runs
    without them. To start over, unpack the zip into a **new, empty** folder.

## If something does not work

| Symptom | Cause | What to do |
|---|---|---|
| `swcraft` is not recognised | the terminal predates the install | open a new terminal; for VS Code's own terminal, quit VS Code and start it again |
| *Check Editor Tooling* says the installation is missing | VS Code was started before the install | restart VS Code; if it persists, *Setup → Install Toolchain* and point it at the SWCraft zip |
| `…pins toolchain_version 0.24.0 and this is SWCraft …` | another release is installed | install the 0.24.0 archive |
| a companion extension is `[problem]` | the installer could not hand that one to VS Code | install its `.vsix` from the unpacked folder's `extensions\` folder as in step 4, or run the installer again; SWCraft's own commands work without it |
| *Diagrams* opens nothing, or a page with no drawing | SWCraft was installed from an older archive, or the page was opened from a `views\` that a failed build removed | install the 0.24.0 archive — *Setup → Update Toolchain* takes the zip directly — and press *Build*, then *Diagrams* again |
| the Diagrams tab says the pages were generated by another SWCraft release | `views\` was written by another release | press **Generate** in the tab, once |
| Kiro's chat has no SWCraft tools and lists no SWCraft steering | the window was not reloaded after **Trust**, or Kiro opened a folder other than the project's | open the project folder itself and run **Developer: Reload Window** once |
| Kiro's review tab does not open, or the SWCraft panel is missing in Kiro | SWCraft's extension is not installed in Kiro — the installer serves VS Code only | install `swcraft-vscode-0.24.0.vsix` in Kiro, step 12 |
| the install takes minutes with no output | the anti-virus scanner reads every file as it lands | wait — it finishes; next time exclude `%LOCALAPPDATA%\SWCraft` first |
| the assistant answers without calling a tool | the chat is in the default mode | pick **SWCraft Architect** in the mode dropdown — every new chat starts in the default mode |
| the assistant reports a change, the files are unchanged | the question in the SWCraft review tab is not answered yet — it waits until it is | nothing commits without your approval; answer it in the review tab, or ask again |
