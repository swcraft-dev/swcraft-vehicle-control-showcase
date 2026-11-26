"""The test tables demonstration: every review state, from a test team that reviewed last week's model.

``demos/test-tables.md`` shows SWCraft's test tables with a test team's annotations
folder, ``demos/test-tables/annotations/``, which ``scripts/generate_test_annotations.py``
writes from last week's model (this week's with two recorded edits undone). This test
holds the page's facts:

* with the SWCraft on ``PATH`` (``swcraft_on_path``: skipped without it or with another
  release, a failure under ``SHOWCASE_REQUIRE_SWCRAFT=1``): ``swcraft generate
  test-tables --annotations`` on a copy of the committed model gives each state its count
  and its rows -- ``accepted``, ``rejected``, ``stale``, ``not-reviewed`` and one orphaned
  annotation; two runs write the same bytes; the team's folder is not written; the
  generator's ``--check`` finds the committed folder current;
* without SWCraft: the editor setting names the folder, the folder holds the three
  tables, the page names each row not accepted (the rejected one aside) and the orphan by
  its whole ``row_id`` and quotes the figures (its table and the command line's lines), the
  generator's two edits apply to the committed model and refuse a model they no longer fit
  (a removal that matches no longer, a rename that does not appear once, a name left
  behind), and the generator's ``main`` -- with its SWCraft steps replaced and a fake
  ``swcraft`` -- refuses no ``swcraft`` and another release, reports a difference, writes
  and removes what it no longer writes, leaves operating-system litter alone, and turns a
  failed step into one ``Error:`` line.

What this does not reach: the Test Tables tab in VS Code (its colours, its sub-tabs, the
folder question) -- the page's steps there are the maintainer's look.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate
from swcraft_on_path import fake_swcraft

PROJECT_ROOT = gate.PROJECT_ROOT
ANNOTATIONS = PROJECT_ROOT / "demos" / "test-tables" / "annotations"
GENERATOR = gate.load_script("generate_test_annotations")

TABLES = ("components.csv", "component-placement.csv", "runnable-scheduling.csv")
OUTPUTS = (*TABLES, "orphaned-annotations.csv", "manifest.json")
REJECTED_ROW = "occurrence:Chassis/BrakeSubsystem/BrakeThermalProtection:InitThermalProtection"
#: The page's figures: each table's review states on the committed model, as the run prints them.
EXPECTED_SUMMARY = (
    "components.csv: 7 rows (6 accepted, 1 stale, 0 rejected, 0 not reviewed)",
    "component-placement.csv: 8 rows (8 accepted, 0 stale, 0 rejected, 0 not reviewed)",
    "runnable-scheduling.csv: 10 rows (7 accepted, 0 stale, 1 rejected, 2 not reviewed)",
    "Orphaned annotations: 1",
)
#: Every row that is not ``accepted``, by table: the rows the page names.
EXPECTED_NOT_ACCEPTED = {
    "components.csv": {"component:DiagnosticManager": "stale"},
    "component-placement.csv": {},
    "runnable-scheduling.csv": {
        REJECTED_ROW: "rejected",
        "occurrence:DiagnosticManager:ConfirmSnapshotStored": "not-reviewed",
        "occurrence:InstrumentCluster:UpdateThermalStatus": "not-reviewed",
    },
}
#: The one orphaned annotation: last week's row of the runnable now called UpdateThermalStatus.
ORPHAN_ROW = "occurrence:InstrumentCluster:RefreshThermalStatus"
PAGE = PROJECT_ROOT / "demos" / "test-tables.md"
#: The page's counts table: its title for each table's file.
PAGE_TABLE_TITLES = {
    "components.csv": "Components",
    "component-placement.csv": "Component placement",
    "runnable-scheduling.csv": "Runnable scheduling",
}
SUMMARY_RE = re.compile(
    r"^(?P<table>\S+): (?P<rows>\d+) rows \((?P<accepted>\d+) accepted, (?P<stale>\d+) stale, "
    r"(?P<rejected>\d+) rejected, (?P<not_reviewed>\d+) not reviewed\)$"
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def folder_bytes(folder: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(folder.iterdir()) if path.is_file()}


class TestTheCommittedFolder(unittest.TestCase):
    """What holds without SWCraft: the setting, the folder, the generator's edits."""

    def test_the_editor_setting_names_the_folder_outside_the_model_and_the_outputs(self) -> None:
        settings = json.loads((PROJECT_ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8"))
        folder = settings.get("swcraft.testTables.annotations")
        self.assertEqual("demos/test-tables/annotations", folder)
        self.assertEqual(ANNOTATIONS, PROJECT_ROOT / folder)
        for refused in ("model", "dist", "views"):
            with self.subTest(refused=refused):
                self.assertFalse(ANNOTATIONS.is_relative_to(PROJECT_ROOT / refused))

    def test_the_folder_holds_the_three_tables_as_the_team_handed_them_back(self) -> None:
        self.assertEqual(set(TABLES), set(folder_bytes(ANNOTATIONS)))
        for table in TABLES:
            with self.subTest(table=table):
                data = (ANNOTATIONS / table).read_bytes()
                self.assertNotIn(b"\r", data)
                rows = read_rows(ANNOTATIONS / table)
                self.assertTrue(rows)
                for row in rows:
                    self.assertEqual(GENERATOR.METHODS[table], row["verification_method"])
                    self.assertEqual("no" if row["row_id"] == REJECTED_ROW else "yes", row["accepted"])
                    self.assertTrue(row["facts_hash"], row["row_id"])
                    self.assertEqual("", row["accepted_facts_hash"])

    def test_the_page_names_each_row_not_accepted_by_its_whole_row_id(self) -> None:
        """The rejected row aside, which the page names by its runnable: one form of ``row_id`` throughout."""
        text = PAGE.read_text(encoding="utf-8")
        named = [row_id for rows in EXPECTED_NOT_ACCEPTED.values() for row_id in rows if row_id != REJECTED_ROW]
        for row_id in (*named, ORPHAN_ROW):
            with self.subTest(row_id=row_id):
                self.assertIn(f"`{row_id}`", text)

    def test_the_page_quotes_the_figures(self) -> None:
        """The command line's lines as one block, and the same counts in the page's table."""
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("```text\n" + "\n".join(EXPECTED_SUMMARY) + "\n```", text)
        for line in EXPECTED_SUMMARY[:-1]:
            figures = SUMMARY_RE.match(line)
            assert figures is not None, line
            row = (
                f"| *{PAGE_TABLE_TITLES[figures['table']]}* | {figures['rows']} | {figures['accepted']} | "
                f"{figures['stale']} | {figures['rejected']} | {figures['not_reviewed']} |"
            )
            with self.subTest(table=figures["table"]):
                self.assertIn(row, text)
        self.assertEqual("Orphaned annotations: 1", EXPECTED_SUMMARY[-1])
        self.assertIn("and **one** orphaned annotation", text)

    def test_the_team_reviewed_last_weeks_runnables(self) -> None:
        runnables = {row["runnable"] for row in read_rows(ANNOTATIONS / "runnable-scheduling.csv")}
        self.assertIn("RefreshThermalStatus", runnables)
        self.assertNotIn("UpdateThermalStatus", runnables)
        self.assertNotIn("ConfirmSnapshotStored", runnables)
        components = {row["component"]: row["runnables"] for row in read_rows(ANNOTATIONS / "components.csv")}
        self.assertEqual("2", components["DiagnosticManager"])

    def test_the_two_edits_apply_to_the_committed_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "model"
            shutil.copytree(PROJECT_ROOT / "model", model)
            GENERATOR.last_weeks_model(model)
            task = (model / "tasks" / "Task_100ms.yaml").read_text(encoding="utf-8")
            self.assertIn("runnable: RefreshThermalStatus\n", task)
            self.assertNotIn("ConfirmSnapshotStored", task)
            manager = (model / "swc" / "application" / "DiagnosticManager.yaml").read_text(encoding="utf-8")
            self.assertNotIn("call_returned", manager)
            self.assertIn("- name: ServeSnapshot\n", manager)

    def model_copy(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        model = Path(temporary.name) / "model"
        shutil.copytree(PROJECT_ROOT / "model", model)
        return model

    def test_an_edit_that_no_longer_fits_the_model_is_refused(self) -> None:
        model = self.model_copy()
        GENERATOR.last_weeks_model(model)
        with self.assertRaisesRegex(GENERATOR.AnnotateError, "matched 0 times, not once"):
            GENERATOR.last_weeks_model(model)

    def test_a_rename_that_does_not_appear_once_is_refused(self) -> None:
        model = self.model_copy()
        current, _ = GENERATOR.RENAMED_RUNNABLE
        task = model / GENERATOR.RENAMES[1]
        text = task.read_text(encoding="utf-8")
        task.write_text(text + f"# {current}\n", encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(GENERATOR.AnnotateError, f"model/{GENERATOR.RENAMES[1]}: {current} appears 2 times, not once"):
            GENERATOR.last_weeks_model(model)

    def test_a_name_left_behind_by_the_edits_is_refused(self) -> None:
        model = self.model_copy()
        current, _ = GENERATOR.RENAMED_RUNNABLE
        (model / "interfaces" / "Note.yaml").write_text(f"# {current}\n", encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(GENERATOR.AnnotateError, f"model/interfaces/Note.yaml still names {current}"):
            GENERATOR.last_weeks_model(model)

    def test_a_missing_rejected_row_is_refused(self) -> None:
        text = '"row_id","facts_hash","verification_method","comment","accepted","accepted_facts_hash"\n"x","0","","","",""\n'
        with self.assertRaisesRegex(GENERATOR.AnnotateError, "has no row"):
            GENERATOR.annotate("runnable-scheduling.csv", text)


class TestTheReviewStates(unittest.TestCase):
    """The committed model with the team's folder: every state, as the page says."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.toolchain = gate.toolchain_or_skip()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.project = Path(cls.tmp.name) / "project"
        cls.project.mkdir()
        shutil.copy2(PROJECT_ROOT / "swcraft.yaml", cls.project / "swcraft.yaml")
        shutil.copytree(PROJECT_ROOT / "model", cls.project / "model")
        cls.annotations_before = folder_bytes(ANNOTATIONS)
        cls.first = cls.generate()
        cls.tables = cls.project / "dist" / "test-tables"
        cls.first_bytes = {name: (cls.tables / name).read_bytes() for name in OUTPUTS}
        cls.second = cls.generate()

    @classmethod
    def generate(cls) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [
                str(cls.toolchain.swcraft),
                "generate",
                "test-tables",
                "--project",
                "swcraft.yaml",
                "--annotations",
                str(ANNOTATIONS),
            ],
            cwd=cls.project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=gate.COMMAND_TIMEOUT,
        )
        if completed.returncode != 0:
            raise AssertionError(f"generate test-tables exited {completed.returncode}:\n{completed.stderr}")
        return completed

    def test_the_run_prints_each_tables_states(self) -> None:
        lines = self.first.stdout.splitlines()
        self.assertEqual(list(EXPECTED_SUMMARY), lines[1:])

    def test_every_row_not_accepted_is_one_the_page_names(self) -> None:
        for table in TABLES:
            with self.subTest(table=table):
                states = {row["row_id"]: row["review_state"] for row in read_rows(self.tables / table)}
                not_accepted = {row_id: state for row_id, state in states.items() if state != "accepted"}
                self.assertEqual(EXPECTED_NOT_ACCEPTED[table], not_accepted)

    def test_the_stale_row_keeps_the_teams_verdict(self) -> None:
        rows = {row["row_id"]: row for row in read_rows(self.tables / "components.csv")}
        stale = rows["component:DiagnosticManager"]
        self.assertEqual("3", stale["runnables"])
        self.assertEqual("yes", stale["accepted"])
        self.assertNotEqual(stale["facts_hash"], stale["accepted_facts_hash"])

    def test_the_rejected_row_carries_the_teams_comment(self) -> None:
        rows = {row["row_id"]: row for row in read_rows(self.tables / "runnable-scheduling.csv")}
        rejected = rows[REJECTED_ROW]
        self.assertEqual("no", rejected["accepted"])
        self.assertEqual("not-mapped", rejected["mapping"])
        self.assertEqual(GENERATOR.REJECTED[2], rejected["comment"])

    def test_the_renamed_runnables_annotation_is_the_one_orphan(self) -> None:
        orphans = read_rows(self.tables / "orphaned-annotations.csv")
        self.assertEqual(
            [("runnable-scheduling", ORPHAN_ROW, "yes")],
            [(row["table"], row["row_id"], row["accepted"]) for row in orphans],
        )

    def test_two_runs_write_the_same_bytes(self) -> None:
        self.assertEqual(self.first.stdout, self.second.stdout)
        for name in OUTPUTS:
            with self.subTest(name=name):
                self.assertEqual(self.first_bytes[name], (self.tables / name).read_bytes())

    def test_the_teams_folder_is_not_written(self) -> None:
        self.assertEqual(self.annotations_before, folder_bytes(ANNOTATIONS))

    def test_the_committed_folder_is_the_generators_output(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            code = GENERATOR.main(["--check"])
        self.assertEqual(0, code, stderr.getvalue())


@unittest.skipIf(os.name == "nt", "the fake swcraft is a POSIX script")
class TestTheGenerator(gate.GeneratorCase, unittest.TestCase):
    """``scripts/generate_test_annotations.py``'s ``main``, with its SWCraft steps replaced.

    The refusals of no ``swcraft`` and of another release are :class:`gate.GeneratorCase`'s.
    """

    generator = GENERATOR

    def setUp(self) -> None:
        super().setUp()
        self.annotations = self.output_dir
        self.annotations.mkdir()
        for table in TABLES:
            (self.annotations / table).write_bytes(f"{table}\n".encode())
        self.produced = {table: f"{table}\n".encode() for table in TABLES}

    def main_hooks(self) -> dict[str, Path]:
        return {"annotations_dir": self.annotations}

    def test_check_finds_the_folder_current(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        code, stderr = self.run_main("--check")
        self.assertEqual(0, code, stderr)
        self.assertEqual([(str(self.bin / "swcraft"), self.project)], self.calls)

    def test_check_reports_a_changed_and_an_extra_file_and_writes_nothing(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        self.produced["components.csv"] = b"changed\n"
        (self.annotations / "notes.csv").write_bytes(b"extra\n")
        before = folder_bytes(self.annotations)
        code, stderr = self.run_main("--check")
        self.assertEqual(1, code)
        self.assertEqual("differs from the generator's output: components.csv, notes.csv\n", stderr)
        self.assertEqual(before, folder_bytes(self.annotations))

    def test_a_write_replaces_the_tables_and_removes_what_it_no_longer_writes(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        self.produced["components.csv"] = b"changed\n"
        (self.annotations / "notes.csv").write_bytes(b"extra\n")
        code, stderr = self.run_main()
        self.assertEqual(0, code, stderr)
        self.assertEqual(self.produced, folder_bytes(self.annotations))

    def test_operating_system_litter_is_neither_compared_nor_removed(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        for name in gate.KIT.IGNORED_NAMES:
            (self.annotations / name).write_bytes(b"litter")
        code, stderr = self.run_main("--check")
        self.assertEqual(0, code, stderr)
        code, stderr = self.run_main()
        self.assertEqual(0, code, stderr)
        for name in gate.KIT.IGNORED_NAMES:
            self.assertEqual(b"litter", (self.annotations / name).read_bytes())

    def test_a_failed_step_is_one_error_line(self) -> None:
        fake_swcraft(self.bin, "9.8.7")

        def failing(swcraft: str, project_root: Path) -> dict[str, bytes]:
            raise GENERATOR.AnnotateError("the removal matched 0 times, not once")

        before = folder_bytes(self.annotations)
        self.produce = failing  # type: ignore[method-assign]
        code, stderr = self.run_main()
        self.assertEqual(2, code)
        self.assertEqual("Error: the removal matched 0 times, not once\n", stderr)
        self.assertEqual(before, folder_bytes(self.annotations))


if __name__ == "__main__":
    unittest.main()
