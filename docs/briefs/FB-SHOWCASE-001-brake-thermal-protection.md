# FB-SHOWCASE-001 — Brake Thermal Protection Showcase Feature Brief

| Field | Value |
|---|---|
| Document ID | FB-SHOWCASE-001 |
| Revision | 0.22 |
| Status | Revision 0.2 — the storefront scope; approved by the owner on 2026-10-08 (0.1 was approved as the scope baseline for model development) |
| Owner | Vehicle Control Showcase project lead |
| Applies to | Synthetic SWCraft showcase only |
| Created | 2026-08-15 |

## 1. Purpose

Create the smallest credible **from-scratch synthetic model** that demonstrates how SWCraft turns
reviewed engineering intent into a checked model and generates consistent ARXML, diagrams, a
Sphinx-Needs export, and supporting evidence.

`Brake Thermal Protection` is the subject of the demonstration, not the product being developed.
The project shall optimize for observable SWCraft capabilities, a clear engineering story, and
repeatable execution. It shall not optimize for automotive-domain completeness.

## 2. Demonstration Question

The showcase shall answer one question:

> Can an engineer use SWCraft, with controlled AI assistance, to introduce a bounded architectural
> feature into a reviewed synthetic model, reject an invalid change, understand the impact, and
> deterministically regenerate traceable outputs?

Since revision 0.2 it also makes one observable claim of its own:

> Every model feature SWCraft supports is visible in one coherent model.

"Every model feature" is every kind and every field of the model contract of the SWCraft release
the project pins — on SWCraft 0.24.0, contract `12.7.1`, 67 kinds and 359 fields — each used at
least once by a model that passes `swcraft check-model` and `swcraft validate`. Showing the `stub`
field costs one warning, and showing a link that needs confirmation three more, one per interface
still naming the version before `REQ_BTP_TEMPERATURE_RANGE`'s (§ 5): the model passes with exactly
those 4 warnings, by design, and therefore fails `--warnings-as-errors` on that set alone. A test
in the repository reads that contract from the installed SWCraft and fails when one is missing,
and checks those 4 warnings.

It does not answer whether the resulting function is suitable for a vehicle.

## 3. Starting Point

The project is intentionally greenfield. It is not imported from Rhapsody, DaVinci Developer, an
AUTOSAR authoring tool, customer data, or an existing vehicle program.

The brief itself is the synthetic upstream input. Model content is created from this brief and its
reviewed acceptance criteria. Generated ARXML is an output and shall not be edited as a source.

This choice demonstrates SWCraft's from-scratch workflow only. Importing or reconciling an
existing engineering model is a separate brownfield use case and is outside this showcase.

## 4. Synthetic Engineering Story

The baseline represents only enough context to make the change understandable:

- `BrakeTemperatureSensor` publishes an already measured synthetic brake temperature;
- `BrakeController` publishes a synthetic requested brake action;
- `VehicleStateManager` publishes a synthetic operating state;
- `DiagnosticManager` receives a synthetic thermal-protection event;
- `InstrumentCluster` receives a synthetic thermal status for display.

`BrakeThermalProtection` is the feature. Revision 0.1 had it added live to the baseline; since
revision 0.2 it is committed, and it consumes the three relevant baseline inputs and publishes:

- a permitted brake-action value;
- a thermal-protection status;
- a synthetic diagnostic event.

Around it, revision 0.2 places a small vehicle, so that every model feature has a natural home:

- a three-level hierarchy — `VehicleControl` holds `Chassis`, which holds `BrakeSubsystem`, the
  sensor and `BrakeThermalProtection`; `Chassis` adds `BrakeController`, and the root adds
  `VehicleStateManager`, `DiagnosticManager`, `InstrumentCluster` and the platform's `NvM`;
- a diagnostic client-server service, `IBrakeDiagnostics`, served by `DiagnosticManager` and
  called by `InstrumentCluster`;
- physical data types — a temperature with unit, conversion and range, a vehicle speed stating the
  same by reference to a unit, a compu method and a data constraint, an enumeration, a record and
  an array — each mapped to its implementation side;
