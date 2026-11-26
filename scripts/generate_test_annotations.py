"""Write the test team's annotations of the showcase's test tables, from last week's model.

The test tables demonstration (``demos/test-tables.md``) needs a test team that exists:
one that reviewed the tables of an earlier model and handed its folder back, so that the
committed model shows every review state SWCraft computes. This script makes that team's
folder, ``demos/test-tables/annotations/``, from the installed SWCraft (``swcraft`` on
``PATH``) and the committed project, on a temporary copy:

1. the project's ``swcraft.yaml`` and ``model/`` are copied to a temporary folder;
2. the copy is turned back into **last week's model** by two recorded edits
   (:data:`REMOVALS` and :data:`RENAMES`), each of which must apply where it is recorded,
   or the script refuses: ``ConfirmSnapshotStored`` removed from ``DiagnosticManager``
   with its event, its mapping into ``Task_100ms`` and its step of
   ``thermal_status_display``; and ``InstrumentCluster``'s ``UpdateThermalStatus`` under
   its earlier name ``RefreshThermalStatus``, every reference renamed with it;
3. ``swcraft generate test-tables`` writes the copy's tables, and the team's columns are
   filled in them as a test team fills them in a spreadsheet tool: every row accepted
   with the table's verification method (:data:`METHODS`), except the one row the team
   rejected, with its comment (:data:`REJECTED`). The three tables are written as the
   team hands them back: SWCraft's columns as generated, the team's filled in.

Against the committed model this folder gives every state: ``accepted``; ``rejected``
(:data:`REJECTED`); ``stale`` (``DiagnosticManager``'s component row: a component row
records its runnable *count*, two last week and three now); ``not-reviewed`` (the rows of
``ConfirmSnapshotStored`` and of ``UpdateThermalStatus``, new since); and one orphaned
annotation (the ``RefreshThermalStatus`` row, whose identity no longer exists). The
states are held by ``tests/test_test_tables.py``. No git history is read: last week's
model is this week's with the two edits undone.

``--check`` writes nothing and exits 1 when a committed file differs, byte for byte, from
what this script would write; a write replaces the folder's files and removes a file the
script no longer writes. Operating-system litter (``scripts/repository_rules.py``'s ``IGNORED_NAMES``) is
neither compared nor removed. It needs SWCraft at the pinned release
(``scripts/pinned_swcraft.py``, shared with the requirements exchange's generator); a
failure of any step is one ``Error:`` line and exit 2. Maintainer tooling, not a kit
member. Run it again when the model changes and ``tests/test_test_tables.py`` fails.

Usage::

    python scripts/generate_test_annotations.py
    python scripts/generate_test_annotations.py --check
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from pinned_swcraft import ToolchainError, copy_project, run_command, run_generator
from repository_rules import IGNORED_NAMES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS_DIR = PROJECT_ROOT / "demos" / "test-tables" / "annotations"
#: What the temporary copy holds: the manifest and the model, nothing else is read.
COPIED = ("swcraft.yaml", "model")
TABLES = ("components.csv", "component-placement.csv", "runnable-scheduling.csv")
TEAM_COLUMNS = ("verification_method", "comment", "accepted", "accepted_facts_hash")

#: The runnable added this week: removed, with its mapping and its sequence step.
ADDED_RUNNABLE = "ConfirmSnapshotStored"
#: The runnable renamed this week: ``(this week's name, last week's name)``.
RENAMED_RUNNABLE = ("UpdateThermalStatus", "RefreshThermalStatus")

#: A list item naming the added runnable of ``DiagnosticManager``: its mapping into the task,
#: and its step of the sequence (with the step's note).
ADDED_ITEM = re.compile(rf"^- swc: DiagnosticManager\n  runnable: {ADDED_RUNNABLE}\n(?:  .*\n)*", re.M)
#: The removals: each pattern must match exactly once in its model file.
REMOVALS = (
    # The runnable, up to the next runnable of the list.
    ("swc/application/DiagnosticManager.yaml", re.compile(rf"^- name: {ADDED_RUNNABLE}\n(?:  .*\n)+", re.M)),
    ("tasks/Task_100ms.yaml", ADDED_ITEM),
    ("sequences/thermal_status_display.yaml", ADDED_ITEM),
)
#: The rename: these files name the runnable, and after it no model file does.
RENAMES = (
    "swc/application/InstrumentCluster.yaml",
    "tasks/Task_100ms.yaml",
    "sequences/thermal_status_display.yaml",
)

#: How the team verifies the rows of each table.
METHODS = {
    "components.csv": "Review of the component's configuration against the architecture",
    "component-placement.csv": "Inspection of the generated RTE and OS configuration",
    "runnable-scheduling.csv": "Timing measurement on the target",
}
#: The one row the team rejected, and why.
REJECTED = (
    "runnable-scheduling.csv",
    "occurrence:Chassis/BrakeSubsystem/BrakeThermalProtection:InitThermalProtection",
    "Mapped to no task, so there is no schedule to verify; we need the task that runs its init event "
    "before we can accept it.",
)


class AnnotateError(ToolchainError):
    """A step of this generator failed; the message is printed as it is."""


def last_weeks_model(model_root: Path) -> None:
    """Undo this week's two changes in the model copy at *model_root*, or refuse."""
    for relative, pattern in REMOVALS:
        path = model_root / relative
        text = path.read_text(encoding="utf-8")
        text, count = pattern.subn("", text)
        if count != 1:
            raise AnnotateError(f"model/{relative}: the removal of {ADDED_RUNNABLE} matched {count} times, not once")
        path.write_text(text, encoding="utf-8", newline="\n")
    current, earlier = RENAMED_RUNNABLE
    word = re.compile(rf"\b{current}\b")
    for relative in RENAMES:
        path = model_root / relative
        text, count = word.subn(earlier, path.read_text(encoding="utf-8"))
        if count != 1:
            raise AnnotateError(f"model/{relative}: {current} appears {count} times, not once")
        path.write_text(text, encoding="utf-8", newline="\n")
    for path in sorted(model_root.rglob("*.yaml"), key=lambda p: p.as_posix()):
        text = path.read_text(encoding="utf-8")
        for name in (ADDED_RUNNABLE, current):
            if re.search(rf"\b{name}\b", text):
                raise AnnotateError(f"model/{path.relative_to(model_root).as_posix()} still names {name}")


