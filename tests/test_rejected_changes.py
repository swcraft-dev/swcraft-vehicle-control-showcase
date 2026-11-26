"""The rejected-change demonstrations: each edit breaks exactly one rule.

``demos/rejected-changes.json`` lists edits a presenter applies by hand to show
that ``swcraft check-model`` refuses a model that breaks a rule. For each entry
this test copies ``swcraft.yaml`` and ``model/`` into a temporary directory,
applies the edits there, and asserts:

* ``swcraft check-model`` exits 1;
* the set of rule ids the validator records on the copy **equals**
  ``{entry.rule}`` -- the rule id is the key, never the message;
* ``entry.rule`` is one of the installed contract's rule ids;
* the CLI prints exactly ``errorLines`` ``ERROR:`` lines, and each ``expect``
  substring appears in its output, so the lines the README quotes cannot go
  stale unnoticed.

The same is done once inside the **colleague kit**, built from this repository
and unpacked: the kit's model passes and one demo is refused by its rule there.

The shape tests run on any Python: unique slugs, a non-empty ``expect``, each
edit exactly one of ``find``/``create``, a ``find`` that differs from its
``replace``, every path inside ``model/``, every ``create`` target absent with
its directory present, and every ``find`` matching exactly once -- counted on
the text as the entry's earlier edits leave it. The README's table is held to
the file: one row per entry, the rule, the paths and the quoted texts.

The committed model's own exit 0 and empty rule set are asserted once, by the
coverage gate. Without the pinned SWCraft on PATH the toolchain tests skip;
``SHOWCASE_REQUIRE_SWCRAFT=1`` makes that a failure (``swcraft_on_path``).

What this does not reach: the messages are the installed release's wording,
which is not a contract; a reworded message fails here and is updated in the
same change, and it can never make a wrong rule pass.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import model_coverage_probe as probe
import swcraft_on_path as gate

KIT = gate.load_script("build_colleague_kit")

DEMOS = gate.PROJECT_ROOT / "demos" / "rejected-changes.json"
DEMOS_README = gate.PROJECT_ROOT / "demos" / "README.md"
ENTRY_KEYS = {"slug", "rule", "title", "explanation", "edits", "errorLines", "expect"}
RULE_RE = re.compile(r"^[a-z][a-z-]*(?:\.[a-z][a-z-]*)+$")
#: The nine demonstrations the README's table promises (one row each, held by
#: ``test_the_readme_table_states_each_entry``).
DEMO_COUNT = 9
#: The demo the kit test applies inside the unpacked kit.
KIT_DEMO = "partition-on-unqualified-core"


def load_entries() -> list[dict[str, Any]]:
    return json.loads(DEMOS.read_text(encoding="utf-8"))["entries"]


def apply_edits(project: Path, edits: list[dict[str, str]]) -> None:
    """Apply one entry's edits to the copy rooted at ``project`` (their shape is ``TestShape``'s)."""
    for edit in edits:
        target = project / edit["path"]
        if "create" in edit:
            target.write_text(edit["create"], encoding="utf-8", newline="\n")
        else:
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace(edit["find"], edit["replace"]), encoding="utf-8", newline="\n")


def error_lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip().startswith("ERROR:")]


def readme_rows() -> dict[str, list[str]]:
    """The demo table of ``demos/README.md``: slug -> its four cells."""
    rows = {}
    for line in DEMOS_README.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4 and (match := re.fullmatch(r"`([a-z-]+)`", cells[0])):
            rows[match.group(1)] = cells
    return rows


class TestShape(unittest.TestCase):
    """The file's own shape, on the committed model, with no toolchain."""

    def test_entries_are_well_formed(self) -> None:
        entries = load_entries()
        self.assertEqual(DEMO_COUNT, len(entries))
        slugs = [entry["slug"] for entry in entries]
        self.assertEqual(len(slugs), len(set(slugs)), "slugs must be unique")
        for entry in entries:
            with self.subTest(slug=entry["slug"]):
                self.assertEqual(ENTRY_KEYS, set(entry))
                self.assertRegex(entry["rule"], RULE_RE)
                self.assertTrue(entry["expect"], "expect must not be empty")
                self.assertTrue(all(isinstance(line, str) and line for line in entry["expect"]))
                self.assertIsInstance(entry["errorLines"], int)
                self.assertGreaterEqual(entry["errorLines"], len(entry["expect"]))
                self.assertTrue(entry["edits"])
                texts: dict[str, str] = {}  # each file as the entry's earlier edits leave it
                for edit in entry["edits"]:
                    self.assertTrue(("find" in edit) != ("create" in edit), "an edit is exactly one of find/create")
                    expected_keys = {"path", "create"} if "create" in edit else {"path", "find", "replace"}
                    self.assertEqual(expected_keys, set(edit))
                    path = PurePosixPath(edit["path"])
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn("..", path.parts)
                    self.assertEqual("model", path.parts[0])
                    committed = gate.PROJECT_ROOT / edit["path"]
                    if "create" in edit:
                        self.assertNotIn(edit["path"], texts, f"{edit['path']} is created twice")
                        self.assertFalse(committed.exists(), f"{edit['path']} must not exist")
                        self.assertTrue(committed.parent.is_dir(), f"{path.parent} must exist")
                        texts[edit["path"]] = edit["create"]
                        continue
                    self.assertNotEqual(edit["find"], edit["replace"])
                    if edit["path"] not in texts:
                        texts[edit["path"]] = committed.read_text(encoding="utf-8")
                    count = texts[edit["path"]].count(edit["find"])
                    self.assertEqual(1, count, f"{edit['path']}: find must occur exactly once")
                    texts[edit["path"]] = texts[edit["path"]].replace(edit["find"], edit["replace"])

    def test_the_readme_table_states_each_entry(self) -> None:
        entries = load_entries()
        rows = readme_rows()
        self.assertEqual([entry["slug"] for entry in entries], list(rows))
        for entry in entries:
            with self.subTest(slug=entry["slug"]):
                _, rule, change, says = rows[entry["slug"]]
                self.assertEqual(f"`{entry['rule']}`", rule)
                quoted = re.findall(r"`([^`]+)`", says)
                self.assertTrue(quoted, "the last column quotes the message")
                self.assertIn(quoted[0], entry["expect"][0])
                paths = {edit["path"] for edit in entry["edits"]}
                edited = "\n".join(value for edit in entry["edits"] for key, value in edit.items() if key != "path")
                context = "\n".join(
                    (gate.PROJECT_ROOT / edit["path"]).read_text(encoding="utf-8")
                    for edit in entry["edits"]
                    if "find" in edit
                )
                for token in re.findall(r"`([^`]+)`", change):
                    if token.startswith("model/"):
                        self.assertIn(token, paths)
                    elif token not in edited and token not in context:
                        # ``Component.port``: both names occur, on lines of their own.
                        parts = token.split(".")
                        self.assertTrue(
                            len(parts) == 2 and all(part in edited or part in context for part in parts),
                            f"{token!r} occurs neither in the edits nor in the file they change",
                        )