- an ASIL D safety goal split into two ASIL B(D) requirements, one for the main channel (sensor
  and controller) and one for the monitor channel (`BrakeThermalProtection`), each naming the
  goal in its `derived_from`; the goal itself is satisfied by `Chassis`, the one composition that
  holds both channels. The independence
  such a decomposition assumes is not modelled: both channels run in one task on one core, and
  the monitor reads the main channel's brake temperature;
- three design constraints the architecture states for itself (`source: architecture`), each
  satisfied by the elements whose own values meet it: `REQ_BTP_CORE_LOAD`, each core within its
  load budget, by the processor, both cores and the three tasks; `REQ_BTP_TEMPERATURE_RANGE`, the brake
  temperature carried from −40 °C to 1000 °C at 0.1 °C, by the three interfaces that carry it;
  `REQ_BTP_EXECUTION_CONTEXT`, both channels in an ASIL B partition on a core and with a memory
  capable of it, by the 50 ms task, `P_Brake`, `Core1` and `RAM`. The last two derive from the two
  decomposed requirements;
- the provenance of the external requirements, as a requirements team's delivery would carry it
  (synthetic, like the rest): a `revision` on each, the delivery that holds them as their
  `baseline` — `0.9`, the requirements team's earlier delivery (§ 5) — and on the two baseline
  requirements the document that states them (`BL-SHOWCASE-001`, § 6);
- a stub: the safety goal derives from `HAZ_BTP_BRAKE_FADE`, the hazard it answers, which the
  requirements have not received; `HAZ_BTP_BRAKE_FADE` is the placeholder the requirements import
  writes for such a parent (`stub: true`), and one of the model's four warnings by design (§ 2);
- shared state inside a component: `BrakeThermalProtection`'s start-up and its 50 ms evaluation
  share the filtered brake temperature and the derating step count as inter-runnable variables,
  and the evaluation runs inside the exclusive area `ThermalState`, which the start-up may enter;
  `DiagnosticManager`'s `ProcessDiagnosticEvent` is started by each arrival of a thermal protection
  event as well as by its 100 ms poll, so every event is stored when it arrives, and keeps the last
  one in `LastThermalEvent`, which `ServeSnapshot` reads to answer the tester;
- the asynchronous snapshot: `ProcessDiagnosticEvent` starts writing the snapshot to the platform's
  non-volatile storage (`WriteBlock`, the call `Call_StoreSnapshot`) **asynchronously**, with a
  timeout, and does not wait for it — a storage job outlives the 100 ms task; a runnable of its
  own, `ConfirmSnapshotStored`, is started by the **call-returned** event of that write
  (`ASRT_SnapshotStored`, the result taken at `Result_StoreSnapshot`) and records whether the
  snapshot was stored. It runs in `Task_100ms` right after `ProcessDiagnosticEvent` and is a step of
  the `thermal_status_display` sequence. The storage's error status is taken the standard's other
  way: `ProcessDiagnosticEvent` calls `GetErrorStatus`, a second operation of `INvStorage`,
  asynchronously and **polls** for the result itself (`Call_NvErrorStatus`, its result at
  `Result_NvErrorStatus`);
- implicit protection inputs: `BrakeThermalProtection`'s 50 ms evaluation reads the brake request
  and the operating state **implicitly** (`by: implicit`), so each run works on one consistent pair
  of inputs that does not change while it runs, and writes the permitted brake action implicitly,
  published once when the run ends. The brake temperature stays a read `by: value`: its port asks
  for an update flag, which an implicit read cannot carry, and the queued thermal protection event
  cannot be read implicitly either — the two rejected changes that try it are refused (§ 9);
- a second core that runs the ASIL B work, and three sequences.

The model expresses component responsibilities, interfaces, connections, scheduling intent, and
traceability. It does not implement a physical thermal model or a production control algorithm.

## 5. Deliberate Simplifications

All values, names, periods, thresholds, resource estimates, and state transitions are illustrative.
They exist only when needed to exercise a SWCraft rule or make the demonstration understandable.

The following are explicitly outside scope:

