"""The requirements exchange's data: the team's sources, its two deliveries, the mapping, the answer key.

``demos/requirements-exchange/`` holds a synthetic requirements team's Sphinx-Needs
project (``team/``) whose two sources ``scripts/generate_requirements_deliveries.py``
writes from one table, and the two ``needs.json`` deliveries ``sphinx-build -b needs``
wrote from them with the team's pinned Sphinx-Needs, committed byte for byte. **No test
runs Sphinx**: these tests hold the committed deliveries to the generator's table, the
team's ``conf.py`` to SWCraft's published declarations, and the answer key to delivery
1.0.

The toolchain test imports both deliveries with the installed SWCraft on a temporary
copy of ``swcraft.yaml`` and ``model/`` and holds the import's summary lines, which
the walkthrough quotes. Without the pinned SWCraft on PATH it skips;
``SHOWCASE_REQUIRE_SWCRAFT=1`` makes that a failure (``swcraft_on_path``).
"""

from __future__ import annotations

import contextlib
import functools
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate
from test_model_coverage import toolchain

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCHANGE = PROJECT_ROOT / "demos" / "requirements-exchange"
TEAM = EXCHANGE / "team"
MAPPING = EXCHANGE / "team.needs-mapping.yaml"
GENERATOR = PROJECT_ROOT / "scripts" / "generate_requirements_deliveries.py"
REQUIREMENTS = PROJECT_ROOT / "model" / "requirements"

REGION_START = "# --- SWCraft's architecture: the need types, fields and link types its needs.json uses ---"
REGION_END = "# --- end of SWCraft's declarations ---"
TARGET_URL = "vscode://swcraft-local.swcraft-vscode/model?path={{need.swcraft_path | urlencode}}"
CONDITIONAL = 'if not (Path(__file__).parent / "swcraft" / "needs.json").is_file(): needs_external_needs = []'

FEATURE_IDS = ("REQ_SHOWCASE_BASELINE_001", "REQ_SHOWCASE_BASELINE_002", "REQ_SHOWCASE_FEATURE_001", "REQ_BTP_SAFETY_GOAL")
TEST_IDS = ("TC-BRK-001", "TC-THP-001")
SWR_RE = re.compile(r"^SWR-(BRK|THP|DIA|DRV|GEN)-\d{3}$")
#: The acronyms the software requirements' synthetic texts use; any other all-capital
#: word would be a name from outside this showcase's world.
ACRONYMS = {"ECU", "DTC"}
KINDS = {"swc", "port", "runnable", "interface", "composition", "task", "partition", "core", "processor", "memory"}
DISTRACTORS = {
    "SWR-BRK-011", "SWR-THP-010", "SWR-DIA-009", "SWR-DIA-010",
    "SWR-DRV-005", "SWR-DRV-006", "SWR-GEN-003", "SWR-GEN-004",
}

HEADER = "Requirements import: baseline {version} (from the file)"
SUMMARY_1_0 = "Summary: 46 added, 0 changed, 0 removed, 0 stubs created, 4 source updates"
SUMMARY_1_1 = "Summary: 0 added, 1 changed, 1 removed, 0 stubs created, 48 source updates"
NOT_IMPORTED = "Not imported: 2 needs of a type the mapping ignores (test)"
WITHDRAWN_LINE = "  SWR-BRK-011 (was v1; absent from this delivery)"


GENERATOR_MODULE = gate.load_script("generate_requirements_deliveries")


def delivery_file(version: str) -> Path:
    return EXCHANGE / "deliveries" / version / "needs.json"


def delivered(version: str) -> tuple[dict, dict[str, dict]]:
    """The delivery's whole document and its selected version's needs."""
    document = json.loads(delivery_file(version).read_text(encoding="utf-8"))
    return document, document["versions"][document["current_version"]]["needs"]


@functools.cache
def answer_key() -> dict[str, Any]:
    """The answer key's whole document, read once."""
    return json.loads((EXCHANGE / "answer-key.json").read_text(encoding="utf-8"))


