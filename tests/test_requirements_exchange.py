"""The requirements exchange: the shipped state, the prepared files, and the scenario walked on the command line.

``demos/requirements-exchange.md`` walks *import delivery 1.0 -> link -> build ->
import delivery 1.1 -> confirm* on the model this repository ships. Three things are
held here:

* **the shipped state** (stdlib; the links also through the probe on the installed
  SWCraft): the model is the state before delivery 1.0 -- no ``SWR-*`` requirement
  and no ``SWR-*`` link, no ``trace-decisions.yaml``, the four external requirements
  at the team's earlier delivery ``0.9``;
* **the prepared files** (stdlib): ``prepared-links.json`` decides exactly the answer
  key -- every key target accepted, every distractor's row rejected, nothing else, no
  mark of an Apply; the ready-made sites under ``sites/`` each show the needs file
  they were built from (their links, by need id, in ``tests/test_requirements_sites.py``);
  neither the links nor the sites name a local path. With SWCraft on ``PATH``,
  ``scripts/generate_requirements_prepared.py --check`` holds the links file and the
  three needs files to the generator (the sites' bytes are checked on the maintainer's
  machine only: no test runs Sphinx);
* **the walk**, on a temporary copy of the project, with the page's command lines on
  the installed SWCraft (``swcraft_on_path``; without it the walk skips, and
  ``SHOWCASE_REQUIRE_SWCRAFT=1`` makes the skip a failure):

  1. import delivery 1.0 with the team's mapping -- the report's *Mapping:* line relative to
     the project also for a mapping given by its full path (:data:`MAPPING_LINE`); 50 warnings;
  2. by hand, ``--labelling '"all"'``: the key on ``SWR-THP-003`` (its third row),
     and ``SWR-BRK-008`` (the first row under **More candidates**, the fourth in the panel's
     order), one ✕ on ``SWR-BRK-011``'s first row in the panel's order
     (:data:`HAND_REJECTED_ROW`), Apply -- 48 warnings;
     then the committed ``prepared-links.json`` copied into ``dist/`` and applied as
     it is, the page's two commands -- 12 warnings, every key requirement satisfied
     by exactly its targets; applied again, *No change.*; the committed file's SHA-256
     taken before the walk starts and equal at its end;
  3. ``generate needs`` names ``1.0``; every element the key linked is a need with the
     requirement under ``satisfies`` and its ``swcraft_path``; the stale case's three
     interfaces under ``satisfies_unconfirmed``; no incoming requirement is a need;
     the file byte for byte the committed ``sites/1.0.needs.json``;
  5. import delivery 1.1: 12 warnings, one of them the link to ``SWR-THP-003@1``
     awaiting confirmation, which ``generate needs`` (naming ``1.1``) puts under
     ``satisfies_unconfirmed`` (``sites/1.1-unconfirmed.needs.json``); ``SWR-BRK-011``
     is gone; a Review search, the link confirmed, Apply -- back under ``satisfies``,
     11 warnings (``sites/1.1-confirmed.needs.json``).

The page itself (:class:`TestThePage`): its § 0 gives the kit's command-line Build as
``clean-outputs``, ``validate``, ``generate diagrams`` and ``generate needs`` -- the panel's Build
empties ``dist/`` first, and step 3 rests on that -- and those commands, run on a copy holding the
copy of the prepared links and a proposals file, take both with them; its limits section names
each case of the team site's link in a window open on another folder (the notification quoted
from the extension's source at the pinned release, not observed: no graphical session here).

What this does not reach: the editor's panel (the maintainer's walk); the team's
Sphinx (the sites are built by the generator on the maintainer's machine); how good
the proposals are -- no band or rank is asserted beyond the three rows the page names,
and the prepared file follows the key wherever the search put its targets.
``SHOWCASE_EXCHANGE_WALK_RECORD`` names a file the walk writes its observations to;
``SHOWCASE_EXCHANGE_WALK_KEEP`` names a directory the walk copies three states of the
project into, each with the ``dist/needs.json`` it generated: ``1.0``,
``1.1-unconfirmed`` and ``1.1-confirmed``.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate
from test_model_coverage import STALE_HOLDERS, STALE_REQUIREMENT, expected_warnings, toolchain, warning_lines
from test_requirements_deliveries import (
    EXCHANGE,
    FEATURE_IDS,
    HEADER,
    MAPPING,
    NOT_IMPORTED,
    REQUIREMENTS,
    SUMMARY_1_0,
    SUMMARY_1_1,
    WITHDRAWN_LINE,
    delivered,
    delivery_file,
    model_requirement,
)

PROJECT_ROOT = gate.PROJECT_ROOT
RECORD_ENV = "SHOWCASE_EXCHANGE_WALK_RECORD"
KEEP_ENV = "SHOWCASE_EXCHANGE_WALK_KEEP"
#: What the walk copies: the project as a colleague has it, without the build's outputs.
COPIED = ("swcraft.yaml", "model", "experiments", "demos")
STUB = "HAZ_BTP_BRAKE_FADE"
CHANGED = "SWR-THP-003"
WITHDRAWN = "SWR-BRK-011"
CHANGED_HOLDER = "PORT-BrakeThermalProtection-pPermittedBrakeAction"
PREPARED_SCRIPT = PROJECT_ROOT / "scripts" / "generate_requirements_prepared.py"
#: Where the page's two hand links stand in the panel's row order: the third row and the
#: fourth -- the panel shows a window of three rows, so the fourth is the **first** row under
#: **More candidates**. A link to an element outside the rows (**Any element of the model…**,
#: two pickers for a runnable) is left to the prepared file, the maintainer's decision of
#: 2026-11-10.
HAND_POSITIONS = {"SWR-THP-003": 3, "SWR-BRK-008": 4}
#: The element the page names for each hand link (the page's "the component" is the kind swc);
#: the third row is the port that step 5 turns unconfirmed.
HAND_TARGETS = {
    "SWR-THP-003": "port BrakeThermalProtection.pPermittedBrakeAction",
    "SWR-BRK-008": "swc BrakeController",
}
#: The row the page's one ✕ falls on: the first of the distractor's rows in the panel's order.
HAND_REJECTED_ROW = "runnable BrakeTemperatureSensor.PublishBrakeTemperature"
#: The summaries the page quotes, as the pinned release prints them.
HAND_SUMMARY = (
    "Summary: 2 written, 0 confirmed, 1 rejected, 0 already done, 0 stale, 0 not written, 553 undecided; 2 files"
)
PREPARED_HEADER = "Trace apply: proposals of the search 'trace' (the model has changed since the search)"
PREPARED_SUMMARY = (
    "Summary: 38 written, 0 confirmed, 73 rejected, 3 already done, 0 stale, 0 not written, 449 undecided; 10 files"
)
AGAIN_SUMMARY = (
    "Summary: 0 written, 0 confirmed, 0 rejected, 114 already done, 0 stale, 0 not written, 449 undecided; 0 files"
)
#: What a site file must not hold: a path of the machine it was built on.
LOCAL_PATH_RE = re.compile(r"/(?:Users|home|private|tmp)/|/var/folders/|[A-Z]:\\Users\\")
#: The import report's *Mapping:* line the page quotes: relative to the project folder, also when
#: the mapping is given by its full path, as VS Code gives it (0.23.0).
MAPPING_LINE = "Mapping: demos/requirements-exchange/team.needs-mapping.yaml"
UNALLOCATED_WARNING = (
    "WARNING: Requirement '{id}' is satisfied by no element: add `satisfies: [{id}@1]` on the component, "
    "port, runnable, composition, interface, task or hardware element that realizes it."
)
PAGE = PROJECT_ROOT / "demos" / "requirements-exchange.md"
#: The page's § 0: the kit's command-line Build, ``clean-outputs`` first as the panel's Build runs it
#: (``vscode_extension/src/commandCore.ts`` at the pinned release, ``BUILD_STEP_SUBCOMMANDS``).
SETUP_COMMANDS = [
    ["swcraft", *command.split(), "--project", "swcraft.yaml"]
    for command in ("clean-outputs", "validate", "generate diagrams", "generate needs")
]
#: The extension's notification for a model link in a window with no SWCraft project
#: (``vscode_extension/src/helpLinks.ts`` at the pinned release).
NO_PROJECT_NOTIFICATION = "SWCraft: a model link was not opened — no SWCraft project is open in this window."
#: The page's limits sentence, case by case (whitespace folded).
LINK_LIMITS = (
    "In a window with no SWCraft project it opens nothing and shows one notification",
    "In another SWCraft project it opens that project's file of the same name, if the project has one",
    "otherwise opens nothing and leaves one line in the **SWCraft** output channel",
)
#: A component member kind -> its need id prefix; every other kind -> its layer's prefix.
MEMBER_PREFIX = {"port": "PORT", "runnable": "RUN"}
LAYER_PREFIX = {
    "swc": "SWC",
    "interface": "IF",
    "composition": "COMP",
    "task": "TASK",
    "core": "HW",
    "partition": "HW",
    "processor": "HW",
    "memory": "HW",
}


PREPARED = gate.load_script("generate_requirements_prepared")
PREPARED_FILE = EXCHANGE / PREPARED.PREPARED_NAME
rows_by_strength = PREPARED.rows_by_strength


def handover_file(state: str) -> Path:
    """The needs file the committed site of *state* was built from."""
    return EXCHANGE / PREPARED.SITES_NAME / f"{state}.needs.json"


#: Requirement id -> the elements the answer key links it to (empty: a distractor), read once.
key = functools.cache(PREPARED.answer_key)


def delivery_ids(version: str) -> list[str]:
    return list(delivered(version)[1])


def project_relative(path: Path, root: Path = PROJECT_ROOT) -> str:
    """*path* relative to the project (*root*), so that in the walk it names the copy's file."""
    return path.relative_to(root).as_posix()


