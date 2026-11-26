"""Stdlib tests for the project's two pins, its configuration, and what it must not carry.

The project installs nothing and runs nothing of its own: the SWCraft toolchain is
one installation per machine, reached as the bare ``swcraft`` on PATH, and moon is
the other per-machine tool. What is left to pin is two lines -- ``toolchain_version``
in ``swcraft.yaml`` and ``moon`` in ``.prototools`` -- and this file holds them.

It also holds the pinned release where the open user files name it: every version written as
SWCraft's (:data:`RELEASE_TOKENS`) is the kit builder's default, which the kit's own tests tie
to the manifest. History-table rows and "since x.y.z" record sentences are skipped by pattern;
a version written in another form is not reached.

It also holds the configuration around them: the manifest's outputs and roots, the
build graph in ``moon.yml``, and the workspace settings (the spell checker's ignored
folders, the requirements import's mapping).
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate

PROJECT_ROOT = gate.PROJECT_ROOT
KIT = gate.load_script("build_colleague_kit")

PIN_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*"([^"]+)"\s*$')
#: ``moon.yml``'s lines: a task, one of its keys, one item of a key's list.
TASK_RE = re.compile(r"^  ([a-z][a-z0-9-]*):\s*$")
KEY_RE = re.compile(r"^    ([a-z]+):\s*(.*?)\s*$")
ITEM_RE = re.compile(r"^      - '([^']*)'\s*$")

_VERSION = r"(\d+\.\d+\.\d+)"
#: The forms in which a user file names SWCraft's release; each captures the version.
RELEASE_TOKENS = re.compile(
    "|".join(
        (
            rf"\bSWCraft[ *`]+{_VERSION}",
            rf"(?<![-/\w])swcraft {_VERSION}",
            rf"\bswcraft-{_VERSION}-",
            rf"\bswcraft-vscode-{_VERSION}\.vsix",
            rf"-kit-{_VERSION}\.zip",
            rf"/releases/tag/v{_VERSION}",
            rf"\btoolchain_version\W+{_VERSION}",
            rf"\b(?:release|version)\W{{1,3}}{_VERSION}",
            rf"\bthe {_VERSION} archive",
            rf'"swcraftVersion":\s*"{_VERSION}"',
        )
    )
)
#: A history-table row: ``| <revision> | <date> | ...``.
HISTORY_ROW_RE = re.compile(r"^\|\s*\d+\.\d+\s*\|\s*\d{4}-\d{2}-\d{2}\s*\|")
#: A record sentence's opening right before the token: "since 0.7.0", "Since SWCraft 0.23.0".
SINCE_RE = re.compile(r"\b[Ss]ince\s+[`*]*$")
#: The open user files that name the release; the requirements exchange's generated sites and
#: deliveries keep the release they were made with, deliberately.
USER_FILE_GLOBS = (
    "README.md",
    "kit/README.md",
    "demos/*.md",
    "demos/*.html",
    "demos/requirements-exchange/prepared-links.json",
    "docs/guide/**/*.md",
    "docs/briefs/*.md",
)

#: Files earlier releases retired. The last four went when the Python preflight
#: did: a project whose toolchain needs no Python on the machine asks for none
#: itself, and the maintainer's kit builder under ``scripts/`` is not a user step.
RETIRED = (
    "bootstrap.py",
    "requirements-swcraft.txt",
    "clean_outputs.py",
    ".vscode/mcp.json.example",
    "setup-showcase",
    "setup-showcase.ps1",
    "scripts/setup_showcase.py",
    "tests/test_setup_showcase.py",
)


def prototools_pins() -> dict[str, str]:
    text = (PROJECT_ROOT / ".prototools").read_text(encoding="utf-8")
    return dict(match.groups() for line in text.splitlines() if (match := PIN_RE.match(line)))


def moon_tasks() -> dict[str, dict[str, list[str]]]:
    """The tasks of ``moon.yml`` with their list keys, read line by line (stdlib only)."""
    tasks: dict[str, dict[str, list[str]]] = {}
    task: dict[str, list[str]] | None = None
    key: str | None = None
    in_tasks = False
    for line in (PROJECT_ROOT / "moon.yml").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            in_tasks = line.rstrip() == "tasks:"
            task = key = None
            continue
        if not in_tasks:
            continue
        if match := TASK_RE.match(line):
            task = tasks.setdefault(match.group(1), {})
            key = None
        elif task is not None and (match := KEY_RE.match(line)):
            key = match.group(1)
            task.setdefault(key, [])
        elif task is not None and key is not None and (match := ITEM_RE.match(line)):
            task[key].append(match.group(1))
    return tasks


def manifest() -> tuple[dict[str, str], dict[str, str]]:
    """``swcraft.yaml``'s top-level ``*_root`` keys and its ``outputs:`` mapping, read line by line (stdlib only)."""
    roots: dict[str, str] = {}
    outputs: dict[str, str] = {}
    inside = False
    for line in (PROJECT_ROOT / "swcraft.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if not line.startswith(" "):
            inside = line.rstrip() == "outputs:"
            name, _, value = line.partition(":")
            if name.endswith("_root"):
                roots[name] = value.split("#", 1)[0].strip().strip("'\"")
        elif inside:
            name, _, value = line.strip().partition(":")
            outputs[name.strip()] = value.strip()
    return roots, outputs


def release_tokens(text: str) -> list[tuple[int, str, str]]:
    """Each release token of ``text`` outside history rows and since-sentences: (line, token, version)."""
    found = []
    for match in RELEASE_TOKENS.finditer(text):
        start = text.rfind("\n", 0, match.start()) + 1
        if HISTORY_ROW_RE.match(text[start : match.start()]) or SINCE_RE.search(text[start : match.start()]):
            continue
        version = next(group for group in match.groups() if group)
        found.append((text.count("\n", 0, match.start()) + 1, match.group(0), version))
    return found


def user_files() -> list[Path]:
    return sorted({path for pattern in USER_FILE_GLOBS for path in PROJECT_ROOT.glob(pattern)}, key=Path.as_posix)


class TestPins(unittest.TestCase):
    def test_the_manifest_pins_one_exact_release(self) -> None:
        manifest = (PROJECT_ROOT / "swcraft.yaml").read_text(encoding="utf-8")
        self.assertEqual(KIT.DEFAULT_VERSION, KIT.parse_toolchain_version(manifest))

    def test_the_user_files_name_the_pinned_release(self) -> None:
        total = 0
        for path in user_files():
            tokens = release_tokens(path.read_text(encoding="utf-8"))
            total += len(tokens)
            with self.subTest(file=path.relative_to(PROJECT_ROOT).as_posix()):
                self.assertEqual([], [token for token in tokens if token[2] != KIT.DEFAULT_VERSION])
        self.assertGreater(total, 0, "the scan found no release token at all")

    def test_the_release_scan_finds_a_stale_version_and_skips_records(self) -> None:
        page = (PROJECT_ROOT / KIT.INSTALL_PAGE_PATH).read_text(encoding="utf-8")
        current = f"swcraft-{KIT.DEFAULT_VERSION}-"
        self.assertIn(current, page)
        stale = page.replace(current, "swcraft-0.0.1-", 1)
        self.assertIn("0.0.1", [token[2] for token in release_tokens(stale)])
        records = (
            "| 0.9 | 2026-01-01 | Migrated to SWCraft 0.0.1: the pin. |\n"
            "Since SWCraft 0.0.1 the scaffold writes them; since `0.0.1` nothing else.\n"
        )
        self.assertEqual([], release_tokens(records))

    def test_prototools_pins_moon_and_no_interpreter(self) -> None:
        self.assertEqual({"moon": "2.3.5"}, prototools_pins())

    def test_project_installs_nothing_and_carries_no_preflight(self) -> None:
        for retired in RETIRED:
            with self.subTest(retired=retired):
                self.assertFalse((PROJECT_ROOT / retired).exists(), retired)

    def test_the_manifest_names_the_needs_file_and_no_rst(self) -> None:
        _, outputs = manifest()
        self.assertEqual("dist/needs.json", outputs.get("needs"))
        self.assertNotIn("rst", outputs)

    def test_the_build_graph_generates_the_needs_file_not_the_rst(self) -> None:
        tasks = moon_tasks()
        self.assertNotIn("generate-rst", tasks)
        moon = (PROJECT_ROOT / "moon.yml").read_text(encoding="utf-8")
        self.assertNotIn("generate-rst", moon)
        self.assertIn("generate-needs", tasks)
        needs = tasks["generate-needs"]
        self.assertEqual(["generate", "needs", "--project", "swcraft.yaml"], needs["args"])
        self.assertEqual(["check-model"], needs["deps"])
        self.assertEqual(["dist/needs.json"], needs["outputs"])
        for task in ("validate-arxml", "build"):
            with self.subTest(task=task):
                self.assertIn("generate-needs", tasks[task]["deps"])

    def test_the_spell_checker_ignores_the_model_and_the_generated_folders(self) -> None:
        """The release note's step 6: the template's ``cSpell.ignorePaths``, from the manifest's roots."""
        settings = json.loads((PROJECT_ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8"))
        ignored = settings.get("cSpell.ignorePaths", [])
        roots, _ = manifest()
        for key in ("model_root", "dist_root", "views_root"):
            with self.subTest(root=key):
                self.assertIn(key, roots)
                self.assertIn(f"{roots[key]}/**", ignored)

    def test_the_requirements_import_mapping_exists_outside_the_model(self) -> None:
        """*Import Requirements…* offers the workspace's mapping: a project-relative path that exists.

        Outside ``model_root``, so the mapping is never read as a model file.
        """
        settings = json.loads((PROJECT_ROOT / ".vscode" / "settings.json").read_text(encoding="utf-8"))
        mapping = settings.get("swcraft.requirementsImport.mapping")
        self.assertEqual("demos/requirements-exchange/team.needs-mapping.yaml", mapping)
        self.assertTrue((PROJECT_ROOT / mapping).is_file(), mapping)
        model_root = (PROJECT_ROOT / manifest()[0]["model_root"]).resolve()
        self.assertFalse((PROJECT_ROOT / mapping).resolve().is_relative_to(model_root), mapping)

    def test_toolchain_version_is_one_exact_release(self) -> None:
        self.assertEqual("1.2.3", KIT.parse_toolchain_version('name: x\ntoolchain_version: "1.2.3"\n'))
        self.assertEqual("1.2.3", KIT.parse_toolchain_version("toolchain_version: 1.2.3  # unquoted\n"))
        with self.assertRaisesRegex(KIT.ManifestError, "no toolchain_version"):
            KIT.parse_toolchain_version("name: x\n")
        with self.assertRaisesRegex(KIT.ManifestError, "more than once"):
            KIT.parse_toolchain_version('toolchain_version: "1.2.3"\ntoolchain_version: "1.2.3"\n')
        for bad in ('">=0.8"', '"0.8"', '"0.8.*"', '"latest"'):
            with self.subTest(bad=bad), self.assertRaisesRegex(KIT.ManifestError, "exact release"):
                KIT.parse_toolchain_version(f"toolchain_version: {bad}\n")


if __name__ == "__main__":
    unittest.main()