def table(version: str) -> dict[str, dict[str, str]]:
    return {need["id"]: need for need in GENERATOR_MODULE.delivery(version)}


def model_requirement(requirement_id: str) -> dict[str, str | list[str]]:
    """The top-level keys of one requirement file, read line by line (stdlib only).

    Enough for the requirement files: plain, single- or double-quoted scalars (quotes
    removed), and block lists (``derived_from``).
    """
    scalars: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    key = None
    for line in (REQUIREMENTS / f"{requirement_id}.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("- ") and key is not None:
            lists.setdefault(key, []).append(line[2:].strip())
            continue
        key, _, raw = line.partition(":")
        raw = raw.strip()
        if raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1].replace("''", "'")
        elif raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        if raw:
            scalars[key] = raw
    return {**scalars, **lists}


class TestGenerator(unittest.TestCase):
    def test_the_committed_sources_are_the_generators_output(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"], capture_output=True, text=True, check=False
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_check_fails_on_a_difference(self) -> None:
        module = GENERATOR_MODULE
        quiet = contextlib.ExitStack()
        quiet.enter_context(contextlib.redirect_stdout(io.StringIO()))
        quiet.enter_context(contextlib.redirect_stderr(io.StringIO()))
        with tempfile.TemporaryDirectory() as tmp, quiet, mock.patch.object(module, "TEAM_DIR", Path(tmp)):
            self.assertEqual(1, module.main(["--check"]))
            self.assertEqual(0, module.main([]))
            self.assertEqual(0, module.main(["--check"]))
            source = Path(tmp) / "delivery-1.0" / "index.rst"
            source.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))
            self.assertEqual(1, module.main(["--check"]))

    def test_the_table_counts(self) -> None:
        first = GENERATOR_MODULE.delivery("1.0")
        self.assertEqual(52, len(first))
        self.assertEqual(46, sum(1 for need in first if SWR_RE.match(need["id"])))
        self.assertEqual(list(TEST_IDS), [need["id"] for need in first if need["type"] == "test"])
        self.assertEqual(["REQ_BTP_SAFETY_GOAL"], [need["id"] for need in first if need["type"] == "sgoal"])


