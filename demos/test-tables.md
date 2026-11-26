# Test tables

The test team verifies the software against the architecture: which component runs where, in which
task, at which period, on which core. SWCraft writes that part of the model as **test tables** —
plain CSV files, one row per thing to verify — and the test team adds its own columns beside SWCraft's:
how it verifies a row, a comment, and whether it accepts the row. SWCraft never writes into the team's
files. When the team hands its folder back, SWCraft generates the tables again from the current model
and joins the team's columns to the new rows, row by row. A row whose facts changed since the team
looked at it is marked **`stale`**, so a review is never carried silently over a change it did not see.

This page shows that round trip on this project, with a test team's folder that is already here.

## What the project holds

A synthetic **test team** reviewed the tables of **last week's model** and handed its folder back. The
folder is committed: `demos/test-tables/annotations/`, the three tables as the team saved them —
SWCraft's columns as they were generated, and the team's filled in:

- every row has the team's `verification_method` (one per table: a configuration review, an
  inspection of the generated RTE and OS configuration, a timing measurement on the target) and
  `accepted` set to `yes`;
- one row is **rejected** — `accepted` is `no` — with the team's comment: the scheduling row of
  `BrakeThermalProtection`'s `InitThermalProtection`, which is mapped to no task, so the team has no
  schedule to verify.

Since last week, the model changed in two ways:

1. `DiagnosticManager` gained the runnable **`ConfirmSnapshotStored`**: the snapshot write to the
   non-volatile storage is now asynchronous, and this runnable is started when the write returns. It
   is mapped into `Task_100ms` and is a step of the `thermal_status_display` sequence.
2. `InstrumentCluster`'s runnable was called **`RefreshThermalStatus`** last week; it is
   **`UpdateThermalStatus`** now.

The team, its review and last week's model are synthetic: the folder was written in the repository by
`scripts/generate_test_annotations.py`, which takes a copy of the committed model, undoes the two
changes on the copy and generates the tables there. Nothing of git's history is read.

`.vscode/settings.json` names the folder in the setting `swcraft.testTables.annotations`, so VS Code
already knows where the team's folder is.

## 1. Generate the tables in VS Code

Open the project folder in VS Code. In the SWCraft panel, under *Model*, press **Test Tables** — it is
directly under **Diagrams** (or run *SWCraft: Test Tables* from the command palette).

The first press usually asks for the test team's **annotations folder**. Here it asks nothing: the
committed setting already answers it with `demos/test-tables/annotations`. The press runs
`swcraft generate test-tables` on the model as it is now; while it runs the item reads `running…`,
then `generated` and the time. The command's own lines go to the **SWCraft** output channel.

A tab named **Test Tables** opens. Its top line names the project, the SWCraft release that wrote the
tables and the annotations folder (`demos/test-tables/annotations`), with **Change…** and **Generate**
beside them; under it, each table's counts.

## 2. Read the tab

The tab has four sub-tabs, one per file: *Components*, *Component placement*, *Runnable scheduling* and
*Orphaned annotations*. Each row is coloured by its review state — accepted green, `stale` orange,
rejected red, a row nobody has reviewed left plain — and its `review_state` cell names the state in
words. The header and the first column, `row_id`, stay in place while you scroll. Hold the pointer over
a shortened cell to read it whole, or over a column header to learn whose column it is: SWCraft's or
the test team's.

**The tab is read-only, on purpose.** The tables are generated from the model, like the diagrams: to
change a row you change the model and press **Test Tables** again. Nothing in the tab can be typed
into, and saving a model file does not redraw it — a press does.

What this project shows:

| Table | Rows | Accepted | `stale` | Rejected | Not reviewed |
|---|---|---|---|---|---|
| *Components* | 7 | 6 | 1 | 0 | 0 |
| *Component placement* | 8 | 8 | 0 | 0 | 0 |
| *Runnable scheduling* | 10 | 7 | 0 | 1 | 2 |

and **one** orphaned annotation. Row by row:

- **`stale`** — `component:DiagnosticManager` on *Components*. The team accepted this row when
  `DiagnosticManager` declared two runnables; it declares three now (`runnables` is `3`), so its facts
  changed after the team's verdict. The row keeps the team's `yes`: SWCraft flags the verdict, it does
  not clear it.
- **Rejected** — `InitThermalProtection`'s row on *Runnable scheduling*, with the team's comment. Its
  facts have not changed, so the verdict still stands.
- **Not reviewed** — two rows on *Runnable scheduling*: `occurrence:DiagnosticManager:ConfirmSnapshotStored`,
  the new runnable, and `occurrence:InstrumentCluster:UpdateThermalStatus`. A row's identity holds names only, so the
  renamed runnable is a **new row** to SWCraft, and nobody has reviewed it.
- **Orphaned** — on *Orphaned annotations*, the team's annotation of
  `occurrence:InstrumentCluster:RefreshThermalStatus`. That row no longer exists, so its annotation has
  nowhere to join; SWCraft keeps it here instead of dropping it.

Every other row is accepted: its facts are the ones the team accepted. Moving a runnable to another
task or changing a period would keep the row and turn its verdict `stale`; renaming it, as here, makes
a new row and an orphan.

## 3. What the test team does next

The tables to hand over are in `dist/test-tables/`. The team takes them and:

- **the `stale` row**: looks at `DiagnosticManager`'s new facts and, if it still accepts the row,
  clears the row's `accepted_facts_hash` cell. The next generation then takes the row's current facts
  as the ones the verdict refers to, and the row is accepted again. Changing `accepted` alone is not
  enough;
- **the two new rows**: fills `verification_method` and `accepted` as for any row;
- **the orphan**: it is last week's verdict on the runnable now called `UpdateThermalStatus`. The team
  reviews the new row on its own facts; the orphan stays in `orphaned-annotations.csv`, round after
  round, until the team leaves it out of the files it hands back;
- **the rejected row**: stays rejected until the architect maps `InitThermalProtection` to a task, or
  the team changes its verdict.

They hand the folder back; the architect replaces `demos/test-tables/annotations/` with it (or keeps it
anywhere outside `model/`, `dist/` and `views/`) and presses **Test Tables** again. SWCraft only reads
the team's folder: after a run its files are byte for byte what they were.

To point at another folder, press **Change…** at the top of the tab: it asks again — the folder in use
offered first, marked *last used*, then *Choose a folder…* and *None yet (no annotations)* — and stores
the answer in `.vscode/settings.json`.

## On the command line

The same tables, from the project folder (the line is the same in Command Prompt, PowerShell and a
POSIX shell):

```text
swcraft generate test-tables --project swcraft.yaml --annotations demos/test-tables/annotations
```

It writes the five files of `dist/test-tables/` — the three tables, `orphaned-annotations.csv` and
`manifest.json` — and prints one line per table and the orphans:

```text
components.csv: 7 rows (6 accepted, 1 stale, 0 rejected, 0 not reviewed)
component-placement.csv: 8 rows (8 accepted, 0 stale, 0 rejected, 0 not reviewed)
runnable-scheduling.csv: 10 rows (7 accepted, 0 stale, 1 rejected, 2 not reviewed)
Orphaned annotations: 1
```

after a first line naming where it wrote. Without `--annotations`, every row is *not reviewed*. **Build**
neither writes nor needs the tables: generate them when you hand them over.

## What this does not show

- **No verification evidence.** The tables are a view of the model and prove nothing about the
  software. An accepted row is the test team's statement, never SWCraft's, and no table is
  verification evidence.
- **No execution order and no measured time.** `task_position` is the order in which the task lists
  its runnables, not the order in which they run; `wcet` is the architect's budget, not a measurement.
- **No sequences, data flow or interfaces**: the three tables carry components, placement and
  scheduling only.
- **The team's review is synthetic**, written by a script for this demonstration, and so is last
  week's model.
