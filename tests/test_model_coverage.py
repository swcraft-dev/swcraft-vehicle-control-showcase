"""The model-coverage gate: every kind and every field of the installed contract.

The storefront's claim is that the committed model uses every kind and every
field of SWCraft's model contract at least once. The contract is read from the
**installed** SWCraft -- the release ``swcraft.yaml`` pins -- through the probe
``tests/model_coverage_probe.py``, run under that installation's own interpreter
(``swcraft_on_path``). Without SWCraft on PATH, or with another release, the gate
skips; ``SHOWCASE_REQUIRE_SWCRAFT=1`` makes either a failure.

Two tests split the claim so that a broken probe cannot pass for full coverage:

* the probe-health test: the probe runs, the versions and the import path agree,
  ``unknown`` is empty, the ids are the contract's, and the committed model
  passes ``swcraft check-model`` with no rule record and exactly the four
  warnings ``expected_warnings()`` lists, all by design -- the stub's,
  ``STUB_WARNING``, and the three links to confirm of the stale case,
  ``STALE_WARNING`` -- which the toolchain's total line ``findings_total()``
  counts, so ``--warnings-as-errors`` fails it on exactly that set;
* the "no id missing" test: every kind and every field of the installed
  contract is carried, so a change that loses any of them fails. (When the gate
  landed the model missed 40 of 58 kinds and 224 of 295 fields; the execution
  log records that list.)

Beside them, the negative controls show that the probe *can* report an id
missing: on a copy of the model with one element file deleted, or one key
removed, exactly the ids only that file carried go missing; and the walk itself
is exercised on a hand-written contract with JSON files (JSON is YAML), on any
Python, so its branches are tested where SWCraft is absent too. The element
count the README states is the number of files the probe walked.

What this does not reach: "carries" is key presence (the probe's docstring);
enumeration values and rules are not coverage targets -- a valid model cannot
show a failing rule, which is what the rejected-change demonstrations are for.
"""

from __future__ import annotations

import functools
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import model_coverage_probe as probe
import swcraft_on_path as gate


# A warning the storefront prints by design: `HAZ_BTP_BRAKE_FADE` is the stub the
# requirements import writes for a parent it does not have, and every stub is a warning
# (`trace.requirement-stub`). It is what carries the contract's `stub` field.
STUB_WARNING = "WARNING: Requirement 'HAZ_BTP_BRAKE_FADE' is a stub: named as a parent, never imported."
# And one stale case by design: `REQ_BTP_TEMPERATURE_RANGE` is at version 2 and its three
# interfaces still name version 1, so each link needs confirmation (`trace.link-needs-confirmation`).
STALE_REQUIREMENT = "REQ_BTP_TEMPERATURE_RANGE"
STALE_HOLDERS = ("IBrakeDiagnostics", "IBrakeTemperature", "IThermalProtectionStatus")
STALE_WARNING = (
    "WARNING: Interface '{holder}' satisfies '{id}@1', but requirement '{id}' is at version 2: "
    "confirm the link against version 2 and write '{id}@2'."
)


def expected_warnings() -> list[str]:
    """The four warnings by design: the stub's line and the stale case's three links to confirm.

    The committed model is the state before the requirements team's delivery 1.0: it
    holds no software requirement of the team's, so no ``trace.requirement-unallocated``
    line is by design.
    """
    stale = [STALE_WARNING.format(holder=holder, id=STALE_REQUIREMENT) for holder in STALE_HOLDERS]
    return sorted([STUB_WARNING, *stale])


def findings_total() -> str:
    """The line SWCraft (since 0.17.0) closes a run's findings with, on stderr: the toolchain's own count."""
    return f"0 error(s), {len(expected_warnings())} warning(s)."


def warning_lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip().startswith("WARNING:")]


def missing(report: dict[str, Any], table: str) -> set[str]:
    return {identifier for identifier, carriers in report[table].items() if not carriers}


def sole_carried(report: dict[str, Any], table: str, rel: str) -> set[str]:
    """The ids of *table* that the file *rel* alone carries."""
    return {identifier for identifier, carriers in report[table].items() if carriers == [rel]}


@functools.cache
def toolchain() -> gate.Toolchain:
    """The pinned installation, looked up once per test process (a skip is not cached)."""
    return gate.toolchain_or_skip()


@functools.cache
def report() -> dict[str, Any]:
    """The committed model's coverage report, probed once per test process."""
    return gate.run_probe(toolchain())