class TestDeliveries(unittest.TestCase):
    def test_each_delivery_holds_exactly_the_tables_needs(self) -> None:
        for version in GENERATOR_MODULE.VERSIONS:
            with self.subTest(version=version):
                document, needs = delivered(version)
                self.assertEqual(version, document["current_version"])
                self.assertEqual([version], list(document["versions"]))
                self.assertEqual("Vehicle control software requirements (synthetic)", document["project"])
                expected = table(version)
                self.assertEqual(set(expected), set(needs))
                self.assertEqual(len(expected), document["versions"][version]["needs_amount"])
                for need_id, row in expected.items():
                    need = needs[need_id]
                    self.assertEqual(
                        (row["type"], row["title"], row["content"], "approved", row.get("document"), row["rev"],
                         row.get("safety"), [row["parent"]] if "parent" in row else [], False),
                        (need["type"], need["title"], need["content"], need["status"], need["document"], need["rev"],
                         need["safety"], need["parent"], need["is_external"]),
                        need_id,
                    )

    def test_the_deliveries_carry_no_timestamp(self) -> None:
        for version in GENERATOR_MODULE.VERSIONS:
            with self.subTest(version=version):
                document, _ = delivered(version)
                self.assertNotIn("created", document)
                self.assertNotIn("created", document["versions"][version])

    def test_delivery_1_1_changes_one_requirement_and_withdraws_one(self) -> None:
        _, first = delivered("1.0")
        _, second = delivered("1.1")
        self.assertEqual({"SWR-BRK-011"}, set(first) - set(second))
        self.assertEqual(set(), set(second) - set(first))
        # Where a need stands moves: its source line with the withdrawn need above it, its
        # sections with the page title naming the delivery. Nothing else may.
        def placed(need: dict) -> dict:
            return {key: value for key, value in need.items() if key not in {"lineno", "sections"}}

        changed = {need_id for need_id in second if placed(first[need_id]) != placed(second[need_id])}
        self.assertEqual({"SWR-THP-003"}, changed)
        before, after = placed(first["SWR-THP-003"]), placed(second["SWR-THP-003"])
        self.assertEqual(("1", "2"), (before["rev"], after["rev"]))
        self.assertIn("600 degC", before["content"])
        self.assertIn("650 degC", after["content"])
        self.assertEqual({"content", "rev"}, {key for key in before if before[key] != after[key]})

    def test_the_four_feature_needs_equal_the_models_requirements(self) -> None:
        _, needs = delivered("1.0")
        for requirement_id in FEATURE_IDS:
            with self.subTest(requirement=requirement_id):
                model = model_requirement(requirement_id)
                need = needs[requirement_id]
                self.assertEqual("external", model["source"])
                self.assertEqual(model["title"], need["title"])
                self.assertEqual(model["description"], need["content"])
                self.assertEqual(model.get("document"), need["document"])
                self.assertEqual(model["revision"], need["rev"])
                self.assertEqual(model.get("asil"), need["safety"])
                parents = [parent.partition("@")[0] for parent in model.get("derived_from", [])]
                self.assertEqual(parents, need["parent"])

    def test_no_id_holds_a_dot(self) -> None:
        """Sphinx-Needs 9.2.0 links no id holding ``.``, and ``generate needs`` refuses one."""
        for version in GENERATOR_MODULE.VERSIONS:
            _, needs = delivered(version)
            for need_id, need in needs.items():
                with self.subTest(version=version, need=need_id):
                    self.assertNotIn(".", need_id)
                    for parent in need["parent"]:
                        self.assertNotIn(".", parent)

    def test_the_software_requirements_stay_in_the_synthetic_world(self) -> None:
        for need_id, need in [*table("1.0").items(), *table("1.1").items()]:
            if not SWR_RE.match(need_id):
                continue
            with self.subTest(need=need_id):
                text = f"{need['title']} {need['content']}"
                self.assertNotRegex(text, r"https?://|@|www\.")
                self.assertLessEqual(set(re.findall(r"\b[A-Z]{2,}\b", text)), ACRONYMS)


class TestAnswerKey(unittest.TestCase):
    def setUp(self) -> None:
        self.document = answer_key()
        self.key = self.document["requirements"]

    def test_the_key_names_exactly_delivery_1_0s_software_requirements(self) -> None:
        _, needs = delivered("1.0")
        software = {need_id for need_id in needs if SWR_RE.match(need_id)}
        self.assertEqual(46, len(software))
        self.assertEqual(software, set(self.key))
        for need_id, entry in self.key.items():
            with self.subTest(need=need_id):
                self.assertNotIn(".", need_id)
                self.assertEqual({"document", "targets"}, set(entry))
                self.assertEqual(needs[need_id]["document"], entry["document"])

    def test_targets_are_addresses(self) -> None:
        for need_id, entry in self.key.items():
            for target in entry["targets"]:
                with self.subTest(need=need_id, target=target):
                    self.assertEqual({"kind", "owner", "name"}, set(target))
                    self.assertIn(target["kind"], KINDS)
                    self.assertEqual(target["kind"] in {"port", "runnable"}, target["owner"] is not None)

    def test_the_eight_distractors(self) -> None:
        self.assertEqual(DISTRACTORS, {need_id for need_id, entry in self.key.items() if not entry["targets"]})

    def test_the_description_names_the_exchange(self) -> None:
        self.assertIn("delivery 1.0", self.document["description"])
        self.assertNotIn("prelinked", self.document["description"])


