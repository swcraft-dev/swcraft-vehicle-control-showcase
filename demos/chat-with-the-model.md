# Chat with the model

An assistant in a chat can answer questions about this architecture and propose changes to it — but
it never writes the model's files itself. It asks SWCraft, and SWCraft answers from the model. A
change it wants is one **proposal** that SWCraft checks first and then shows you in a **review
tab**, with **Approve** and **Reject**; nothing is written until you approve. And a **model guard**
stops the assistant's own file tools at the model directory, so it cannot go around SWCraft.

This page runs the same short scenario in two chat clients, **GitHub Copilot in VS Code** and
**Kiro**: one question about the model, one question about the impact of a change, one change
proposed and **rejected** in the review tab, and the guard refusing a direct reach into the model.
Everything you ask is in the boxes below; copy each one into the chat as it stands.

## Before you start

- SWCraft 0.24.0 is installed and `swcraft --version` answers `swcraft 0.24.0` in a new terminal —
  the project's install page says how (in the colleague kit, it is the kit's `README.md`).
- The project's files for both clients are already in it — the files the pinned release's onboarding
  writes for each client, taken from a fresh `swcraft init --client copilot --client kiro` scaffold —
  and nothing has to be run again:
  - Copilot: `.github/agents/swcraft-architect.agent.md` (the **SWCraft Architect** agent),
    `.github/copilot-instructions.md` and `.github/hooks/swcraft.json` (the guard);
  - Kiro: `.kiro/settings/mcp.json` (SWCraft's server, its review set to the panel),
    `.kiro/steering/swcraft.md` (SWCraft's instructions) and `.kiro/hooks/swcraft-guard.json` (the
    guard).
- The model is as it came: `git status` shows no change in `model/`. In an unpacked kit, where there
  is no git, `model/interfaces/INvStorage.yaml` lists two operations, `WriteBlock` and
  `GetErrorStatus`, and no other. The scenario ends with the model exactly as it started.

## 1. Open the project

### In VS Code with Copilot

1. *File → Open Folder…* and pick the project folder itself — the folder that holds `swcraft.yaml`.
   Answer **Yes** when VS Code asks whether you trust the authors.
2. Open **Copilot Chat** and start a **new** chat.
3. In the chat box, open the **chat-mode dropdown** and pick **SWCraft Architect**. This is the step
   everybody misses: the built-in modes answer too, but from files, beside the terminal. The choice
   does not last — every new chat and every window reload starts without it, so pick it again then.

The SWCraft Architect agent has SWCraft's tools and one read-only file tool, `view`, which it uses
for a large SWCraft answer that Copilot saved to a file. It has no file editing and no terminal. The
first time it calls each SWCraft tool, VS Code asks whether to allow it: answer **Allow in this
Workspace**. That permission lets the tool run; it is **not** the review of a change.

### In Kiro

1. **Install SWCraft's extension into Kiro, once.** SWCraft's installer hands the extension to
   VS Code, not to Kiro. In Kiro, open the Extensions view, its `…` menu, **Install from VSIX…**, and
   pick `swcraft-vscode-0.24.0.vsix` from the folder you unpacked the SWCraft archive into. Kiro takes
   the two companion extensions, Red Hat YAML and Red Hat XML, from its own extension store with it.
   The extension is what opens the review tab, so Kiro needs it even though its chat finds SWCraft
   through the project's files.
2. *File → Open Folder…* and pick the project folder itself. Kiro starts SWCraft's server in that
   folder: opened anywhere else, every SWCraft tool answers that there is no SWCraft project here.
3. **Trust the folder, then reload the window, once.** Kiro asks whether to trust the folder: choose
   **Trust**. Then run **Developer: Reload Window** from the command palette. Right after **Trust**,
   without the reload, Kiro has not read the project's files yet: no SWCraft server, no guard and no
   SWCraft instructions. After the reload Kiro's MCP servers view shows `swcraft` connected, its
   hooks list shows **SWCraft model guard**, and its chat lists `.kiro/steering/swcraft.md` under
   **Included Steering**. A folder you trusted before has all three from the moment you open it.
4. Open Kiro's chat.

Kiro asks before **every** call of a SWCraft tool; **Allow** runs it. Before its first call of each
SWCraft tool, Kiro's assistant also calls `tool_load` for it — one more step in the chat, nothing to
answer.

**Before you use Kiro on a real project:** Kiro's own data-protection page says that by default, on
its free tier and for individual subscribers, it collects what you and its assistant send — your
model's text among it — for service improvement. Check your organisation's rules first. It is
switched off under **Settings → User → Application → Telemetry and Content**.

## 2. Ask about the model

The non-volatile storage service, `INvStorage`, is used in two different ways in this model: a write
whose end is reported by an event, and a status the caller fetches itself. Ask:

```text
Which runnables use the non-volatile storage interface INvStorage, and how does each one get the result of its call?
```

The assistant answers through SWCraft's tools, never by opening a file. What it should find:

- **`DiagnosticManager.ProcessDiagnosticEvent`** makes both calls, through its port `rNvStorage`.
  Both are **asynchronous**: the runnable starts the call and goes on.
  - `WriteBlock` (the call `Call_StoreSnapshot`) stores a snapshot; the runnable does not wait for it.
  - `GetErrorStatus` (the call `Call_NvErrorStatus`) is **polled**: the runnable fetches the result
    itself, at the result point `Result_NvErrorStatus`.
- **`DiagnosticManager.ConfirmSnapshotStored`** takes the result of the write: it is started by a
  **call-returned** event (`ASRT_SnapshotStored`) when `WriteBlock` returns, and takes the result at
  `Result_StoreSnapshot`.

The wording is the assistant's own and differs from run to run; these facts do not. On the command
line, one query per fact:

```text
swcraft query swc --members runnables.calls --where port=rNvStorage --project swcraft.yaml
swcraft query swc --members runnables.calls --where asynchronous=true --project swcraft.yaml
swcraft query swc --members runnables.calls --where poll=true --project swcraft.yaml
swcraft query swc --members runnables.events --where type=call_returned --project swcraft.yaml
```

A call's line shows its runnable, `port` and `operation` only, so the first query answers the two
calls on `rNvStorage`, the second that both are asynchronous, and the third that `GetErrorStatus` is
the polled one. The fourth shows the call-returned event whole: its name, `WriteBlock` and
`Result_StoreSnapshot`. The call names `Call_StoreSnapshot` and `Call_NvErrorStatus` and the polled
result point `Result_NvErrorStatus` are not printed: they are in
`model/swc/application/DiagnosticManager.yaml`, under `ProcessDiagnosticEvent`'s `calls`.

## 3. Ask what a change would affect

Before changing an interface, an architect asks what depends on it:

```text
What would a change to the interface INvStorage affect?
```

SWCraft walks the model from `INvStorage` to everything that depends on it, directly or through
something else. The answer, as `swcraft impact INvStorage --project swcraft.yaml` prints it:

```text
Impact of 'INvStorage':

interface:
  swc DiagnosticManager (via port rNvStorage)
  task Task_100ms (runnables ProcessDiagnosticEvent, ConfirmSnapshotStored)
  connector ChassisToDiagnostics (via port DiagnosticManager.rThermalProtectionEvent)
  connector DiagnosticsToCluster (via port DiagnosticManager.pBrakeDiagnostics)
  connector NvMToDiagnostics (via port DiagnosticManager.rNvStorage)
  composition VehicleControl (member DiagnosticManager)
  sequence thermal_status_display (steps: ProcessDiagnosticEvent, ConfirmSnapshotStored)
```

The assistant may group or shorten it. The component that **serves** the interface, `NvM`, is not in
the list: it is an external component, declared outside this project, and its port only records
`INvStorage` as an observation (`observed_interface`), which SWCraft does not count as a dependency.
The connector `NvMToDiagnostics` is in the list, through `DiagnosticManager`'s port.

## 4. Propose a change, and reject it

Now ask for a change:

```text
Add an operation EraseBlock to the interface INvStorage.
```

The assistant does not edit the file. It states the change as **one proposal** to SWCraft, which
applies it to a private copy of the model, checks the copy with the model checks, and only then puts
it in front of you. This change passes the checks, so the proposal reaches you.

**The SWCraft review tab opens** beside the editor, by itself, without taking the focus: it shows
the change exactly as SWCraft computed it — `INvStorage`'s list of operations with `EraseBlock`
added — and under it **Approve** and **Reject**. In Kiro the same tab opens, naming the client as
`kiro`. Meanwhile the chat shows the tool as still running — in Kiro with **Working** and **Cancel**:
that is the wait for your answer, not a failure. Typing *approve* or *reject* in the chat does
nothing; the tab is the only place to answer.

Click **Reject**. One click decides, and nothing is written: `model/interfaces/INvStorage.yaml` is
unchanged — it still lists `WriteBlock` and `GetErrorStatus` only — and `git status` still shows no
change in `model/` (in an unpacked kit, the file's two operations are the check). The assistant is told the change was
rejected. Every proposal also leaves its record — what was proposed, what you were asked, what you
answered — as lines in `dist/audit.jsonl`.

Closed the tab without answering? The **Pending Change Sets** view in the SWCraft panel lists every
proposal still waiting; a click reopens its tab.

## 5. The guard: the assistant cannot go around SWCraft

The two clients have different file tools, so each project file of theirs guards what that client
could do. Both guards run `swcraft guard` before every tool call the assistant makes.

### Copilot: a direct read is denied

The SWCraft Architect agent has one file tool, `view`. Ask it to use it on the model:

```text
Use view to open model/interfaces/INvStorage.yaml and show me its text.
```

The guard denies the read, and the agent is told why:

```text
SWCraft: the model under `model` is read through the SWCraft tools, never by file tools; a saved SWCraft answer may be viewed.
```

The agent then reads the interface through SWCraft instead, or says it may not open the file. Copilot's
guard judges **reads and searches** only: the SWCraft Architect agent has no file edit to make, and a
file edit in Copilot's other modes is not guarded.

### Kiro: a direct edit is denied

Kiro's assistant has file tools that write. Ask it to use them on the model:

```text
Without the SWCraft tools, edit model/interfaces/INvStorage.yaml directly with your file tools and add EraseBlock to its operations.
```

Kiro's guard denies a write to the model directory and names the file:

```text
SWCraft: in this project the model directory (`model`) is changed through the SWCraft tools, whose changes the panel reviews; this edit writes `model/interfaces/INvStorage.yaml` there. Use the SWCraft MCP tool `change_set` instead.
```

In Kiro's editor the assistant has been seen reading the file before it writes it. Then it is the
read that is denied first,
with the sentence Copilot's guard gives above — Kiro's guard denies reads of the model as well as
edits. Either way the file is unchanged, and the assistant is pointed back to SWCraft's tools, whose
change would come to the review tab like the one in step 4.

## What this does not show

- **What the assistant says is not fixed.** A chat model words its answers differently from run to
  run, and a lighter model can answer worse. The facts above are SWCraft's answers, which the
  command lines reproduce; the assistant's sentences around them are not.
- **The guard has limits.** It is a check on each tool call, not a sandbox: a terminal command in
  Copilot's general Agent mode is not guarded, and in Kiro a shell command that reaches the model
  without naming it passes. The SWCraft guide's page *The model guard's rules* states every rule
  for each client and what it does not reach.
- **A home folder with a pattern character:** when your home folder's path holds a character that
  search patterns use, such as `(` in `John (Admin)`, Kiro's guard denies every path and pattern
  that starts with the home-folder `~`. Write the path in full instead.
- **Kiro was tried by SWCraft's makers on macOS**, with the Kiro releases the guide names; a later
  Kiro may read its files or name its tools differently. **Reject** through Kiro was not among what
  they tried.
- **Approve is not shown here.** Approving writes exactly the change the tab showed, and the model
  then holds an operation nothing calls; this page keeps the model as committed.