def csv_text(header: list[str], rows: list[dict[str, str]]) -> str:
    """CSV as SWCraft writes it: every field quoted, a line feed after every line."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([row[column] for column in header])
    return buffer.getvalue()


def annotate(table: str, text: str) -> str:
    """The generated *table*'s *text* with the team's columns filled."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    header = list(reader.fieldnames or [])
    missing = [column for column in ("row_id", "facts_hash", *TEAM_COLUMNS) if column not in header]
    if missing:
        raise AnnotateError(f"{table} has no column {', '.join(missing)}")
    rows = list(reader)
    rejected_table, rejected_row, rejected_comment = REJECTED
    found = False
    for row in rows:
        row["verification_method"] = METHODS[table]
        if (table, row["row_id"]) == (rejected_table, rejected_row):
            row["accepted"], row["comment"] = "no", rejected_comment
            found = True
        else:
            row["accepted"] = "yes"
    if table == rejected_table and not found:
        raise AnnotateError(f"{table} has no row {rejected_row} for the team to reject")
    return csv_text(header, rows)


def outputs(swcraft: str, project_root: Path = PROJECT_ROOT) -> dict[str, bytes]:
    """The three annotated tables of last week's model, by file name."""
    with tempfile.TemporaryDirectory() as temporary:
        copy = Path(temporary) / "project"
        copy.mkdir()
        copy_project(project_root, copy, COPIED)
        last_weeks_model(copy / "model")
        completed = run_command(
            [swcraft, "generate", "test-tables", "--project", "swcraft.yaml"], "swcraft generate test-tables", cwd=copy
        )
        if completed.returncode != 0:
            raise AnnotateError(
                f"swcraft generate test-tables exited {completed.returncode} on last week's model: "
                f"{completed.stderr.strip()}"
            )
        tables = copy / "dist" / "test-tables"
        files = {}
        for table in TABLES:
            try:
                text = (tables / table).read_text(encoding="utf-8")
            except OSError as error:
                raise AnnotateError(f"{table} could not be read: {error}") from None
            files[table] = annotate(table, text).encode("utf-8")
        return files


def committed(annotations_dir: Path) -> dict[str, bytes]:
    """The committed files of the annotations folder, by name; operating-system litter is no file of it."""
    if not annotations_dir.is_dir():
        return {}
    return {
        path.name: path.read_bytes()
        for path in annotations_dir.iterdir()
        if path.is_file() and path.name not in IGNORED_NAMES
    }


def write_annotations(produced: dict[str, bytes], annotations_dir: Path) -> None:
    """*produced* written into *annotations_dir*; a file it no longer writes is removed, litter is left alone."""
    present = committed(annotations_dir)
    annotations_dir.mkdir(parents=True, exist_ok=True)
    for name in set(present) - set(produced):
        (annotations_dir / name).unlink()
    for name, data in produced.items():
        (annotations_dir / name).write_bytes(data)


def main(
    argv: list[str] | None = None,
    *,
    produce: Callable[[str, Path], dict[str, bytes]] = outputs,
    annotations_dir: Path = ANNOTATIONS_DIR,
    project_root: Path = PROJECT_ROOT,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare the committed files, write nothing")
    args = parser.parse_args(argv)

    def differing(produced: dict[str, bytes]) -> list[str]:
        present = committed(annotations_dir)
        return sorted(name for name in set(produced) | set(present) if produced.get(name) != present.get(name))

    return run_generator(
        project_root=project_root,
        output_dir=annotations_dir,
        outputs="the tables the annotations are written over",
        check=args.check,
        produce=lambda swcraft: produce(swcraft, project_root),
        differing=differing,
        write=lambda produced: write_annotations(produced, annotations_dir),
    )


if __name__ == "__main__":
    sys.exit(main())