class TestTeamProject(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = (TEAM / "conf.py").read_text(encoding="utf-8").splitlines()

    def region(self) -> list[str]:
        return self.lines[self.lines.index(REGION_START) : self.lines.index(REGION_END)]

    def test_the_region_links_into_vs_code_and_names_the_handover_path(self) -> None:
        region = self.region()
        self.assertIn(f'        "target_url": "{TARGET_URL}",', region)
        self.assertIn('        "json_path": "swcraft/needs.json",', region)
        self.assertEqual(4, sum(line.count('"parse_conditions": False') for line in region))
        self.assertEqual(5, sum(line.count('"parse_dynamic_functions": False') for line in region))
        self.assertEqual(2, sum(line.count('"allow_dead_links": True') for line in region))

    def test_the_conditional_follows_the_region(self) -> None:
        tail = self.lines[self.lines.index(REGION_END) + 1 :]
        self.assertIn(CONDITIONAL, tail)
        self.assertEqual(1, sum(1 for line in self.lines if "needs_external_needs = []" in line))
        self.assertIn("needs_reproducible_json = True", tail)

    def test_requirements_pin_the_oracles_versions(self) -> None:
        pins = [
            line.strip() for line in (TEAM / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        self.assertEqual(["sphinx-needs==9.2.0", "sphinx==9.0.4", "ub-needs-exchange==1.1.0", "docutils==0.22.4"], pins)

    def test_the_handover_folder_is_git_ignored_and_absent_from_the_commit(self) -> None:
        ignored = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("demos/requirements-exchange/team/swcraft/", ignored)
        # The commit: a checkout has git and .git (the CI runner checks out); a kit has
        # no .git, and there only this half skips.
        with self.subTest("git ls-files"):
            git = shutil.which("git")
            if git is None or not (PROJECT_ROOT / ".git").exists():
                self.skipTest("no git or no .git: the commit's file list cannot be read")
            listed = subprocess.run(
                [git, "-C", str(PROJECT_ROOT), "ls-files", "--", "demos/requirements-exchange/team/swcraft"],
                capture_output=True, text=True, encoding="utf-8", check=False,
            )
            self.assertEqual(0, listed.returncode, listed.stderr)
            self.assertEqual("", listed.stdout, "the handover folder's files are committed")


class TestTheImport(unittest.TestCase):
    """Both deliveries through the installed SWCraft's import, on a temporary copy."""

    def run_import(self, root: Path, version: str, *extra: str):
        return subprocess.run(
            [str(toolchain().swcraft), "import", "requirements", "--source", str(delivery_file(version)),
             "--project", str(root / "swcraft.yaml"), *extra],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def test_the_two_deliveries(self) -> None:
        toolchain()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copy2(gate.MANIFEST, root / "swcraft.yaml")
            shutil.copytree(gate.MODEL_ROOT, root / "model")
            mapping = ("--mapping", str(MAPPING))

            refused = self.run_import(root, "1.0", "--dry-run")
            self.assertNotEqual(0, refused.returncode, refused.stdout)
            self.assertIn("map it under 'types'", refused.stderr)

            dry = self.run_import(root, "1.0", *mapping, "--dry-run")
            self.assertEqual(0, dry.returncode, dry.stderr)
            lines = dry.stdout.splitlines()
            self.assertEqual(HEADER.format(version="1.0"), lines[0])
            self.assertIn(NOT_IMPORTED, lines)
            self.assertIn(SUMMARY_1_0, lines)

            applied = self.run_import(root, "1.0", *mapping)
            self.assertEqual(0, applied.returncode, applied.stderr)
            self.assertIn(SUMMARY_1_0, applied.stdout.splitlines())

            second = self.run_import(root, "1.1", *mapping, "--dry-run")
            self.assertEqual(0, second.returncode, second.stderr)
            lines = second.stdout.splitlines()
            self.assertEqual(HEADER.format(version="1.1"), lines[0])
            self.assertIn(SUMMARY_1_1, lines)
            self.assertIn(WITHDRAWN_LINE, lines)


if __name__ == "__main__":
    unittest.main()
