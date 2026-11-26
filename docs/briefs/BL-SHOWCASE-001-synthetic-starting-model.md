# BL-SHOWCASE-001 — Synthetic Starting Model Contract

| Field | Value |
|---|---|
| Document ID | BL-SHOWCASE-001 |
| Revision | 0.2 |
| Status | **Historical** — the baseline this contract defines is the tag `showcase-baseline-001`; it is no longer the model on `main` (revision 0.2, 2026-10-08) |
| Owner | Vehicle Control Showcase project lead |
| Parent scope | FB-SHOWCASE-001 |
| Created | 2026-08-15 |

> **Status, revision 0.2 (2026-10-08).** The baseline defined below is preserved as the tag
> `showcase-baseline-001`, which predates later SWCraft releases and does not load at the release
> this project pins. The model on `main` is the storefront of FB-SHOWCASE-001 revision 0.2, which
> commits `BrakeThermalProtection` and places it in a three-level vehicle. This contract is kept as
> the record of the starting point; nothing else in it changed.

## 1. Purpose

Define the exact small model that exists immediately before the live `BrakeThermalProtection`
change. This contract makes the starting point reviewable independently of both AI prompts and the
final feature result.

The baseline provides demonstration context only. It is not a partial production brake-system
architecture and shall not grow to cover automotive concerns outside FB-SHOWCASE-001.

## 2. Baseline Inventory

The starting model contains exactly:

| Model item | Baseline count | Feature-brief maximum |
|---|---:|---:|
| SWCs | 5 | 6 |
| Primitive data types | 2 | Smallest coherent set |
| Sender-receiver interfaces | 6 | 8 |
| Connectors | 0 | 8 |
| Tasks | 2 | 3 |
| Demonstration sequences | 1 | 2 |
| Requirements | 2 | 8 |
| CPU resources | 1 | Not budgeted |
| Memory resources | 1 | Not budgeted |

There are no composites, client-server interfaces, deployment mappings, variants, calibrations,
or production diagnostic definitions.

## 3. Data Types and Interfaces

Two generic primitive data types are sufficient:

| Data type | Purpose |
|---|---|
| `uint8` | Synthetic state, status, and event values |
| `uint16` | Synthetic temperature and brake-action values |

The model does not attach physical units, ranges, scaling, or calibration semantics.

| Interface | Element | Type | Baseline provider | Baseline consumer |
|---|---|---|---|---|
| `IBrakeTemperature` | `value` | `uint16` | `BrakeTemperatureSensor` | None |
| `IBrakeRequest` | `value` | `uint16` | `BrakeController` | None |
| `IVehicleOperatingState` | `value` | `uint8` | `VehicleStateManager` | None |
| `IPermittedBrakeAction` | `value` | `uint16` | None | `BrakeController` |
| `IThermalProtectionStatus` | `value` | `uint8` | None | `InstrumentCluster` |
| `IThermalProtectionEvent` | `value` | `uint8` | None | `DiagnosticManager` |

Unconnected ports are deliberate at baseline. They expose the exact typed endpoints that the
demonstrated feature will connect; they do not represent an incomplete production integration.

## 4. Components and Runnables

| SWC | Ports | Runnable | Synthetic responsibility |
|---|---|---|---|
| `BrakeTemperatureSensor` | provide `pBrakeTemperature` | `PublishBrakeTemperature` | Publish an already measured value |
| `BrakeController` | provide `pBrakeRequest`; require `rPermittedBrakeAction` | `ProcessBrakeRequest` | Publish a request and receive a permitted value |
| `VehicleStateManager` | provide `pOperatingState` | `PublishOperatingState` | Publish an illustrative operating state |
| `DiagnosticManager` | require `rThermalProtectionEvent` | `ProcessDiagnosticEvent` | Receive an illustrative event |
| `InstrumentCluster` | require `rThermalProtectionStatus` | `UpdateThermalStatus` | Receive an illustrative display status |

Each SWC has one runnable. No runnable contains algorithm, pseudo-code, calibration, or safety
logic.

## 5. Execution Context

The periods and resource numbers are intentionally synthetic:

- `Task_50ms` contains the three context-provider runnables;
- `Task_100ms` contains the diagnostic and display runnables;
- `baseline_50ms_cycle` shows only the three `Task_50ms` steps;
- `Core0` exists to exercise CPU budget reporting;
- `RAM` exists to exercise memory budget reporting.

Values shall be simple, internally consistent, and leave visible headroom for the demonstrated
feature. They are presentation inputs, not timing analysis or resource estimates.

## 6. Requirements and Trace Scope

The baseline contains two synthetic requirements:

| Requirement | Intent | Links |
|---|---|---|
| `REQ_SHOWCASE_BASELINE_001` | Provide the three typed context signals used by the future change | `BrakeTemperatureSensor`, `BrakeController`, `VehicleStateManager` |
| `REQ_SHOWCASE_BASELINE_002` | Provide typed diagnostic and display endpoints for the future change | `DiagnosticManager`, `InstrumentCluster` |

This is enough to exercise requirement-to-architecture traceability and ensure that every baseline
SWC has a requirement link. It is not a system or software requirements specification.

## 7. Expected Feature Boundary

The later reviewed feature change may:

- add `BrakeThermalProtection` as the sixth SWC;
- add its typed require and provide ports;
- add up to six connectors between the already defined endpoints;
- add feature requirements and their trace links;
- add the feature runnable to an existing task;
- update or add one demonstration sequence;
- add illustrative resource consumption within existing headroom.

It shall not rename or delete a baseline element. The exact accepted delta is frozen separately
before the AI scenario is authored.

## 8. Materialization Workflow

The showcase shall be authored as an external SWCraft project. Instructions may be taken from:

- released SWCraft user and concept documentation;
- the installed CLI and its `--help` output;
- the generated workspace instructions;
- the installed MCP tool descriptions exposed to `SWCraft Architect`.

SWCraft product source code, internal schemas, and tests shall not be consulted to discover how a
user is expected to create or change the model. If the documented surface is insufficient or
ambiguous, materialization pauses at that step and the missing information is recorded as a
SWCraft documentation gap.

Representative day-to-day actions shall be performed by the project owner through the supported
user workflow. These include creating model elements, approving bounded changes, running model
checks, and reviewing semantic diffs. Assistance may prepare the bounded input, state the expected
result, and analyze the observed output, but shall not silently replace the user interaction that
the showcase is intended to evaluate.

AI-assisted model changes shall go through `SWCraft Architect` and the `swcraft` MCP server. They
shall not be implemented by directly editing files under `model/`.

## 9. Baseline Acceptance Criteria

The baseline is accepted when:

- the inventory matches this contract exactly;
- every SWC is linked from one of the two baseline requirements;
- no connector or `BrakeThermalProtection` element exists;
- `swcraft check-model` passes;
- the canonical build generates ARXML, C4, and RST successfully;
- structural or XSD validation mode is reported honestly;
- a repeated clean build produces the same output hashes;
- generated outputs and local evidence remain untracked;
- no model description implies production suitability or safety completeness.

Once these criteria pass, baseline modeling stops. Additional context requires revision of this
contract and a corresponding observable SWCraft demonstration need.