def _write_executable(path: Path, text: str = "not run: the version answer is injected\n") -> None:
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)


class TestLookup(unittest.TestCase):
    """The lookup and the skip/require policy, against a temporary fake ``bin/``."""

    PIN = "0.21.0"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.bin = Path(self._tmp.name) / "bin"
        self.bin.mkdir()
        self.exe = ".exe" if os.name == "nt" else ""

    def _swcraft(self) -> Path:
        swcraft = self.bin / f"swcraft{self.exe}"
        _write_executable(swcraft)
        return swcraft

    def _python(self) -> Path:
        python = self.bin / f"python{self.exe}"
        _write_executable(python)
        return python

    def _answer(self, version: str) -> Callable[[Path], str]:
        return lambda swcraft: version

    def test_found_takes_the_interpreter_beside_swcraft_unresolved(self) -> None:
        swcraft = self._swcraft()
        python = self._python()
        toolchain = gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=True, version_of=self._answer(self.PIN))
        self.assertEqual(swcraft, toolchain.swcraft)
        self.assertEqual(python, toolchain.python)
        self.assertEqual(self.PIN, toolchain.version)

    def test_a_symlinked_interpreter_is_not_resolved(self) -> None:
        self._swcraft()
        elsewhere = Path(self._tmp.name) / "elsewhere"
        elsewhere.mkdir()
        target = elsewhere / "python3"
        _write_executable(target)
        link = self.bin / "python3"
        try:
            link.symlink_to(target)
        except OSError as error:  # a capability, not a platform: probe for it
            self.skipTest(f"this filesystem refuses a symlink: {error}")
        toolchain = gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=True, version_of=self._answer(self.PIN))
        self.assertEqual(link, toolchain.python)

    def test_no_interpreter_beside_it_skips_or_fails_under_require(self) -> None:
        self._swcraft()
        with self.assertRaisesRegex(unittest.SkipTest, "no Python interpreter"):
            gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=False, version_of=self._answer(self.PIN))
        with self.assertRaisesRegex(AssertionError, "no Python interpreter"):
            gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=True, version_of=self._answer(self.PIN))

    def test_not_on_path_skips_or_fails_under_require(self) -> None:
        self._python()
        with self.assertRaisesRegex(unittest.SkipTest, "not on PATH"):
            gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=False, version_of=self._answer(self.PIN))
        with self.assertRaisesRegex(AssertionError, "not on PATH"):
            gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=True, version_of=self._answer(self.PIN))

    def test_another_version_skips_or_fails_under_require_naming_both(self) -> None:
        self._swcraft()
        self._python()
        with self.assertRaisesRegex(unittest.SkipTest, r"is 9\.9\.9, but .* pins toolchain_version 0\.21\.0"):
            gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=False, version_of=self._answer("9.9.9"))
        with self.assertRaisesRegex(AssertionError, r"is 9\.9\.9, but .* pins toolchain_version 0\.21\.0"):
            gate.toolchain_or_skip(str(self.bin), pin=self.PIN, require=True, version_of=self._answer("9.9.9"))

    def test_require_is_the_one_value_1(self) -> None:
        self.assertTrue(gate.require_requested({gate.REQUIRE_ENV: "1"}))
        self.assertFalse(gate.require_requested({gate.REQUIRE_ENV: "0"}))
        self.assertFalse(gate.require_requested({}))

    def test_the_path_check_names_both_sides(self) -> None:
        root = Path(self._tmp.name)
        python = self._python()
        inside = root / "lib" / "site-packages" / "swcraft_tools" / "__init__.py"
        gate.assert_tools_path_inside(inside.as_posix(), python)
        outside = root.parent / "another-env" / "swcraft_tools" / "__init__.py"
        with self.assertRaises(AssertionError) as raised:
            gate.assert_tools_path_inside(outside.as_posix(), python)
        self.assertIn(outside.resolve().as_posix(), str(raised.exception))
        self.assertIn(root.resolve().as_posix(), str(raised.exception))