- brake-system physics, heat transfer, temperature estimation, and sensor plausibility;
- production control laws, torque arbitration, hydraulic behavior, and vehicle dynamics;
- calibration strategy or vehicle-specific thresholds;
- redundancy, degradation strategy, watchdog design, and production diagnostics;
- HARA, ASIL allocation, safety concept, FMEA/FMEDA, DFA, or safety-case claims;
- complete AUTOSAR platform, ECU, BSW, RTE, network, memory, and deployment configuration;
- production code generation, compilation, flashing, SIL/HIL, or vehicle validation;
- proof of compatibility with a real downstream AUTOSAR toolchain;
- tool qualification or qualification credit for the generated artifacts.

No scope item may be added merely to make the example look more like a production architecture.

Since revision 0.2 the model declares ASIL levels on requirements, components and data elements,
ASIL capabilities on the cores and the memory, `measures` on a port and a `coexistence` argument on
a mixed-criticality task. Since revision 0.5 one interface carries two levels: `IBrakeTemperature`'s
`temperature` is ASIL B and its `wheelTemperatures` QM, each data element being its own signal, and
both ASIL-rated consumers declare a measure for the QM element on their port (`rBrakeTemperature`,
`rRearBrakeTemperature`).
These are **illustrative declarations that exercise SWCraft's checks, not a safety concept**: no
HARA stands behind the levels, no analysis behind the decomposition, and no tool verifies what a
measure or a coexistence argument says. The ASIL allocation item above stays out of scope.

`NvM` is an external component stub. It stands for a platform file this project does not have; the
three platform interface stubs (`INvStorage`, `IOdometer`, `IEcuMode`), the one platform
implementation type (`PlatformCounter16`) and every `/Platform/...` path are invented in the same
way. The platform's BSW and its deployment stay out of scope.

Two declarations exist to show a field or to keep a rule satisfied rather than to model the
function, and are named here so that nobody reads them as modelling advice:

- `is_service: true` on `IBrakeTemperature` and `IBrakeDiagnostics` shows the field. The AUTOSAR
  Software Component Template sets that flag on an interface used between a component and an
  AUTOSAR service on the same ECU; between two application components, as here, a real project
  would leave it unset.
- The measure for `vehicleSpeed` on `BrakeThermalProtection`'s port `rOperatingState` guards an
  element no runnable of that component reads. The consumer rule judges every element of a
  required port's interface that is rated below the component, so the port states one measure per
  such element.
- `BrakeThermalProtection`'s two inter-runnable variables are written in the two forms the
  contract allows: `FilteredBrakeTemperature` `implicit` on an application type, with
  `sw_calibration_access: read_only` and a `description`, and `DerateStepCount` `explicit` on an
  implementation type, `uint16`; one read and one write of a variable carry a `name` and the others
  none. The function would need neither the second form nor the calibration access; they show the
  fields. The shared state itself, the exclusive area `ThermalState`, `DiagnosticManager`'s data
  event beside its 100 ms poll and its variable `LastThermalEvent` are part of the story (§ 4).

Every `satisfies` entry is true of the element it sits on, and a reader can check it against the
model's own values. A component's own link, a port's or a runnable's allocates the requirement to
the component; these are the trace, moved from the requirements in revision 0.8 without changing
what any component is allocated. A link on a composition, an interface, a task or a hardware
element allocates no level and records what the element meets:

- `Chassis` satisfies the safety goal: it is the one composition holding both channels of the
  decomposition — the two sensor occurrences, `BrakeController` and `BrakeThermalProtection`.
- `INvStorage` satisfies `REQ_BTP_DIAGNOSTICS`: its `WriteBlock` is the operation
  `ProcessDiagnosticEvent` calls to store the snapshot, and `ConfirmSnapshotStored`, which records
  whether it was stored, satisfies the requirement as `ProcessDiagnosticEvent` does. Beside the runnables,
  `DiagnosticManager`'s port `rThermalProtectionEvent` satisfies it too: it is where the events
  the requirement records arrive, queued four deep. And `BrakeThermalProtection`'s port
  `pPermittedBrakeAction` satisfies `REQ_SHOWCASE_FEATURE_001` beside the evaluating runnable: it
  is where the feature publishes the permitted brake action. Neither port link allocates anything
  new; each component already carries the requirement through its runnable.
