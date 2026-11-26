"""Diagrams in VS Code: the marks the tab reads, on the page ``demos/README.md`` walks.

The section *Diagrams in VS Code* of ``demos/README.md`` Ctrl+clicks ``ConfirmSnapshotStored``
on the sequence ``thermal_status_display`` and comes back with *Show in Diagram*. The tab
itself is not automated; what it acts on is in the generated pages, and that is held here:

* without SWCraft: the page names the sequence, the runnable and its file; the sequence
  walks the three runnables in the order the page gives; the file declares the runnable
  on the line the page quotes;
* with the SWCraft on ``PATH`` (``swcraft_on_path``: skipped without it or with another
  release, a failure under ``SHOWCASE_REQUIRE_SWCRAFT=1``), ``swcraft generate diagrams``
  on a copy of the project:
  - the sequence page's ``swcraft-model`` block maps the drawn ``ConfirmSnapshotStored``
    step -- by its ordinal among the inlined drawing's ``[data-role]`` elements, which is
    how the page script counts -- to ``DiagnosticManager.yaml``'s member
    ``runnables/ConfirmSnapshotStored``: what a Ctrl+click opens;
  - the index's ``swcraft-elements`` block lists that member on this one sequence alone:
    what *Show in Diagram* opens, without asking which diagram;
  - the page draws the three steps in the page's order and no call (no operation of
    ``INvStorage`` is named on it), and names no absolute path.

What this does not reach: the tab's bridge (the open, the selection, the ``diagram``
link, **Back**/**Forward**, the release check and its **Generate**), which is the
extension's and the maintainer's look; and the line the editor lands on, which the
extension resolves from the member path -- the test holds only that the file declares
the runnable once.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate

PROJECT_ROOT = gate.PROJECT_ROOT
PAGE = PROJECT_ROOT / "demos" / "README.md"
SEQUENCE = "thermal_status_display"
SEQUENCE_FILE = PROJECT_ROOT / "model" / "sequences" / f"{SEQUENCE}.yaml"
RUNNABLE = "ConfirmSnapshotStored"
MODEL_FILE = "swc/application/DiagnosticManager.yaml"
MEMBER = f"runnables/{RUNNABLE}"
DECLARATION = f"- name: {RUNNABLE}"
STEPS = ("ProcessDiagnosticEvent", RUNNABLE, "UpdateThermalStatus")
CALLED_OPERATIONS = ("WriteBlock", "GetErrorStatus")
#: A path of the machine the pages were made on (as the requirements exchange's test spells it).
LOCAL_PATH_RE = re.compile(r"/(?:Users|home|private|tmp)/|/var/folders/|[A-Z]:\\Users\\")

ROLE_ELEMENT_RE = re.compile(r"<[A-Za-z][\w:-]*\b[^>]*\bdata-role=\"([^\"]*)\"[^>]*>")
NAME_RE = re.compile(r"\bdata-name=\"([^\"]*)\"")


def page_section() -> str:
    text = PAGE.read_text(encoding="utf-8")
    start = text.index("## Diagrams in VS Code")
    end = text.index("\n## ", start + 1)
    return text[start:end]


def script_block(page: str, block_id: str) -> dict:
    match = re.search(rf'<script type="application/json" id="{block_id}">(.*?)</script>', page, re.S)
    if match is None:
        raise AssertionError(f"no {block_id} block on the page")
    return json.loads(match.group(1))


def drawn_elements(page: str) -> list[tuple[str, str]]:
    """``(role, name)`` of each ``[data-role]`` element of the inlined drawing, in document order."""
    start = page.index("<svg")
    drawing = page[start : page.index("</svg>", start)]
    elements = []
    for match in ROLE_ELEMENT_RE.finditer(drawing):
        name = NAME_RE.search(match.group(0))
        elements.append((match.group(1), html.unescape(name.group(1)) if name else ""))
    return elements


class TestThePageAndTheModel(unittest.TestCase):
    """What holds without SWCraft: the page's names exist in the model as it says."""

    def test_the_page_names_the_sequence_the_runnable_and_its_file(self) -> None:
        section = page_section()
        for name in (SEQUENCE, RUNNABLE, f"model/{MODEL_FILE}", f"`{DECLARATION}`", *STEPS):
            with self.subTest(name=name):
                self.assertIn(name, section)

    def test_the_sequence_walks_the_three_steps_in_the_pages_order(self) -> None:
        runnables = re.findall(r"^\s+runnable: (\S+)$", SEQUENCE_FILE.read_text(encoding="utf-8"), re.M)
        self.assertEqual(list(STEPS), runnables)

    def test_the_file_declares_the_runnable_once(self) -> None:
        lines = (PROJECT_ROOT / "model" / MODEL_FILE).read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, lines.count(DECLARATION))


class TestTheGeneratedPages(unittest.TestCase):
    """The marks the tab reads, on pages generated from a copy of the committed model."""

    @classmethod
    def setUpClass(cls) -> None:
        toolchain = gate.toolchain_or_skip()
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        project = Path(temporary.name)
        shutil.copy2(PROJECT_ROOT / "swcraft.yaml", project / "swcraft.yaml")
        shutil.copytree(PROJECT_ROOT / "model", project / "model")
        completed = subprocess.run(
            [str(toolchain.swcraft), "generate", "diagrams", "--project", "swcraft.yaml"],
            cwd=project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=gate.COMMAND_TIMEOUT,
        )
        if completed.returncode != 0:
            raise AssertionError(f"swcraft generate diagrams exited {completed.returncode}:\n{completed.stderr}")
        views = project / "views"
        cls.project = project
        cls.sequence_page = (views / f"sequence-{SEQUENCE}.html").read_text(encoding="utf-8")
        cls.index_page = (views / "index.html").read_text(encoding="utf-8")

    def test_a_ctrl_click_on_the_step_opens_the_runnable(self) -> None:
        elements = drawn_elements(self.sequence_page)
        ordinals = [i for i, (_, name) in enumerate(elements) if name.split(" — ")[0] == RUNNABLE]
        self.assertEqual(1, len(ordinals), elements)
        self.assertEqual("activation", elements[ordinals[0]][0])
        model = script_block(self.sequence_page, "swcraft-model")
        self.assertEqual({"file": MODEL_FILE, "member": MEMBER}, model[str(ordinals[0])])

    def test_show_in_diagram_finds_it_on_this_sequence_alone(self) -> None:
        elements = script_block(self.index_page, "swcraft-elements")
        self.assertEqual([f"sequence-{SEQUENCE}"], elements[MODEL_FILE]["members"][MEMBER])

    def test_the_sequence_draws_the_three_steps_and_no_call(self) -> None:
        steps = [name.split(" — ")[0] for role, name in drawn_elements(self.sequence_page) if role == "activation"]
        self.assertEqual(list(STEPS), steps)
        for operation in CALLED_OPERATIONS:
            with self.subTest(operation=operation):
                self.assertNotIn(operation, self.sequence_page)

    def test_the_pages_name_no_absolute_path(self) -> None:
        """Neither the copy's own folder nor any path of a machine: a home, a temporary folder, a drive."""
        for page in (self.sequence_page, self.index_page):
            for spelling in (self.project.as_posix(), str(self.project), self.project.resolve().as_posix(), PROJECT_ROOT.as_posix()):
                self.assertNotIn(spelling, page)
            self.assertIsNone(LOCAL_PATH_RE.search(page))


if __name__ == "__main__":
    unittest.main()