@unittest.skipIf(os.name == "nt", "the fake swcraft is a POSIX shell script")
class TestInstalledVersion(unittest.TestCase):
    """``installed_version`` against a fake ``swcraft`` that prints a given answer."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.swcraft = Path(self._tmp.name) / "swcraft"

    def _answering(self, answer: str, code: int = 0) -> Path:
        _write_executable(self.swcraft, f"#!/bin/sh\nprintf '%s' '{answer}'\nexit {code}\n")
        return self.swcraft

    def test_the_bare_version_is_returned(self) -> None:
        self.assertEqual("0.21.0", gate.installed_version(self._answering("swcraft 0.21.0\n")))

    def test_a_non_zero_exit_is_refused_with_the_code(self) -> None:
        with self.assertRaisesRegex(gate.ToolchainUnavailable, "exited 3"):
            gate.installed_version(self._answering("swcraft 0.21.0\n", code=3))

    def test_an_answer_of_another_shape_is_refused(self) -> None:
        for answer in ("swcraft version 0.21.0\n", "", "swcraft 0.21.0 (dev)\n", "0.21.0\n"):
            with self.subTest(answer=answer):
                with self.assertRaisesRegex(gate.ToolchainUnavailable, "not 'swcraft <version>'"):
                    gate.installed_version(self._answering(answer))


def _write_json(root: Path, relative: str, value: object) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8", newline="\n")


def _field(layer: str, kind: str, name: str, **extra: object) -> dict[str, Any]:
    return {"id": f"field:{layer}.{kind}.{name}", "name": name, **extra}


def _kind(layer: str, kind: str, fields: list[dict[str, Any]], member_only: bool = False) -> dict[str, Any]:
    return {"id": f"kind:{layer}.{kind}", "kind": kind, "memberOnly": member_only, "fields": fields}


#: A contract of two layers in the shape the installed one has: ``things`` is
#: grouped, with a placement field, a collection whose two member kinds are told
#: apart by ``direction``, and an element-kind field; ``parts`` has two top-level
#: kinds told apart by ``kind``.
MINI_CONTRACT = {
    "contractVersion": "0.0.0",
    "rules": [],
    "layers": [
        {
            "name": "things",
            "storage": {"directory": "things", "nesting": "group"},
            "placement": {"field": "group"},
            "kinds": [
                _kind(
                    "things",
                    "thing",
                    [
                        _field("things", "thing", "name"),
                        _field("things", "thing", "group", placement=True),
                        _field(
                            "things",
                            "thing",
                            "ports",
                            collection={"memberKinds": ["port_in", "port_out"], "discriminatorField": "direction"},
                        ),
                        _field("things", "thing", "timing", elementKind="timing"),
                    ],
                ),
                _kind(
                    "things",
                    "port_in",
                    [_field("things", "port_in", "name"), _field("things", "port_in", "direction", enum=["in"])],
                    member_only=True,
                ),
                _kind(
                    "things",
                    "port_out",
                    [
                        _field("things", "port_out", "name"),
                        _field("things", "port_out", "direction", enum=["out"]),
                        _field("things", "port_out", "init"),
                    ],
                    member_only=True,
                ),
                _kind("things", "timing", [_field("things", "timing", "period")], member_only=True),
            ],
        },
        {
            "name": "parts",
            "storage": {"directory": "parts"},
            "kinds": [
                _kind(
                    "parts",
                    "part_a",
                    [
                        _field("parts", "part_a", "name"),
                        _field("parts", "part_a", "kind", enum=["a"]),
                        _field("parts", "part_a", "size"),
                    ],
                ),
                _kind(
                    "parts",
                    "part_b",
                    [
                        _field("parts", "part_b", "name"),
                        _field("parts", "part_b", "kind", enum=["b"]),
                        _field("parts", "part_b", "weight"),
                    ],
                ),
            ],
        },
    ],
}


class TestWalk(unittest.TestCase):
    """The probe's walk on a hand-written contract, with JSON files and no SWCraft."""

    T1 = "things/g1/T1.yaml"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        _write_json(
            root,
            self.T1,
            {
                "name": "T1",
                "ports": [{"name": "p", "direction": "in"}, {"name": "q", "direction": "sideways"}, "a string"],
                "timing": {"period": 1},
                "colour": "red",
            },
        )
        _write_json(root, "things/T0.yaml", {"name": "T0", "colour": "outside any group"})
        _write_json(root, "parts/A.yaml", {"name": "A", "kind": "a", "size": 1})
        _write_json(root, "parts/C.yaml", {"name": "C", "kind": "c"})
        _write_json(root, "parts/L.yaml", [1, 2])
        _write_json(root, "parts/sub/X.yaml", {"name": "X", "kind": "a", "weight": 2})
        self.walk = probe.Walk(MINI_CONTRACT, root)
        self.walk.run(load=json.loads)

    def test_kinds_are_marked_by_their_files_and_an_absent_kind_stays_empty(self) -> None:
        self.assertEqual(
            {
                "things.thing": [self.T1],
                "things.port_in": [self.T1],
                "things.port_out": [],
                "things.timing": [self.T1],
                "parts.part_a": ["parts/A.yaml"],
                "parts.part_b": [],
            },
            self.walk.kinds,
        )

    def test_fields_are_marked_by_key_presence_and_placement(self) -> None:
        carried = {identifier for identifier, carriers in self.walk.fields.items() if carriers}
        self.assertEqual(
            {
                "things.thing.name",
                "things.thing.group",
                "things.thing.ports",
                "things.thing.timing",
                "things.port_in.name",
                "things.port_in.direction",
                "things.timing.period",
                "parts.part_a.name",
                "parts.part_a.kind",
                "parts.part_a.size",
            },
            carried,
        )
        self.assertEqual([], self.walk.fields["things.port_out.init"])
        self.assertEqual([], self.walk.fields["parts.part_b.weight"])

    def test_unknown_names_each_kind_of_surprise(self) -> None:
        self.assertEqual(
            [
                f"{self.T1}: things.thing.ports[?]",
                f"{self.T1}: things.thing.colour",
                "parts/C.yaml: parts.kind='c'",
                "parts/L.yaml: not a mapping",
            ],
            self.walk.unknown,
        )


