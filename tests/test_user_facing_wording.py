"""Stdlib test: the files a user of this showcase opens name no phase, no plan and no checklist.

The storefront is what a colleague opens, and a roadmap reference in it is noise to
them and a promise to nobody. The scan reads each file's **whole text**, not line by
line, because a wrap inside a YAML comment puts ``# `` between a word and its number
(``since Phase`` / ``# 14``): ``\\s`` alone misses that, so the phase pattern also
admits ``#``.

The scope is the files a user opens -- ``README.md``, the install page, the briefs,
the work instructions, ``kit/``, ``demos/``, ``model/``, ``.github/``, ``.kiro/``, ``moon.yml``,
``experiments/``, and the three project files the colleague kit also ships:
``swcraft.yaml``, ``.vscode/settings.json`` and ``.gitattributes``. Evidence records, notes and plans are maintainer documents and are not
scanned, nor are the kit's three legal files (``LEGAL_FILES``: verbatim licence texts), nor are the requirements exchange's four ready-made site folders
(``demos/requirements-exchange/sites/<state>/`` and ``sites/1.0-original/``), which are Sphinx's generated output. What the scan does **not** reach: a plan or phase named in other words
than the three patterns (``the plan`` alone, a roadmap item by title), and any file
outside the scope.
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate

PROJECT_ROOT = gate.PROJECT_ROOT
# The kit's own allowlists and its list of operating-system litter.
KIT = gate.load_script("build_colleague_kit")

#: The three patterns. The first widens SWCraft's own ``\\bPhase\\s+\\d`` by ``#``;
#: the second is SWCraft's own path pattern; the third catches a plan named in prose.
PATTERNS = (
    re.compile(r"\bPhase[\s#]+\d"),
    re.compile(r"docs/(?:plans|checklists)/"),
    re.compile(r"\b(?:implementation|project|execution|live-demo|showcase|release)\s+plans?\b", re.IGNORECASE),
)

SCOPE_FILES = (
    "README.md",
    "moon.yml",
    "swcraft.yaml",
    ".vscode/settings.json",
    ".gitattributes",
)
SCOPE_DIRS = ("docs/briefs", "docs/guide", "kit", "demos", "experiments", "model", ".github", ".kiro")

#: Operating-system and interpreter litter that is git-ignored, never user-facing and
#: not text: skipped by name (the kit builder's list of litter, and ``__pycache__``). Any
#: other file in scope must decode as UTF-8.
IGNORED_NAMES = frozenset(KIT.IGNORED_NAMES)
IGNORED_DIRS = frozenset({"__pycache__"})
#: Generated, not written: the requirements team's ready-made sites are Sphinx's output
#: (its pages, scripts, style sheets and images), built by
#: ``scripts/generate_requirements_prepared.py``; their text is the deliveries' and the
#: architecture's, which the tests of the exchange hold. Skipped by path: the site
#: folders the kit ships (``DEMO_TREES``), not the needs files beside them.
IGNORED_TREES = tuple(f"{tree}/" for tree in KIT.DEMO_TREES)
#: The kit's legal files: the Apache-2.0 text, the notice and the third-party licences, each verbatim.
#: A hit there could not be fixed by rewording, so they are the only project files the kit ships
#: that the scan does not read.
LEGAL_FILES = frozenset(KIT.LEGAL_FILES)


def scope_files(root: Path) -> list[Path]:
    """Every file of the scope under *root*, in POSIX order."""
    files = [root / relative for relative in SCOPE_FILES if (root / relative).is_file()]
    for relative in SCOPE_DIRS:
        directory = root / relative
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.name in IGNORED_NAMES:
                continue
            if IGNORED_DIRS & set(path.relative_to(root).parts):
                continue
            if path.relative_to(root).as_posix().startswith(IGNORED_TREES):
                continue
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def hits_in(text: str) -> list[tuple[int, str]]:
    """``(line, matched text)`` for every pattern match in *text*, in text order."""
    matches = sorted(
        (match for pattern in PATTERNS for match in pattern.finditer(text)),
        key=lambda match: (match.start(), match.group()),
    )
    return [(text.count("\n", 0, match.start()) + 1, match.group()) for match in matches]


def scan(root: Path) -> list[str]:
    """One ``path:line: 'match'`` line per hit across the scope."""
    report = []
    for path in scope_files(root):
        text = path.read_text(encoding="utf-8")
        for line, matched in hits_in(text):
            report.append(f"{path.relative_to(root).as_posix()}:{line}: {matched!r}")
    return report


class TestPatterns(unittest.TestCase):
    def test_a_phase_wrapped_inside_a_yaml_comment_is_caught(self) -> None:
        self.assertEqual([(1, "Phase\n  # 1")], hits_in("# since Phase\n  # 14 the RST carries\n"))

    def test_each_pattern_catches_its_case(self) -> None:
        for text in (
            "see Phase 3",
            "Phase #12",
            "docs/plans/x.md",
            "docs/checklists/y.md",
            "the Implementation Plan",
            "required by the project plan",
            "the live-demo plans",
            "the release  plan",
        ):
            with self.subTest(text=text):
                self.assertEqual(1, len(hits_in(text)), text)

    def test_ordinary_words_are_not_hits(self) -> None:
        for text in (
            "the phase of the moon",
            "Phase shift",
            "a planned feature",
            "the checklist as returned",
            "docs/briefs/FB.md",
            "plan the work",
        ):
            with self.subTest(text=text):
                self.assertEqual([], hits_in(text), text)

    def test_the_scope_skips_litter_and_reads_every_other_file(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for relative, data in {
                "README.md": b"Phase 1\n",
                "model/.DS_Store": b"\x80\x81 Phase 2",
                "kit/__pycache__/x.pyc": b"\x80 Phase 3",
                "demos/README.md": b"see docs/plans/a.md\n",
                "docs/evidence/run.md": b"Phase 4\n",
                "docs/plans/p.md": b"Phase 5\n",
                "demos/requirements-exchange/sites/1.0/_static/plus.png": b"\x89PNG Phase 6",
                "demos/requirements-exchange/sites/1.0/index.html": b"the release plan\n",
            }.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            self.assertEqual(
                ["README.md:1: 'Phase 1'", "demos/README.md:1: 'docs/plans/'"],
                scan(root),
            )


class TestThisRepository(unittest.TestCase):
    def test_the_scope_is_not_empty(self) -> None:
        names = {path.relative_to(PROJECT_ROOT).as_posix() for path in scope_files(PROJECT_ROOT)}
        for expected in (
            "README.md",
            "moon.yml",
            "demos/README.md",
            "kit/README.md",
            ".github/copilot-instructions.md",
            "swcraft.yaml",
            ".vscode/settings.json",
            ".gitattributes",
        ):
            self.assertIn(expected, names)

    def test_the_scope_covers_every_project_file_the_kit_ships(self) -> None:
        """Every file the kit ships is scanned but the legal files, and the exemption is exactly them."""
        names = {path.relative_to(PROJECT_ROOT).as_posix() for path in scope_files(PROJECT_ROOT)}
        shipped = set(KIT.PROJECT_FILES + KIT.DEMO_FILES)
        shipped |= {path.relative_to(PROJECT_ROOT).as_posix() for path in KIT.OVERLAY_DIR.rglob("*") if path.is_file()}
        self.assertEqual(LEGAL_FILES, shipped - names)

    def test_no_user_facing_file_names_a_phase_a_plan_or_a_checklist(self) -> None:
        report = scan(PROJECT_ROOT)
        self.assertEqual([], report, "\n".join(report))


if __name__ == "__main__":
    unittest.main()