def with_unallocated(by_design: list[str], need_ids: list[str]) -> list[str]:
    """The warnings by design and one *satisfied by no element* warning per requirement of *need_ids*."""
    return sorted([*by_design, *(UNALLOCATED_WARNING.format(id=need_id) for need_id in need_ids)])


def element_need_id(target: dict[str, Any]) -> str:
    """The id SWCraft's needs file gives the element a key target addresses."""
    if target["kind"] in MEMBER_PREFIX:
        return f"{MEMBER_PREFIX[target['kind']]}-{target['owner']}-{target['name']}"
    return f"{LAYER_PREFIX[target['kind']]}-{target['name']}"


def address(target: dict[str, Any]) -> str:
    owner = f"{target['owner']}." if target.get("owner") else ""
    return f"{target['kind']} {owner}{target['name']}"


def satisfying_sites(links: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Member (``<id>@<version>``) -> the sites whose ``satisfies`` lists it."""
    sites: dict[str, list[dict[str, Any]]] = {}
    for entry in links["links"]:
        for member in entry["members"]:
            sites.setdefault(member, []).append(entry["site"])
    return sites


def unordered(targets: list[dict[str, Any]]) -> list[str]:
    return sorted(json.dumps(target, sort_keys=True) for target in targets)


class Walk:
    """The project copied into a temporary directory, and the commands the walkthrough runs."""

    def __init__(self, root: Path) -> None:
        self.root = root
        for name in COPIED:
            source = PROJECT_ROOT / name
            if source.is_dir():
                shutil.copytree(source, root / name)
            else:
                shutil.copy2(source, root / name)
        self.manifest = root / "swcraft.yaml"
        self.proposals_path = root / "dist" / "experiments" / "trace" / "proposals.json"
        self.needs_path = root / "dist" / "needs.json"

    def swcraft(self, *args: str, expect: int = 0) -> str:
        completed = subprocess.run(
            [str(toolchain().swcraft), *args, "--project", str(self.manifest)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            cwd=self.root,
            timeout=gate.COMMAND_TIMEOUT,
        )
        output = completed.stdout + completed.stderr
        if completed.returncode != expect:
            raise AssertionError(f"swcraft {' '.join(args)} exited {completed.returncode}:\n{output}")
        return output

    def import_delivery(self, version: str, *extra: str) -> str:
        source, mapping = project_relative(delivery_file(version)), project_relative(MAPPING)
        return self.swcraft("import", "requirements", "--source", source, "--mapping", mapping, *extra)

    def search(self, labelling: str) -> dict[str, Any]:
        self.swcraft("experiment", "trace", "--config", "experiments/trace.yaml", "--labelling", labelling)
        return self.proposals()

    def proposals(self) -> dict[str, Any]:
        return json.loads(self.proposals_path.read_text(encoding="utf-8"))

    def save(self, proposals: dict[str, Any]) -> None:
        self.proposals_path.write_text(json.dumps(proposals, indent=2) + "\n", encoding="utf-8", newline="\n")

    def apply(self) -> str:
        """The dry run, then the applied run bound to its plan; the applied run's output."""
        dry = self.swcraft("experiment", "trace", "--apply", str(self.proposals_path), "--dry-run")
        plan = re.search(r"^Plan: (sha256:[0-9a-f]{64})$", dry, re.MULTILINE)
        assert plan is not None, dry
        return self.swcraft(
            "experiment", "trace", "--apply", str(self.proposals_path), "--expect-plan", plan.group(1)
        )

    def warnings(self) -> list[str]:
        return sorted(warning_lines(self.swcraft("check-model")))

    def links(self) -> dict[str, Any]:
        return gate.model_links(toolchain(), self.root / "model")

    def generate_needs(self) -> dict[str, Any]:
        self.swcraft("generate", "needs")
        return json.loads(self.needs_path.read_text(encoding="utf-8"))

    def keep(self, name: str) -> None:
        """Copy the project as it stands, ``dist/needs.json`` included, into the keep directory."""
        keep_dir = os.environ.get(KEEP_ENV)
        if keep_dir:
            shutil.copytree(self.root, Path(keep_dir) / name)


def summary_lines(output: str, *ids: str) -> list[str]:
    """The report's header, *Not imported* and summary lines, and the lines of the requirements *ids*."""
    heads = ("Requirements import:", "Not imported:", "Summary:", *(f"  {need_id} " for need_id in ids))
    return [line for line in output.splitlines() if line.startswith(heads)]


def apply_counts(output: str) -> dict[str, int]:
    """An Apply's *Summary:* line as the counts the page states: written, confirmed, rejected, files."""
    match = re.search(
        r"^Summary: (\d+) written, (\d+) confirmed, (\d+) rejected, .*; (\d+) files?$", output, re.MULTILINE
    )
    assert match is not None, output
    return dict(zip(("written", "confirmed", "rejected", "files"), map(int, match.groups())))


def apply_lines(output: str, count: int = 2) -> list[str]:
    """An applied run's first *count* lines: its header, its *Summary:* line, and *No change.* if it says so."""
    return output.splitlines()[:count]


class TestShippedState(unittest.TestCase):
    """The model the repository ships is the state before delivery 1.0."""

    def test_no_software_requirement_and_no_decisions_file(self) -> None:
        self.assertEqual([], sorted(path.name for path in REQUIREMENTS.glob("SWR-*")))
        self.assertFalse((PROJECT_ROOT / "trace-decisions.yaml").exists())
        holding = [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in sorted((PROJECT_ROOT / "model").rglob("*.yaml"))
            if "SWR-" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual([], holding)

    def test_the_four_externals_are_at_the_earlier_delivery(self) -> None:
        externals = sorted(
            path.stem
            for path in REQUIREMENTS.glob("*.yaml")
            if model_requirement(path.stem).get("source") == "external" and path.stem != STUB
        )
        self.assertEqual(sorted(FEATURE_IDS), externals)
        for need_id in FEATURE_IDS:
            with self.subTest(need_id=need_id):
                self.assertEqual("0.9", model_requirement(need_id).get("baseline"))

    def test_no_link_names_a_software_requirement(self) -> None:
        links = gate.model_links(toolchain())
        members = sorted(member for entry in links["links"] for member in entry["members"])
        self.assertEqual([], [member for member in members if member.startswith("SWR-")])
        self.assertEqual([], links["decisions"])


class TestPreparedFiles(unittest.TestCase):
    """The prepared links and the ready-made sites, as committed."""

    def test_the_prepared_links_decide_exactly_the_answer_key(self) -> None:
        proposals = json.loads(PREPARED_FILE.read_text(encoding="utf-8"))
        entries = {entry["id"]: entry for entry in proposals["requirements"]}
        answer = key()
        self.assertLessEqual(set(answer), set(entries))
        for need_id, entry in entries.items():
            with self.subTest(need_id=need_id):
                self.assertEqual("review", entry["pass"])
                decisions = [row["decision"] for row in entry["candidates"]]
                accepted = [row["target"] for row in entry["candidates"] if row["decision"] == "accept"]
                chosen = [item["target"] for item in entry["chosen"]]
                if need_id not in answer:
                    self.assertEqual(set(), set(decisions) - {None})
                    self.assertEqual([], chosen)
                elif answer[need_id]:
                    self.assertEqual(unordered(answer[need_id]), unordered(accepted + chosen))
                    self.assertEqual(set(), set(decisions) - {None, "accept"})
                else:
                    self.assertTrue(decisions)
                    self.assertEqual({"reject"}, set(decisions))
                    self.assertEqual([], chosen)
                for item in [*entry["candidates"], *entry["chosen"], *entry["linked"]]:
                    self.assertFalse({"applied", "stale", "preselected"} & set(item), item)

    def test_each_site_shows_the_needs_file_it_was_built_from(self) -> None:
        for state, version in PREPARED.STATES.items():
            with self.subTest(state=state):
                handover = json.loads(handover_file(state).read_text(encoding="utf-8"))
                self.assertEqual(version, handover["current_version"])
                page = (EXCHANGE / PREPARED.SITES_NAME / state / "index.html").read_text(encoding="utf-8")
                self.assertIn(f"delivery {version}", page)
                for need_id in handover["versions"][version]["needs"]:
                    self.assertIn(f">{need_id}<", page, need_id)
        unconfirmed = (EXCHANGE / PREPARED.SITES_NAME / "1.1-unconfirmed" / "index.html").read_text(encoding="utf-8")
        confirmed = (EXCHANGE / PREPARED.SITES_NAME / "1.1-confirmed" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(1, unconfirmed.count("satisfied by (unconfirmed)"))
        self.assertEqual(0, confirmed.count("satisfied by (unconfirmed)"))

    def test_the_prepared_files_name_no_local_path(self) -> None:
        """The prepared links and every file under ``sites/``: no path of the machine they were made on."""
        sites = EXCHANGE / PREPARED.SITES_NAME
        files = [path for path in sorted(sites.rglob("*")) if path.is_file()]
        self.assertTrue(files)
        for path in [PREPARED_FILE, *files]:
            with self.subTest(path=path.relative_to(EXCHANGE).as_posix()):
                self.assertIsNone(LOCAL_PATH_RE.search(path.read_bytes().decode("utf-8", errors="replace")))
                self.assertNotIn(path.name, PREPARED.SITE_REFUSED_NAMES)

    def test_the_committed_files_are_the_generators_output(self) -> None:
        """The links and the three needs files; the sites' HTML only on the maintainer's machine (Sphinx)."""
        tools = toolchain()
        result = subprocess.run(
            [sys.executable, str(PREPARED_SCRIPT), "--check"],
            capture_output=True, text=True, encoding="utf-8", check=False, timeout=gate.COMMAND_TIMEOUT,
            env={**os.environ, "PATH": os.pathsep.join([str(tools.swcraft.parent), os.environ.get("PATH", "")])},
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


def setup_commands() -> list[list[str]]:
    """The command block of the page's § 0: the kit's command-line Build, one argv per line."""
    text = PAGE.read_text(encoding="utf-8")
    section = text[text.index("## 0. Setup") : text.index("## 1. ")]
    block = re.search(r"```text\n(.*?)```", section, re.DOTALL)
    assert block is not None, "demos/requirements-exchange.md § 0 has no command block"
    return [line.split() for line in block.group(1).splitlines() if line.strip()]


class TestThePage(unittest.TestCase):
    """What the page says of the kit's command-line Build and of the team site's link."""

    def test_the_kits_command_line_build_empties_the_outputs_first(self) -> None:
        self.assertEqual(SETUP_COMMANDS, setup_commands())

    def test_the_kits_command_line_build_takes_the_copy_and_the_proposals_with_it(self) -> None:
        """Step 3 rests on the Build emptying ``dist/``; on a copy, the page's commands do."""
        toolchain()
        with tempfile.TemporaryDirectory() as tmp:
            walk = Walk(Path(tmp))
            copy = walk.root / "dist" / PREPARED.PREPARED_NAME
            walk.proposals_path.parent.mkdir(parents=True)
            shutil.copy2(PREPARED_FILE, copy)
            shutil.copy2(PREPARED_FILE, walk.proposals_path)
            for argv in setup_commands():
                self.assertEqual(["--project", "swcraft.yaml"], argv[-2:], argv)
                walk.swcraft(*argv[1:-2])
            self.assertFalse(copy.exists(), "the copy of the prepared links")
            self.assertFalse(walk.proposals_path.exists(), "the last search's proposals file")
            self.assertTrue((walk.root / "dist" / "model.arxml").is_file())
            self.assertTrue(walk.needs_path.is_file())

    def test_the_links_limits_name_each_case_of_another_folder(self) -> None:
        text = " ".join(PAGE.read_text(encoding="utf-8").split())
        for sentence in (*LINK_LIMITS, NO_PROJECT_NOTIFICATION):
            with self.subTest(sentence=sentence):
                self.assertIn(sentence, text)


class TestTheWalk(unittest.TestCase):
    """``demos/requirements-exchange.md`` on the command line, on a temporary copy."""

    maxDiff = None

    def assert_linked_exactly(self, sites: dict[str, list[dict[str, Any]]], need_id: str, version: int) -> None:
        """*need_id* is satisfied by exactly the key's targets, at *version* and at no other."""
        targets = key()[need_id]
        found = [site for member, listed in sites.items() if member.split("@")[0] == need_id for site in listed]
        self.assertEqual(unordered(targets), unordered(sites.get(f"{need_id}@{version}", [])), need_id)
        self.assertEqual(unordered(targets), unordered(found), need_id)

    def test_the_requirements_exchange(self) -> None:
        toolchain()
        started = time.monotonic()
        answer = key()
        distractors = sorted(need_id for need_id, targets in answer.items() if not targets)
        linked_by_key = sorted(need_id for need_id, targets in answer.items() if targets)
        by_design = expected_warnings()
        record: dict[str, Any] = {}
        prepared_before = hashlib.sha256(PREPARED_FILE.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            walk = Walk(Path(tmp))
            self.assertEqual(by_design, walk.warnings())

            # 1. Delivery 1.0, with the team's mapping; the dry run with full paths, as VS Code runs it.
            dry = walk.swcraft(
                "import", "requirements", "--source", str(walk.root / project_relative(delivery_file("1.0"))),
                "--mapping", str(walk.root / project_relative(MAPPING)), "--dry-run",
            )
            self.assertIn(MAPPING_LINE, dry.splitlines(), "demos/requirements-exchange.md, step 1")
            imported = walk.import_delivery("1.0")
            self.assertIn(MAPPING_LINE, imported.splitlines())
            lines = summary_lines(imported)
            self.assertEqual([HEADER.format(version="1.0"), NOT_IMPORTED, SUMMARY_1_0], lines)
            record["importSummary1.0"] = lines
            after_import = walk.warnings()
            self.assertEqual(with_unallocated(by_design, list(answer)), after_import)
            self.assertEqual(50, len(after_import))
            record["warningsAfterImport1.0"] = len(after_import)

            # 2, by hand: Labelling of everything; two links and one rejection, Apply.
            proposals = walk.search('"all"')
            entries = {entry["id"]: entry for entry in proposals["requirements"]}
            positions = {}
            for need_id in PREPARED.HAND_LINKS:
                ordered = [row["target"] for row in rows_by_strength(entries[need_id]["candidates"])]
                (target,) = answer[need_id]
                positions[need_id] = ordered.index(target) + 1 if target in ordered else None
            page = "demos/requirements-exchange.md, step 2, by hand"
            self.assertEqual(HAND_POSITIONS, positions, f"{page}: the third row, the fourth")
            self.assertEqual(
                HAND_TARGETS,
                {need_id: address(answer[need_id][0]) for need_id in PREPARED.HAND_LINKS},
                f"{page} names each hand link's element",
            )
            hand_rejected = rows_by_strength(entries[PREPARED.HAND_REJECT]["candidates"])[0]["target"]
            self.assertEqual(HAND_REJECTED_ROW, address(hand_rejected), f"{page}: the first row of SWR-BRK-011")
            walk.save(PREPARED.decide_by_hand(proposals, answer))
            hand_apply = walk.apply()
            self.assertEqual(HAND_SUMMARY, apply_lines(hand_apply)[1], page)
            after_hand = walk.warnings()
            self.assertEqual(with_unallocated(by_design, sorted(set(answer) - set(PREPARED.HAND_LINKS))), after_hand)
            self.assertEqual(48, len(after_hand), f"{page} states that check-model prints 48 warnings")
            record["handPositions"] = positions
            record["handRejectedRow"] = address(hand_rejected)
            record["handApply"] = apply_lines(hand_apply)
            record["warningsAfterHand"] = len(after_hand)

            # 2, prepared: the committed proposals file copied into dist/ and applied as it is.
            committed_prepared = PREPARED_FILE.read_bytes()
            copy = walk.root / "dist" / PREPARED.PREPARED_NAME
            shutil.copyfile(walk.root / project_relative(PREPARED_FILE), copy)
            prepared_apply = walk.swcraft("experiment", "trace", "--apply", project_relative(copy, walk.root))
            page = "demos/requirements-exchange.md, step 2, the prepared links"
            self.assertEqual([PREPARED_HEADER, PREPARED_SUMMARY], apply_lines(prepared_apply), page)
            again = walk.swcraft("experiment", "trace", "--apply", project_relative(copy, walk.root))
            self.assertEqual([PREPARED_HEADER, AGAIN_SUMMARY, "No change."], apply_lines(again, 3), page)
            # Apply marks the copy; the copy's own prepared file is never changed by use.
            self.assertNotEqual(committed_prepared, copy.read_bytes())
            self.assertEqual(committed_prepared, (walk.root / project_relative(PREPARED_FILE)).read_bytes())
            record["preparedApply"] = apply_lines(prepared_apply)
            record["preparedAgain"] = apply_lines(again, 3)

            linked = walk.warnings()
            self.assertEqual(with_unallocated(by_design, distractors), linked)
            self.assertEqual(12, len(linked), f"{page}: 12 warnings")
            record["warningsAfterPrepared"] = len(linked)
            links = walk.links()
            sites = satisfying_sites(links)
            self.assertEqual(38, len(linked_by_key))
            for need_id in linked_by_key:
                with self.subTest(need_id=need_id):
                    self.assert_linked_exactly(sites, need_id, 1)
            for need_id in distractors:
                self.assertFalse(any(member.split("@")[0] == need_id for member in sites), need_id)
            self.assertEqual([], [decision for decision in links["decisions"] if decision.get("preselected")])
            rejected = [decision for decision in links["decisions"] if decision["decision"] == "reject"]
            self.assertTrue(all(decision["requirement"] in distractors for decision in rejected), rejected)
            record["decisionsRecorded"] = len(links["decisions"])
            record["rejectionsRecorded"] = len(rejected)

            # 3. The build's needs file: delivery 1.0, the key's elements, the stale case.
            needs_file = walk.generate_needs()
            self.assertEqual("1.0", needs_file["current_version"])
            needs = needs_file["versions"]["1.0"]["needs"]
            self.check_needs(walk, needs, answer, linked_by_key, delivery_ids("1.0"))
            self.assertIn(CHANGED, needs[CHANGED_HOLDER].get("satisfies", []))
            self.assertEqual(
                52, len(needs), "demos/requirements-exchange.md, step 3 states that dist/needs.json holds 52 needs"
            )
            record["needsAfterLinking"] = len(needs)
            walk.keep("1.0")
            self.assert_handover(walk, "1.0")

            # 5, import: delivery 1.1, one requirement changed, one withdrawn.
            imported = walk.import_delivery("1.1")
            self.assertIn(MAPPING_LINE, imported.splitlines(), "demos/requirements-exchange.md, step 5")
            lines = summary_lines(imported, CHANGED, WITHDRAWN)
            self.assertEqual(
                [
                    HEADER.format(version="1.1"),
                    NOT_IMPORTED,
                    SUMMARY_1_1,
                    f"  {CHANGED} v1 → v2 (description, baseline, revision)",
                    WITHDRAWN_LINE,
                ],
                lines,
            )
            record["importSummary1.1"] = lines
            self.assertFalse((walk.root / "model" / "requirements" / f"{WITHDRAWN}.yaml").exists())
            unconfirmed = walk.warnings()
            expected_left = with_unallocated(by_design, [need_id for need_id in distractors if need_id != WITHDRAWN])
            awaiting = [line for line in unconfirmed if line not in expected_left]
            self.assertEqual(12, len(unconfirmed))
            self.assertEqual(1, len(awaiting), awaiting)
            self.assertIn(f"'{CHANGED}@1'", awaiting[0])
            self.assertIn("pPermittedBrakeAction", awaiting[0])
            self.assertEqual(expected_left, sorted(line for line in unconfirmed if line != awaiting[0]))
            record["warningsAfterImport1.1"] = len(unconfirmed)
            record["awaitingConfirmation"] = awaiting[0]
            needs_file = walk.generate_needs()
            self.assertEqual("1.1", needs_file["current_version"])
            needs = needs_file["versions"]["1.1"]["needs"]
            self.assertIn(CHANGED, needs[CHANGED_HOLDER].get("satisfies_unconfirmed", []))
            self.assertNotIn(CHANGED, needs[CHANGED_HOLDER].get("satisfies", []))
            self.assertFalse(any(WITHDRAWN in json.dumps(need) for need in needs.values()))
            walk.keep("1.1-unconfirmed")
            self.assert_handover(walk, "1.1-unconfirmed")

            # 5, confirmation: Review again, the link confirmed against version 2.
            proposals = walk.search("[]")
            entries = {entry["id"]: entry for entry in proposals["requirements"]}
            self.assertNotIn(WITHDRAWN, entries)
            for decision in rejected:
                if decision["requirement"] in entries:
                    rows = [row["target"] for row in entries[decision["requirement"]]["candidates"]]
                    self.assertNotIn(decision["target"], rows, decision)
            pending = [link for link in entries[CHANGED]["linked"] if not link["confirmed"]]
            self.assertEqual(1, len(pending), entries[CHANGED]["linked"])
            pending[0]["decision"] = "confirm"
            walk.save(proposals)
            confirm_apply = walk.apply()
            self.assertEqual(
                {"written": 0, "confirmed": 1, "rejected": 0, "files": 1},
                apply_counts(confirm_apply),
                "demos/requirements-exchange.md, step 5 states 0 written, 1 confirmed in 1 file",
            )
            record["confirmApply"] = confirm_apply.splitlines()[:3]
            confirmed = walk.warnings()
            self.assertEqual(expected_left, confirmed)
            self.assertEqual(11, len(confirmed))
            record["warningsAfterConfirmation"] = len(confirmed)
            sites = satisfying_sites(walk.links())
            self.assert_linked_exactly(sites, CHANGED, 2)
            needs_file = walk.generate_needs()
            self.assertEqual("1.1", needs_file["current_version"])
            needs = needs_file["versions"]["1.1"]["needs"]
            self.assertIn(CHANGED, needs[CHANGED_HOLDER].get("satisfies", []))
            self.assertNotIn(CHANGED, needs[CHANGED_HOLDER].get("satisfies_unconfirmed", []))
            self.check_needs(walk, needs, answer, [n for n in linked_by_key if n != WITHDRAWN], delivery_ids("1.1"))
            walk.keep("1.1-confirmed")
            self.assert_handover(walk, "1.1-confirmed")

        # The committed file, hashed before the walk began, is the same at its end.
        self.assertEqual(prepared_before, hashlib.sha256(PREPARED_FILE.read_bytes()).hexdigest())
        record["seconds"] = round(time.monotonic() - started, 1)
        record_path = os.environ.get(RECORD_ENV)
        if record_path:
            Path(record_path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")

    def assert_handover(self, walk: Walk, state: str) -> None:
        """The walk's ``dist/needs.json`` at *state* is the one the committed site of *state* was built from."""
        self.assertEqual(
            handover_file(state).read_bytes(),
            walk.needs_path.read_bytes(),
            f"{project_relative(handover_file(state))} differs from the page's steps: "
            "run scripts/generate_requirements_prepared.py with --sphinx-build",
        )

    def check_needs(
        self,
        walk: Walk,
        needs: dict[str, Any],
        answer: dict[str, list[dict[str, Any]]],
        linked_by_key: list[str],
        incoming: list[str],
    ) -> None:
        """Every key element a need satisfying its requirement, with its file; the stale case; no incoming need."""
        for need_id in linked_by_key:
            for target in answer[need_id]:
                element = element_need_id(target)
                with self.subTest(requirement=need_id, element=element):
                    self.assertIn(element, needs)
                    self.assertIn(need_id, needs[element].get("satisfies", []))
                    path = needs[element].get("swcraft_path", "")
                    self.assertTrue(path)
                    self.assertTrue((walk.root / "model" / path).is_file(), path)
        for holder in STALE_HOLDERS:
            self.assertIn(STALE_REQUIREMENT, needs[f"IF-{holder}"].get("satisfies_unconfirmed", []), holder)
        self.assertEqual([], sorted(set(needs) & {*incoming, STUB}))
        for need in needs.values():
            self.assertTrue(need.get("swcraft_path"), need["id"])


if __name__ == "__main__":
    unittest.main()