class TestProbeHealth(unittest.TestCase):
    """The probe and the installation it reads are what they claim."""

    def test_the_probe_reads_the_pinned_installation_and_the_model_is_clean(self) -> None:
        installation = toolchain()
        facts = report()
        self.assertEqual(gate.pinned_version(), installation.version)
        self.assertEqual(
            installation.version,
            facts["swcraftVersion"],
            f"swcraft --version answers {installation.version}, the probe's swcraft_tools is {facts['swcraftVersion']}",
        )
        gate.assert_tools_path_inside(facts["swcraftToolsPath"], installation.python)
        self.assertEqual("installed", facts["contractSource"])
        self.assertEqual([], facts["unknown"], "keys the installed contract does not declare")

        contract = gate.dump_contract(installation)
        self.assertEqual(contract["contractVersion"], facts["contractVersion"])
        kinds = {probe.bare(kind["id"]) for layer in contract["layers"] for kind in layer["kinds"]}
        fields = {
            probe.bare(field["id"])
            for layer in contract["layers"]
            for kind in layer["kinds"]
            for field in kind["fields"]
        }
        rules = {probe.bare(rule["id"]) for rule in contract["rules"]}
        self.assertEqual(kinds, set(facts["kinds"]))
        self.assertEqual(fields, set(facts["fields"]))
        self.assertEqual(rules, set(facts["rules"]))

        checked = gate.check_model(installation)
        self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
        self.assertEqual([], gate.rule_records(installation))
        expected = expected_warnings()
        self.assertEqual(4, len(expected))
        self.assertEqual(expected, sorted(warning_lines(checked.stdout + checked.stderr)))
        self.assertIn(findings_total(), checked.stderr.splitlines())
        strict = gate.check_model(installation, gate.MANIFEST, "--warnings-as-errors")
        self.assertEqual(1, strict.returncode, strict.stdout + strict.stderr)
        self.assertEqual(expected, sorted(warning_lines(strict.stdout + strict.stderr)))
        self.assertIn(findings_total(), strict.stderr.splitlines())
        self.assertIn(f"{len(expected)} warning(s) treated as errors", strict.stdout + strict.stderr)

        print(
            f"\nmodel coverage under SWCraft {installation.version}, contract {facts['contractVersion']}: "
            f"{len(kinds) - len(missing(facts, 'kinds'))} / {len(kinds)} kinds, "
            f"{len(fields) - len(missing(facts, 'fields'))} / {len(fields)} fields",
            file=sys.stderr,
        )

    def test_the_stated_element_count_is_the_number_of_files_walked(self) -> None:
        walked = {rel for carriers in report()["kinds"].values() for rel in carriers}
        stated = f"{len(walked)} elements"
        for page in ("README.md", "docs/guide/install-on-a-workstation.md"):
            with self.subTest(page=page):
                text = " ".join((gate.PROJECT_ROOT / page).read_text(encoding="utf-8").split())
                self.assertIn(stated, text)