- `REQ_BTP_CORE_LOAD` (each core at or below its budget, 70 % on `Core0`, 60 % on `Core1`):
  `Core0` declares `threshold: 0.7` and carries `Task_100ms`, 6000 µs every 0.1 s, 6 %, and
  `Task_100ms_Low`, 1000 µs every 0.1 s, 1 % — 7 % in all; `Core1`
  declares `threshold: 0.6` and carries `Task_50ms`, 12000 µs every 0.05 s, 24 %; both strict, and
  `CPU` is the processor both cores belong to. `swcraft resource-report` prints the same figures.
- `REQ_BTP_TEMPERATURE_RANGE` (−40 °C to 1000 °C at 0.1 °C): `BrakeTemperature_C` is in `degC`
  with `factor: 0.1`, `offset: -40` and `range` −40 to 1000, stored as `BrakeTemperatureRaw_T`,
  0 to 14400 tenths above −40 °C. `IBrakeTemperature` carries it (`temperature`, and the four
  `wheelTemperatures`), `IThermalProtectionStatus` in the record's `temperature`, and
  `IBrakeDiagnostics` as `peakTemperature` and in the snapshot's stored temperatures. The
  requirement is at **version 2** since revision 0.13, which states that both ends of the range
  are included (the conversion's limits are closed); the three interfaces still name version 1,
  the stale case: each link needs confirmation (`trace.link-needs-confirmation`) until someone
  checks the interface against version 2 and writes `@2`.
- `REQ_BTP_EXECUTION_CONTEXT` (an ASIL B partition, a core and a memory capable of it):
  `Task_50ms` runs both channels — the two sensor occurrences, the protection and the
  controller — in `P_Brake`, `asil: B`, on `Core1`,
  `asil_capability: D`; `RAM`, accessible to `Core1`, declares `asil_capability: B`.

Since revision 0.19 the model carries **no** demonstration requirements. The **requirements
exchange** (`demos/requirements-exchange.md`) is declared demonstration content beside the model:
a synthetic requirements team keeps its software requirements in a Sphinx-Needs project
(`demos/requirements-exchange/team/`) and delivers them as `needs.json`, and the committed model is
the state before the team's delivery 1.0 — its four external requirements at the team's earlier
delivery `0.9`, no software requirement, no link to one and no `trace-decisions.yaml`. Delivery 1.0
holds those four and 46 software requirements (`SWR-*`), written against this model's element names
and derived from no real project: 42 in four documents — *SRS Brake Control* (12), *SRS Thermal
Protection* (12), *SRS Diagnostics* (10) and *SRS Driver Information* (8) — and four with none.
The walkthrough imports them, links two by hand in SWCraft's trace link search and rejects one
candidate, then applies the rest of the links from a prepared decisions file
(`demos/requirements-exchange/prepared-links.json`, generated, copied under `dist/` and never
changed by use). It builds `dist/needs.json` for the team's Sphinx site, opens the ready-made sites
under `demos/requirements-exchange/sites/`, and imports delivery 1.1, which changes one linked
requirement and drops one distractor. Nothing the walk writes into the model is committed.
**Eight are distractors** —
`SWR-BRK-011` *Pedal feel*, `SWR-THP-010` *Cooling estimate*, `SWR-DIA-009` *DTC clearing*,
`SWR-DIA-010` *Diagnostic session*, `SWR-DRV-005` *Warning lamp*, `SWR-DRV-006` *Display
brightness*, `SWR-GEN-003` *Service brake availability* and `SWR-GEN-004` *Software update*: the
architecture realises none of them, on purpose, and none shall be linked. These requirements are
not part of the feature's engineering story (§ 4); `demos/requirements-exchange/answer-key.json`
names the element each of the others was written against.

The **test tables** (`demos/test-tables.md`) are declared demonstration content of the same kind: a
synthetic test team's review of the tables SWCraft generates from the model, committed under
`demos/test-tables/annotations/`. The team reviewed **last week's** model — the committed one with
`ConfirmSnapshotStored` removed and `InstrumentCluster`'s `UpdateThermalStatus` under its earlier
name `RefreshThermalStatus`, a model that exists only as a copy `scripts/generate_test_annotations.py`
makes — so that against the committed model every review state shows. Neither the team nor last
week's model is part of the feature's engineering story.

## 6. Complexity Budget

Since revision 0.2 the budget is the storefront's element count, layer by layer — exactly what
the claim of § 2 needs on SWCraft 0.24.0 (contract `12.7.1`), and no element more; the
requirements exchange's requirements (§ 5) are not in the committed model:

| Model layer | Maximum |
|---|---:|
| SWCs, including `BrakeThermalProtection` and the `NvM` stub | 7 |
| Interfaces | 10 |
| Connectors | 9 |
| Application data types | 6 |
| Implementation data types | 11 |
| Base types | 2 |
| Mapping sets | 1 |
| Units | 1 |
| Compu methods | 2 |
| Data constraints | 1 |
| Requirements, including the `HAZ_BTP_BRAKE_FADE` stub | 11 |
| Compositions | 3 |
| Tasks | 3 |
| Demonstration sequences | 3 |
| Hardware elements (a processor, two cores, a partition on each, one memory) | 6 |
| **Total** | **76** |

Revision 0.1's budget (6 SWCs, 8 requirements, 8 interfaces, 8 connectors, 3 tasks, 2 sequences)
was sized for the feature alone; it is superseded.

Each data type shall either carry a kind or a field no other element of the model carries, or be
a type the story needs as a target: `uint8` and `uint16` are the implementation side the mapping
set gives `ThermalProtectionState` and `VehicleSpeed_Kmh`, which keeps every application type
mapped, and `uint8_base` is the base type `uint8` stands on. Resource values may be attached to
components solely to demonstrate reporting and impact analysis; they are not engineering
estimates.

Exceeding this budget requires a brief revision that identifies the new observable SWCraft claim
and explains why an existing model element cannot demonstrate it.

## 7. Required SWCraft Coverage

Every committed model element shall support at least one of these observable claims:

1. requirements can be traced to architecture elements;
2. typed ports and connectors can be checked deterministically;
3. an incompatible connection is rejected without leaving a model delta;
4. an approved feature produces an understandable semantic and resource impact;
5. one source model generates consistent ARXML, diagram, and Sphinx-Needs outputs;
6. a component can be exported with its supported dependency closure;
7. deterministic replay and the controlled-AI path reach equivalent accepted semantics;
8. every model feature SWCraft supports is visible in one coherent model (§ 2);
9. requirements can be exchanged with a requirements team and linked to the architecture with
   SWCraft's trace link search, proposals decided by a person and written by Apply (§ 5).

If an element supports none of these claims, it shall be omitted.

## 8. AI and Human Roles

AI may propose requirements, model changes, trace links, tests, and explanations within an
approved bounded step. AI output is untrusted until it passes deterministic checks and human
review.

The human reviewer owns:

- approval of this brief and each acceptance criterion;
- confirmation that a change stays within the demonstration scope;
- review of semantic diff and downstream impact;
- acceptance or rejection of the resulting model;
- any decision to revise the complexity budget.

The live demonstration shall not imply that AI independently engineered a vehicle function.

## 9. Acceptance Criteria

The feature result is accepted for the showcase when:

- the model remains within the complexity budget;
- every model element maps to a required SWCraft coverage claim;
- the deliberately incompatible connection fails without persistent mutation;
- the model carries every kind and every field of the pinned release's model contract with no
  warning but the stub's and the stale case's three links to confirm, and each
  rejected-change demonstration under `demos/` is refused by exactly the rule it names;
- the valid change adds only the reviewed feature scope and trace links;
- the canonical build generates deterministic ARXML, diagram, and Sphinx-Needs outputs;
- validation mode is reported honestly as structural or XSD;
- deterministic replay and controlled-AI execution have equivalent accepted semantics;
- documentation explicitly states that the example is synthetic and not production-ready.

Cross-platform and presentation-release gates remain governed by the work instructions; they are
not relaxed by this brief.

## 10. Stop Rule

Model development stops when the acceptance criteria and required SWCraft coverage are met.

Additional automotive detail is deferred unless it exposes a specific SWCraft defect or is
required for an already approved demonstration claim. Domain realism beyond that point is scope
creep, not showcase progress.

## 11. Revision History

| Revision | Date | Change |
|---|---|---|
| 0.1 | 2026-08-15 | Scope baseline for the from-scratch model: the feature added live to a five-component baseline |
| 0.16 | 2026-10-25 | SWCraft 0.19.2 (contract `12.0.0`, unchanged; 59 kinds and 323 fields): § 2 and § 6 name the release; the element count stays 122, no model file moves, and the 35 warnings by design are unchanged. The ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to 0.19.1's |
| 0.17 | 2026-10-29 | SWCraft 0.20.0 (contract `12.0.0`, unchanged; 59 kinds and 323 fields): § 2 and § 6 name the release; the element count stays 122, no model file moves, and the 35 warnings by design are unchanged. The ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to 0.19.2's; the build now also writes its build report |
| 0.18 | 2026-11-03 | SWCraft 0.21.0 (contract `12.0.0`, unchanged; 59 kinds and 323 fields): § 2 and § 6 name the release; the element count stays 122, no model file moves, and the 35 warnings by design are unchanged. The ARXML, the Sphinx-Needs export, the build report and the component exports are byte-identical to 0.20.0's; the views differ only by the text a port and a sequence diagram's data message now show of their interface, the drawing unchanged |
| 0.19 | 2026-11-08 | SWCraft 0.22.0 (contract `12.6.0`, a minor over `12.0.0`; 66 kinds and 349 fields): § 2 and § 6 name the release and the contract. The release's new kinds and fields are shown in the story: `BrakeThermalProtection`'s two inter-runnable variables, read and written by its start-up and its 50 ms evaluation, and the exclusive area `ThermalState` the evaluation runs inside; `DiagnosticManager`'s `ProcessDiagnosticEvent` also started by each arrival of a thermal protection event, a data event beside its 100 ms poll, and its variable `LastThermalEvent`, which `ServeSnapshot` reads — no element file added; § 4 tells them and § 5 names the two forms of a variable that exist to show a field. The model holds one requirements source: the trace link demonstration's 46 requirements, their 15 links and `trace-decisions.yaml` leave it, the four external requirements name the requirements team's earlier delivery `0.9` in place of the tag, and § 5's demonstration becomes the requirements exchange beside the model. The element count goes from 122 to 76 (§ 6, without the demonstration's row), the warnings by design from 35 to 4 (§ 2), and § 9 states them as they are. The Sphinx-Needs export is one file, `dist/needs.json`, in place of the RST (§§ 1, 7, 9). Evidence `docs/evidence/20261108-migration-0.22.0.md`. |
| 0.20 | 2026-11-08 | After the maintainer's walk of the requirements exchange: § 5 tells the walkthrough as it now runs. Three links are made by hand and one candidate is rejected; the rest of the links come from a prepared, generated decisions file applied from a copy under `dist/`; the team's sites for 1.0 and 1.1 are carried ready-made. The model, its element count and its warnings by design do not move |
| 0.21 | 2026-11-10 | SWCraft 0.23.0 (contract `12.7.0`, a minor over `12.6.0`; 67 kinds and 359 fields): § 2 and § 6 name the release and the contract. The release's new kind and fields are shown in the story (§ 4): the asynchronous snapshot — `ProcessDiagnosticEvent` writes the snapshot without waiting, with a timeout, and a new runnable of `DiagnosticManager`, `ConfirmSnapshotStored`, started by the write's call-returned event, records whether it was stored, in `Task_100ms` and in the `thermal_status_display` sequence; the storage's error status polled through a second operation of `INvStorage`, `GetErrorStatus`; and `BrakeThermalProtection`'s evaluation reading the brake request and the operating state and writing the permitted brake action implicitly. § 5 names `ConfirmSnapshotStored`'s link to `REQ_BTP_DIAGNOSTICS` and declares the test tables' synthetic test team as demonstration content. A runnable is a member, not an element: the element count stays 76 (§ 6) and the warnings by design stay 4 (§ 2); two rejected changes show the implicit reads the rules refuse. Evidence `docs/evidence/20261110-migration-0.23.0.md`. |
| 0.22 | 2026-11-26 | SWCraft 0.24.0 (contract `12.7.1`, a patch over `12.7.0`; 67 kinds and 359 fields, unchanged): § 2 and § 6 name the release and the contract. No element, member or link changes: the element count stays 76 (§ 6), the warnings by design stay 4 (§ 2), and the generated ARXML, needs file and component exports are byte-identical to 0.23.0's. Evidence: the migration's evidence record. |
| 0.15 | 2026-10-23 | SWCraft 0.19.1 (contract `12.0.0`, unchanged; 59 kinds and 323 fields): § 2 and § 6 name the release; the element count stays 122, no model file moves, and the 35 warnings by design are unchanged. The ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to 0.19.0's |
| 0.14 | 2026-10-23 | SWCraft 0.19.0 (contract `12.0.0`, unchanged; 59 kinds and 323 fields): § 2 and § 6 name the release; the element count stays 122, no model file moves, and the 35 warnings by design are unchanged. The ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to 0.18.1's |
| 0.13 | 2026-10-22 | Requirements traceability: two natural port sites beside a runnable's link — `DiagnosticManager.rThermalProtectionEvent` satisfies `REQ_BTP_DIAGNOSTICS` and `BrakeThermalProtection.pPermittedBrakeAction` satisfies `REQ_SHOWCASE_FEATURE_001`, allocating nothing new — and one stale case: `REQ_BTP_TEMPERATURE_RANGE` goes to version 2 (its description now states that both ends of the range are included) while its three interfaces keep `@1`, so each link needs confirmation (§ 5). check-model's warnings by design go from 32 to 35 (§ 2); the trace link demonstration's 31 unlinked requirements and its walkthrough do not move, and no element is added (the count stays 122) |
| 0.12 | 2026-10-22 | A second task in `P_Vehicle`, `Task_100ms_Low` (period 0.1 s, priority 3, below `Task_100ms`'s 5; `wcet: 1000us`; no runnable mapped), so that moving a runnable from one task to another is shown without crossing a partition: with one task per partition, every such move needed a new coexistence argument. It satisfies `REQ_BTP_CORE_LOAD` like the other two tasks, and `Core0` carries 7 % of its 70 % (§ 5). § 6's tasks go from 2 to 3 and the element count from 121 to 122; check-model's 32 warnings by design are unchanged |
| 0.11 | 2026-10-21 | SWCraft 0.18.1, a patch (contract `12.0.0`, unchanged; 59 kinds and 323 fields): § 2 and § 6 name the release; the element count stays 121, no model file moves, and the 32 warnings by design are unchanged. The ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to 0.18.0's |
| 0.10 | 2026-10-21 | SWCraft 0.18.0, a major (contract `12.0.0`, which retires the rule that a component must satisfy a requirement; 59 kinds and 323 fields): § 2 and § 6 name the release and the contract. The trace link demonstration is added as declared demonstration content (§ 5) and claim 9 (§ 7): 46 synthetic requirements imported by SWCraft, 15 links made by its Apply, eight distractors; the budget gains their row and the element count goes from 75 to 121 (§ 6); § 2 and § 9 state the 32 warnings by design — the stub's and one per requirement the demonstration leaves unlinked — the maintainer's decision of 2026-10-20. The feature's own elements and links do not move; the ARXML and the component exports are byte-identical to 0.17.1's |
| 0.9 | 2026-10-19 | SWCraft 0.17.1, a patch (contract `11.1.0`, unchanged; 59 kinds and 323 fields): § 2 and § 6 name the release; the element count stays 75, no model file moves, and the one warning is still the stub's. The ARXML, the Sphinx-Needs export, the component exports and the views are byte-identical to 0.17.0's |
| 0.8 | 2026-10-19 | SWCraft 0.17.0, a major (contract `11.1.0`, 59 kinds and 323 fields): § 2 and § 6 name the release and the contract, and § 2 states the one warning, the stub's, by design. The external requirements carry a synthetic `revision`, the two baseline requirements their document and baseline, and the safety goal derives from the stub `HAZ_BTP_BRAKE_FADE` (§ 4); the requirements go to 11 and the element count to 75 (§ 6); the RST is the Sphinx-Needs export under `dist/needs/`. Each requirement loses `links` and `status` and gains `version: 1` and a `source` — `external` for the safety goal and the three `req` items, `architecture` for the three `spec` items — and the two decomposed requirements name the safety goal in `derived_from` (§ 4). The trace moves into the elements as `satisfies: [<id>@1]`: on the components, on three ports and two runnables, so every component is allocated exactly the requirements it was before and keeps its level. By the maintainer's decision of 2026-10-16 — no link without something real behind it — three design constraints are added, `source: architecture`, satisfied by the elements whose own values meet them: `REQ_BTP_CORE_LOAD`, `REQ_BTP_TEMPERATURE_RANGE` and `REQ_BTP_EXECUTION_CONTEXT` (§ 4, § 5); the requirements go from 7 to 10 and the element count from 71 to 74 (§ 6). Allocating nothing, `Chassis` satisfies the safety goal, `INvStorage` the diagnostics requirement, and the processor, the cores, the partition, the memory, the tasks and three interfaces the new constraints (§ 5). The ARXML, the component exports and the views are byte-identical to 0.16.2's; the RST loses `:status:`, computes `:links:` from the elements and gains the three constraints |
| 0.7 | 2026-10-15 | SWCraft 0.16.2, a patch (contract `10.1.1`, a prose change to one field's description; 59 kinds and 306 fields, unchanged): § 2 and § 6 name the release and the contract; the element count stays 71 and no model file moves. The ARXML and the RST are byte-identical to 0.16.1's; the diagrams draw the `NvM` stub's port, whose type the model does not declare, as a bare square and its connector to `DiagnosticManager` dashed as not judged, and `rEcuMode`, on the mode-switch stub `IEcuMode`, as a bare square too |
| 0.6 | 2026-10-14 | SWCraft 0.16.1, a patch (contract `10.1.0`, 59 kinds and 306 fields, unchanged): § 2 and § 6 name the release; the element count stays 71. Revision 0.5's two levels on one interface ship on 0.16.1, the first release the showcase is tagged at with them; on it, as on 0.16.0, the ARXML moves only by the element's new description, and the `asil` and the two measures write nothing |
| 0.5 | 2026-10-13 | Two levels on one interface: `IBrakeTemperature.wheelTemperatures` declares `asil: QM` beside the ASIL B `temperature`, and the two rated consumers declare a measure for it; `check-model` stays clean, the ARXML moves only by the element's new description |
| 0.4 | 2026-10-13 | SWCraft 0.16.0 (contract `10.1.0`, 59 kinds and 306 fields): § 2 and § 6 follow the contract; the element count stays 71. The two tasks' budgets carry their unit (`wcet: 6000us`, `wcet: 12000us`), and `EvaluateThermalProtection` declares a budget of its own, `wcet: 3500us` with `wcet_type: gross` — an illustrative allotment like the other resource values, within the 50 ms task's — which the generated ARXML writes as the component's execution-time constraint |
| 0.3 | 2026-10-10 | SWCraft 0.15.0 (contract `9.2.0`, 59 kinds and 304 fields): § 2 and § 6 follow the contract; § 6's budget gains two partitions (`P_Brake`, ASIL B and trusted, on the D-capable core; `P_Vehicle`, ASIL A with a coexistence argument, on the A-capable core) and one connector, 71 elements in all. The brake temperature sensor is placed twice — `FrontBrakeSensor` in the brake subsystem, `RearBrakeSensor` on the chassis feeding the brake controller — so that the 50 ms task and the two brake sequences name an occurrence by its path; the two decomposed requirements write their level as `B(D)`. The task-on-unqualified-core demo becomes the partition-on-unqualified-core demo, the rule the release replaced it with |
| 0.2 | 2026-10-08 | The storefront: `BrakeThermalProtection` committed inside a three-level vehicle; § 2 gains the claim that every model feature SWCraft supports is visible in one coherent model, and § 7 lists it; § 4 describes the vehicle around the feature; § 5 states that the ASIL levels, the measures and the coexistence text are illustrative declarations, not a safety concept, and that the `NvM` stub stands for a platform file the project does not have; § 6's budget is replaced by the storefront's 68 elements, layer by layer, measured on SWCraft 0.14.0 (contract `8.0.0`); § 9 adds the coverage and rejected-change criteria; the retired C4 output is called the diagrams. Before approval, after review: § 4 states that the decomposition's independence is not modelled; § 5 names the implementation-type stub and the two declarations that show a field or keep a rule satisfied; § 6's data-type rule admits the types a rule needs as targets |