def _project_copy(scratch: Path) -> Path:
    shutil.copy2(gate.MANIFEST, scratch / "swcraft.yaml")
    shutil.copytree(gate.MODEL_ROOT, scratch / "model")
    return scratch


class TestEachEditBreaksExactlyItsRule(unittest.TestCase):
    """One subtest per entry, against the pinned installation."""

    def assert_refused_by_exactly(self, toolchain: gate.Toolchain, project: Path, entry: dict[str, Any]) -> None:
        completed = gate.check_model(toolchain, project / "swcraft.yaml")
        output = completed.stdout + completed.stderr
        self.assertEqual(1, completed.returncode, output)
        self.assertEqual([entry["rule"]], gate.rule_records(toolchain, project / "model"))
        self.assertEqual(entry["errorLines"], len(error_lines(output)), output)
        for line in entry["expect"]:
            self.assertIn(line, output)

    def test_each_entry_is_refused_by_exactly_its_rule(self) -> None:
        toolchain = gate.toolchain_or_skip()
        contract_rules = {probe.bare(rule["id"]) for rule in gate.dump_contract(toolchain)["rules"]}
        for entry in load_entries():
            with self.subTest(slug=entry["slug"]):
                self.assertIn(entry["rule"], contract_rules)
                with tempfile.TemporaryDirectory() as scratch:
                    project = _project_copy(Path(scratch))
                    apply_edits(project, entry["edits"])
                    self.assert_refused_by_exactly(toolchain, project, entry)

    def test_inside_the_unpacked_kit_the_model_passes_and_a_demo_is_refused(self) -> None:
        toolchain = gate.toolchain_or_skip()
        members = KIT.build_members(gate.PROJECT_ROOT, KIT.OVERLAY_DIR, KIT.INSTALL_PAGE, toolchain.version)
        entry = next(entry for entry in load_entries() if entry["slug"] == KIT_DEMO)
        with tempfile.TemporaryDirectory() as scratch:
            with zipfile.ZipFile(io.BytesIO(KIT.zip_bytes(members))) as archive:
                archive.extractall(scratch)
            project = Path(scratch) / KIT.KIT_NAME
            json.loads((project / "demos" / "rejected-changes.json").read_text(encoding="utf-8"))
            clean = gate.check_model(toolchain, project / "swcraft.yaml")
            self.assertEqual(0, clean.returncode, clean.stdout + clean.stderr)
            apply_edits(project, entry["edits"])
            self.assert_refused_by_exactly(toolchain, project, entry)


if __name__ == "__main__":
    unittest.main()