class TestNoIdMissing(unittest.TestCase):
    """The target: every kind and every field of the installed contract is carried."""

    def test_every_kind_and_every_field_is_carried(self) -> None:
        facts = report()
        absent = sorted(missing(facts, "kinds")) + sorted(missing(facts, "fields"))
        self.assertEqual([], absent, f"{len(absent)} ids missing:\n" + "\n".join(absent))


class TestNegativeControl(unittest.TestCase):
    """The probe reports a loss: on a copy, exactly the ids one file alone carried go missing."""

    def _probe_copy(self, change: Callable[[Path], None]) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "model"
            shutil.copytree(gate.MODEL_ROOT, copy)
            change(copy)
            return gate.run_probe(toolchain(), model_root=copy)

    def test_deleting_one_element_file_loses_exactly_what_it_alone_carried(self) -> None:
        facts = report()
        # The file that alone carries the most ids, so the control is not a trivial one.
        files = sorted({rel for carriers in facts["kinds"].values() for rel in carriers})
        rel = max(
            files,
            key=lambda name: (
                len(sole_carried(facts, "kinds", name)) + len(sole_carried(facts, "fields", name)),
                name,
            ),
        )
        expected_kinds = sole_carried(facts, "kinds", rel)
        self.assertTrue(expected_kinds, f"{rel} carries no kind alone")
        changed = self._probe_copy(lambda copy: (copy / rel).unlink())
        self.assertEqual(expected_kinds, missing(changed, "kinds"))
        self.assertEqual(sole_carried(facts, "fields", rel), missing(changed, "fields"))

    def test_removing_one_key_loses_exactly_that_field(self) -> None:
        facts = report()
        # A top-level scalar key that one file alone carries: one line, nothing indented under it.
        for identifier, carriers in sorted(facts["fields"].items()):
            if len(carriers) != 1:
                continue
            name = identifier.rsplit(".", 1)[1]
            lines = (gate.MODEL_ROOT / carriers[0]).read_text(encoding="utf-8").splitlines(keepends=True)
            at = [index for index, line in enumerate(lines) if re.match(rf"{re.escape(name)}: \S", line)]
            if len(at) == 1 and (at[0] + 1 == len(lines) or not lines[at[0] + 1][:1].isspace()):
                break
        else:
            self.fail("no top-level scalar key is carried by one file alone")
        rel, index = carriers[0], at[0]

        def strip(copy: Path) -> None:
            path = copy / rel
            path.write_text("".join(lines[:index] + lines[index + 1 :]), encoding="utf-8", newline="\n")

        changed = self._probe_copy(strip)
        self.assertEqual(set(), missing(changed, "kinds"))
        self.assertEqual({identifier}, missing(changed, "fields"))


class TestInjectedContract(unittest.TestCase):
    """The ``unknown`` guard, proven on something other than the committed model.

    Against a contract that does not declare ``handle_termination_and_restart``
    -- an older one, as a stale installation would ship -- the key-presence walk
    alone would silently drop the key; ``unknown`` names it in every application
    component instead.
    """

    KEY = "handle_termination_and_restart"

    def test_unknown_names_a_key_the_contract_does_not_declare(self) -> None:
        installation = toolchain()
        contract = gate.dump_contract(installation)
        removed = 0
        for layer in contract["layers"]:
            for kind in layer["kinds"]:
                kept = [field for field in kind["fields"] if field["id"] != f"field:swc.swc.{self.KEY}"]
                removed += len(kind["fields"]) - len(kept)
                kind["fields"] = kept
        self.assertEqual(1, removed)
        with tempfile.TemporaryDirectory() as tmp:
            contract_file = Path(tmp) / "older-contract.json"
            contract_file.write_text(json.dumps(contract), encoding="utf-8", newline="\n")
            facts = gate.run_probe(installation, "--contract-file", str(contract_file))
        self.assertEqual("file", facts["contractSource"])
        components = sorted(
            path.relative_to(gate.MODEL_ROOT).as_posix()
            for path in (gate.MODEL_ROOT / "swc" / "application").glob("*.yaml")
        )
        self.assertTrue(components)
        self.assertEqual([f"{component}: swc.swc.{self.KEY}" for component in components], facts["unknown"])


if __name__ == "__main__":
    unittest.main()
