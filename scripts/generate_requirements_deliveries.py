"""Write the requirements team's sources for deliveries 1.0 and 1.1 from one table.

The showcase's requirements exchange (``demos/requirements-exchange.md``) starts from
a synthetic requirements team: a Sphinx-Needs project under
``demos/requirements-exchange/team/`` that writes in its own vocabulary (the need
types ``swreq``, ``sgoal`` and ``test``, the fields ``safety``, ``rev`` and
``document``, the link ``parent``) and delivers its requirements as the
``needs.json`` its build writes. This script writes the team's two sources,
``team/delivery-1.0/index.rst`` and ``team/delivery-1.1/index.rst``; the deliveries
under ``demos/requirements-exchange/deliveries/`` are what ``sphinx-build -b needs``
wrote from them, committed byte for byte (the walkthrough says how).

Delivery 1.0 holds 50 requirements -- 46 software requirements, 42 of them in four
documents and 4 without one, and the brake thermal protection feature's four
external requirements as the model holds them -- and two test cases. Delivery 1.1
is 1.0 with ``SWR-THP-003``'s derating threshold raised (revision 2) and
``SWR-BRK-011`` withdrawn. Everything is synthetic, derived from no real project,
and no id holds ``.``.

Stdlib only and deterministic: UTF-8, LF. ``--check`` writes nothing and exits 1
when a committed source differs from what this script would write. This is
maintainer tooling and is not a kit member.

Usage::

    python scripts/generate_requirements_deliveries.py           # write both sources
    python scripts/generate_requirements_deliveries.py --check   # compare, write nothing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEAM_DIR = PROJECT_ROOT / "demos" / "requirements-exchange" / "team"
SOURCE_NAME = "index.rst"
VERSIONS = ("1.0", "1.1")

#: The software requirements, per document: (id prefix, [(title, text), ...]),
#: numbered from 001 in this order.
DOCUMENTS = {
    "SRS Brake Control": ("BRK", [
        ("Brake request processing", "The brake controller shall process every brake request within one control cycle."),
        ("Brake request input", "The brake controller shall receive the brake request from the pedal interface."),
        ("Permitted brake action applied", "The brake controller shall apply only the permitted brake action."),
        ("Rear brake temperature use", "The brake controller shall read the rear brake temperature before each brake request is processed."),
        ("Brake request rejection", "A brake request that exceeds the permitted brake action shall be limited, not rejected."),
        ("Brake request timing", "Processing of a brake request shall complete within 10 ms."),
        ("Brake request plausibility", "The brake request shall be checked for plausibility against the operating state."),
        ("Brake pressure ramp", "The brake pressure shall ramp up at no more than 200 bar/s."),
        ("Brake controller start", "The brake controller shall be ready to process a brake request 50 ms after start."),
        ("Brake controller degraded mode", "In degraded mode the brake controller shall keep the last permitted brake action."),
        ("Pedal feel", "The pedal feel shall remain constant over the full temperature range."),
        ("Brake request logging", "Each rejected brake request shall be reported to diagnostics."),
    ]),
    "SRS Thermal Protection": ("THP", [
        ("Thermal protection evaluation", "Thermal protection shall be evaluated every 50 ms from the brake temperature."),
        ("Thermal protection initialisation", "Thermal protection shall be initialised at start with a cold brake assumption."),
        ("Permitted action under fade", "When the brake temperature exceeds 600 degC the permitted brake action shall be reduced."),
        ("Thermal protection status", "The thermal protection status shall be published to the instrument cluster."),
        ("Thermal protection event", "A thermal protection event shall be raised when the permitted brake action is reduced."),
        ("Brake temperature publication", "The brake temperature sensor shall publish the brake temperature every 50 ms."),
        ("Brake temperature range", "The brake temperature shall be carried from -40 degC to 1000 degC."),
        ("Operating state use", "Thermal protection shall take the vehicle operating state into account."),
        ("Temperature sensor fault", "A brake temperature sensor fault shall set the thermal protection status to unknown."),
        ("Cooling estimate", "The cooling of the brake disc shall be estimated from vehicle speed."),
        ("Fade warning threshold", "The fade warning threshold shall be calibratable."),
        ("Thermal protection recovery", "Thermal protection shall restore the full permitted brake action below 400 degC."),
    ]),
    "SRS Diagnostics": ("DIA", [
        ("Diagnostic event processing", "The diagnostic manager shall process every thermal protection event."),
        ("Snapshot storage", "On a thermal protection event the diagnostic manager shall store a snapshot in non-volatile storage."),
        ("Snapshot read service", "The diagnostic manager shall serve a read snapshot request from the tester."),
        ("Brake diagnostics publication", "Brake diagnostics shall be published to the instrument cluster."),
        ("ECU mode dependency", "Diagnostic events shall not be stored while the ECU mode is shutdown."),
        ("NvM write retry", "A failed non-volatile storage write shall be retried once."),
        ("Snapshot content", "A snapshot shall hold the brake temperature and the permitted brake action."),
        ("Event debouncing", "A diagnostic event shall be debounced over three evaluation cycles."),
        ("DTC clearing", "Stored trouble codes shall be cleared only by a tester request."),
        ("Diagnostic session", "The extended diagnostic session shall time out after 5 s without a request."),
    ]),
    "SRS Driver Information": ("DRV", [
        ("Thermal status display", "The instrument cluster shall display the thermal protection status."),
        ("Thermal status update", "The instrument cluster shall update the thermal status within 100 ms."),
        ("Brake diagnostics display", "The instrument cluster shall show brake diagnostics to the driver."),
        ("Odometer display", "The instrument cluster shall display the odometer."),
        ("Warning lamp", "A brake fade warning lamp shall be lit while thermal protection is active."),
        ("Display brightness", "Display brightness shall follow the ambient light sensor."),
        ("Operating state publication", "The vehicle state manager shall publish the operating state every 100 ms."),
        ("Operating state start", "The operating state shall be valid 100 ms after ignition on."),
    ]),
}

#: The software requirements in no document, numbered SWR-GEN-001 on.
WITHOUT_DOCUMENT = [
    ("Brake temperature resolution", "The brake temperature shall have a resolution of 0.1 degC."),
    ("Core load limit", "The core load shall stay below 70 percent."),
    ("Service brake availability", "The service brake shall remain available after a single fault."),
    ("Software update", "The software shall be updatable over the diagnostic interface."),
]

#: The brake thermal protection feature's four external requirements, exactly as
#: the model holds them (title, description, document, revision, ASIL, parent);
#: the team delivered them before, at 0.9.
FEATURE = [
    {
        "id": "REQ_SHOWCASE_BASELINE_001", "type": "swreq",
        "title": "Provide typed context signals",
        "content": "The architecture provides typed context signals for the showcase.",
        "document": "BL-SHOWCASE-001", "rev": "3",
    },
    {
        "id": "REQ_SHOWCASE_BASELINE_002", "type": "swreq",
        "title": "Provide diagnostic and display endpoints",
        "content": "The architecture provides diagnostic and display endpoints for the showcase.",
        "document": "BL-SHOWCASE-001", "rev": "2",
    },
    {
        "id": "REQ_SHOWCASE_FEATURE_001", "type": "swreq",
        "title": "Brake thermal protection evaluates and publishes",
        "content": (
            "The brake thermal protection evaluates the brake temperature and publishes the permitted brake "
            "action, its status and its events."
        ),
        "rev": "5",
    },
    {
        "id": "REQ_BTP_SAFETY_GOAL", "type": "sgoal",
        "title": "Prevent brake fade from thermal overload",
        "content": (
            "Safety goal: the brake system shall not lose braking capability because the brakes overheat. "
            "Decomposed into REQ_BTP_DECOMP_MAIN and REQ_BTP_DECOMP_MONITOR, each ASIL B(D). Illustrative."
        ),
        "rev": "4", "safety": "D", "parent": "HAZ_BTP_BRAKE_FADE",
    },
]

#: The team's own test cases: a need type the architect's mapping ignores.
TESTS = [
    {
        "id": "TC-BRK-001", "type": "test", "title": "Brake request processing test",
        "content": "Apply a brake request and check that it is processed within one control cycle.",
        "rev": "1",
    },
    {
        "id": "TC-THP-001", "type": "test", "title": "Fade derating test",
        "content": "Heat the brake above the derating threshold and check that the permitted brake action is reduced.",
        "rev": "1",
    },
]

#: Each later delivery against 1.0: the changed requirements' fields, and the withdrawn ones.
CHANGES: dict[str, tuple[dict[str, dict[str, str]], tuple[str, ...]]] = {
    "1.1": (
        {
            "SWR-THP-003": {
                "content": "When the brake temperature exceeds 650 degC the permitted brake action shall be reduced.",
                "rev": "2",
            },
        },
        ("SWR-BRK-011",),
    ),
}

#: The section a need without a document is written under, and the test cases' section.
NO_DOCUMENT_SECTION = "Requirements without a document"
TESTS_SECTION = "Test cases"


def software_requirements() -> list[dict[str, str]]:
    """The 46 software requirements of delivery 1.0, in document order."""
    needs = []
    for document, (prefix, items) in DOCUMENTS.items():
        for number, (title, content) in enumerate(items, 1):
            needs.append({
                "id": f"SWR-{prefix}-{number:03d}", "type": "swreq", "title": title, "content": content,
                "document": document, "rev": "1",
            })
    for number, (title, content) in enumerate(WITHOUT_DOCUMENT, 1):
        needs.append({"id": f"SWR-GEN-{number:03d}", "type": "swreq", "title": title, "content": content, "rev": "1"})
    return needs


def delivery(version: str) -> list[dict[str, str]]:
    """Every need of one delivery, in source order: the requirements, then the test cases.

    Each need is a dict of ``id``, ``type``, ``title``, ``content``, ``rev`` and, where
    it has one, ``document``, ``safety`` and ``parent``.
    """
    if version not in VERSIONS:
        raise ValueError(f"no delivery {version!r}; the deliveries are {', '.join(VERSIONS)}")
    needs = [dict(need) for need in software_requirements() + FEATURE + TESTS]
    changed, withdrawn = CHANGES.get(version, ({}, ()))
    needs = [need for need in needs if need["id"] not in withdrawn]
    for need in needs:
        need.update(changed.get(need["id"], {}))
    return needs


def heading(text: str, underline: str) -> list[str]:
    return [text, underline * len(text), ""]


def directive(need: dict[str, str]) -> list[str]:
    lines = [f".. {need['type']}:: {need['title']}", f"   :id: {need['id']}", "   :status: approved"]
    for option in ("document", "rev", "safety", "parent"):
        if option in need:
            lines.append(f"   :{option}: {need[option]}")
    return lines + ["", f"   {need['content']}", ""]


def source(version: str) -> str:
    """The team's ``index.rst`` of one delivery."""
    lines = [
        ".. Written by scripts/generate_requirements_deliveries.py; edit the table there, not this file.",
        "",
        *heading(f"Vehicle control software requirements, delivery {version}", "="),
        "The requirements team's software requirements for the vehicle control architecture.",
        "Synthetic, derived from no real project.",
        "",
    ]
    sections: dict[str, list[dict[str, str]]] = {}
    for need in delivery(version):
        if need["type"] == "test":
            section = TESTS_SECTION
        else:
            section = need.get("document", NO_DOCUMENT_SECTION)
        sections.setdefault(section, []).append(need)
    order = [s for s in sections if s not in (NO_DOCUMENT_SECTION, TESTS_SECTION)]
    order += [s for s in (NO_DOCUMENT_SECTION, TESTS_SECTION) if s in sections]
    for section in order:
        lines += heading(section, "-")
        for need in sections[section]:
            lines += directive(need)
    # The architect's own requirements, once the architecture is handed over: conf.py sets the
    # ``swcraft`` tag when swcraft/needs.json is there, so a delivery built without it shows the
    # team's requirements alone. The architecture's elements are not listed: each is already
    # shown, and opens, under *satisfied by* of the requirement it satisfies.
    lines += [".. only:: swcraft", ""]
    lines += [f"   {line}" if line else "" for line in heading("Architecture requirements (SWCraft)", "-")]
    lines += [
        "   .. needtable::",
        '      :filter: is_external and type in ["arch_req", "arch_spec"]',
        '      :columns: id, title, derived_from as "Derived from", satisfies_back as "Satisfied by", satisfies_unconfirmed_back as "Satisfied by (unconfirmed)"',
        "      :style: table",
    ]
    return "\n".join(lines) + "\n"


def outputs() -> dict[str, str]:
    """Each source's path, relative to the team's folder, and its text."""
    return {f"delivery-{version}/{SOURCE_NAME}": source(version) for version in VERSIONS}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare the committed sources, write nothing")
    args = parser.parse_args(argv)
    differing = []
    for relative, text in outputs().items():
        path = TEAM_DIR / relative
        if args.check:
            # Bytes, not text: reading text would turn a CRLF file into the LF one written.
            if not path.is_file() or path.read_bytes() != text.encode("utf-8"):
                differing.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            shown = path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path
            print(f"wrote {shown.as_posix()}")
    if differing:
        print(f"differs from the generator's output: {', '.join(differing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
