"""The chat scenario: the facts ``demos/chat-with-the-model.md`` quotes, from their command-line equivalents.

The page runs one scenario in Copilot and in Kiro. A chat's own sentences are not
reproducible, so this test holds what the chat's answers rest on:

* without SWCraft: the page quotes each command, each expected answer and each guard
  sentence held below, and names the six client files the project commits; each fact the
  page states for the architect's question is on the page, with the value a query line
  prints for it; the call names and the polled result point, which no query line prints,
  are in the file the page sends the reader to, under ``ProcessDiagnosticEvent``'s ``calls``;
* with the SWCraft on ``PATH`` (``swcraft_on_path``: skipped without it or with another
  release, a failure under ``SHOWCASE_REQUIRE_SWCRAFT=1``):
  - the architect's question: ``swcraft query`` answers the calls on ``rNvStorage``,
    both asynchronous, the polled one and the call-returned event as the page says (each
    query's rows, :data:`QUERIES`);
  - the impact question: ``swcraft impact INvStorage`` prints the page's block, byte for
    byte, and ``NvM`` is not in it;
  - the proposal the page rejects passes ``swcraft check-model`` on a copy of the model,
    so it reaches the review tab instead of being refused;
  - Copilot's guard (``swcraft guard``) denies a read of the model file with the page's
    sentence, allows a read outside the model, and does not judge an edit;
  - Kiro's guard (``swcraft guard --host kiro``) denies the page's direct edit with exit 2
    and its sentence on standard error, denies a read of the model, and allows a write
    outside it;
  - both deny a path outside the model that names it (Copilot's read, Kiro's edit) and
    allow its controls (:data:`PATHS_NOT_NAMING_THE_MODEL`);
  - Kiro's guard denies a ``~`` path when the home folder's name holds a pattern
    character, and allows the same file written in full and a ``~`` path under an
    ordinary home folder.

What this does not reach: the chats themselves (which tools an assistant calls, its
wording), the review tab and its **Reject**, Kiro's trust and reload, and the
extension's installation into Kiro -- those steps are the maintainer's look. The guard
payloads are the shapes SWCraft's own tests give each client's tools, not ones captured
from a client here.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate

PROJECT_ROOT = gate.PROJECT_ROOT
PAGE = PROJECT_ROOT / "demos" / "chat-with-the-model.md"
MODEL_FILE = "model/interfaces/INvStorage.yaml"
#: Paths outside the model that only the guard's path rules deny: the model folder's name as a
#: part of another path, and a path ending like a model file.
PATHS_NAMING_THE_MODEL = ("notes/model/x.md", "elsewhere/interfaces/INvStorage.yaml")
#: Their controls, allowed: the folder's name only inside a longer name, and an ending no model
#: file has.
PATHS_NOT_NAMING_THE_MODEL = ("notes/models/x.md", "elsewhere/interfaces/NotAModelFile.yaml")

CLIENT_FILES = (
    ".github/agents/swcraft-architect.agent.md",
    ".github/copilot-instructions.md",
    ".github/hooks/swcraft.json",
    ".kiro/settings/mcp.json",
    ".kiro/steering/swcraft.md",
    ".kiro/hooks/swcraft-guard.json",
)

#: The architect's question: each command the page quotes and the rows it answers.
QUERIES = {
    "swcraft query swc --members runnables.calls --where port=rNvStorage --project swcraft.yaml": [
        'swc: DiagnosticManager.ProcessDiagnosticEvent.{"operation": "WriteBlock", "port": "rNvStorage"}',
        'swc: DiagnosticManager.ProcessDiagnosticEvent.{"operation": "GetErrorStatus", "port": "rNvStorage"}',
    ],
    "swcraft query swc --members runnables.calls --where asynchronous=true --project swcraft.yaml": [
        'swc: DiagnosticManager.ProcessDiagnosticEvent.{"operation": "WriteBlock", "port": "rNvStorage"}',
        'swc: DiagnosticManager.ProcessDiagnosticEvent.{"operation": "GetErrorStatus", "port": "rNvStorage"}',
    ],
    "swcraft query swc --members runnables.calls --where poll=true --project swcraft.yaml": [
        'swc: DiagnosticManager.ProcessDiagnosticEvent.{"operation": "GetErrorStatus", "port": "rNvStorage"}',
    ],
    "swcraft query swc --members runnables.events --where type=call_returned --project swcraft.yaml": [
        'swc: DiagnosticManager.ConfirmSnapshotStored.{"name": "ASRT_SnapshotStored", "operation": "WriteBlock", '
        '"port": "rNvStorage", "result": "Result_StoreSnapshot", "type": "call_returned"}',
    ],
}
#: The facts the page states for the architect's question, each with the value a query row
#: prints for it (the rows of :data:`QUERIES`).
PAGE_FACTS = {
    "**`DiagnosticManager.ProcessDiagnosticEvent`** makes both calls, through its port `rNvStorage`.":
        'swc: DiagnosticManager.ProcessDiagnosticEvent.{"operation": "WriteBlock", "port": "rNvStorage"}',
    "Both are **asynchronous**": '"operation": "GetErrorStatus", "port": "rNvStorage"',
    "`GetErrorStatus` (the call `Call_NvErrorStatus`) is **polled**": '"operation": "GetErrorStatus"',
    "**`DiagnosticManager.ConfirmSnapshotStored`** takes the result of the write": "swc: DiagnosticManager.ConfirmSnapshotStored.",
    "**call-returned** event (`ASRT_SnapshotStored`) when `WriteBlock` returns": '"name": "ASRT_SnapshotStored"',
    "`Result_StoreSnapshot`": '"result": "Result_StoreSnapshot"',
}
#: What the page says a query line does not print, and the file it sends the reader to instead:
#: each value under ``ProcessDiagnosticEvent``'s ``calls``, by key.
NOT_PRINTED = {"Call_StoreSnapshot": "name", "Call_NvErrorStatus": "name", "Result_NvErrorStatus": "result"}
CALLS_FILE = "model/swc/application/DiagnosticManager.yaml"
CALLS_RUNNABLE = "ProcessDiagnosticEvent"

IMPACT_COMMAND = "swcraft impact INvStorage --project swcraft.yaml"
IMPACT_TEXT = """\
Impact of 'INvStorage':

interface:
  swc DiagnosticManager (via port rNvStorage)
  task Task_100ms (runnables ProcessDiagnosticEvent, ConfirmSnapshotStored)
  connector ChassisToDiagnostics (via port DiagnosticManager.rThermalProtectionEvent)
  connector DiagnosticsToCluster (via port DiagnosticManager.pBrakeDiagnostics)
  connector NvMToDiagnostics (via port DiagnosticManager.rNvStorage)
  composition VehicleControl (member DiagnosticManager)
  sequence thermal_status_display (steps: ProcessDiagnosticEvent, ConfirmSnapshotStored)
"""

PROPOSAL = "Add an operation EraseBlock to the interface INvStorage."
READ_DENIED = (
    "SWCraft: the model under `model` is read through the SWCraft tools, never by file tools; "
    "a saved SWCraft answer may be viewed."
)
EDIT_DENIED = (
    "SWCraft: in this project the model directory (`model`) is changed through the SWCraft tools, "
    "whose changes the panel reviews; this edit writes `model/interfaces/INvStorage.yaml` there. "
    "Use the SWCraft MCP tool `change_set` instead."
)


def page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


def runnable_calls(text: str, runnable: str) -> list[dict[str, str]]:
    """The ``calls`` of *runnable* in a component file, each call's scalar keys (stdlib only).

    Enough for the model's own layout: runnables are ``- name:`` items at the top of
    ``runnables:``, their keys two spaces in, a call a ``- `` item under ``  calls:``.
    """
    lines = text.splitlines()
    start = lines.index(f"- name: {runnable}")
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].startswith("  ")), len(lines))
    block = lines[start + 1 : end]
    calls: list[dict[str, str]] = []
    inside = False
    for line in block:
        if line == "  calls:":
            inside = True
        elif inside and line.startswith("  - "):
            calls.append({})
            line = "    " + line[4:]
        elif inside and not line.startswith("    "):
            inside = False
        if inside and calls and line.startswith("    ") and not line.startswith("     "):
            key, _, value = line.strip().partition(": ")
            calls[-1][key] = value
    return calls


def run(
    command: list[str], *, cwd: Path = PROJECT_ROOT, stdin: str | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=stdin,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=gate.COMMAND_TIMEOUT,
    )


class TestThePageQuotes(unittest.TestCase):
    """What holds without SWCraft: the page carries every command, answer and sentence held here."""

    def test_the_page_quotes_each_command_and_its_answer(self) -> None:
        text = page_text()
        for command in (*QUERIES, IMPACT_COMMAND.split(" --project")[0]):
            with self.subTest(command=command):
                self.assertIn(command, text)
        self.assertIn(IMPACT_TEXT, text)
        self.assertIn(PROPOSAL, text)

    def test_the_page_states_each_fact_a_query_row_answers(self) -> None:
        text = " ".join(page_text().split())
        rows = [row for answer in QUERIES.values() for row in answer]
        for fact, printed in PAGE_FACTS.items():
            with self.subTest(fact=fact):
                self.assertIn(fact, text)
                self.assertTrue(any(printed in row for row in rows), printed)

    def test_what_a_query_line_does_not_print_is_in_the_file_the_page_names(self) -> None:
        text = page_text()
        self.assertIn(f"`{CALLS_FILE}`, under `{CALLS_RUNNABLE}`'s `calls`", " ".join(text.split()))
        calls = runnable_calls((PROJECT_ROOT / CALLS_FILE).read_text(encoding="utf-8"), CALLS_RUNNABLE)
        self.assertEqual([("rNvStorage", "WriteBlock"), ("rNvStorage", "GetErrorStatus")], [(c["port"], c["operation"]) for c in calls])
        for value, key in NOT_PRINTED.items():
            with self.subTest(value=value):
                self.assertIn(f"`{value}`", text)
                self.assertEqual(1, [call.get(key) for call in calls].count(value))
                self.assertFalse(any(value in row for rows in QUERIES.values() for row in rows))

    def test_the_page_quotes_both_guards_sentences(self) -> None:
        text = page_text()
        self.assertIn(READ_DENIED, text)
        self.assertIn(EDIT_DENIED, text)

    def test_the_client_files_the_page_names_are_committed(self) -> None:
        text = page_text()
        for relative in CLIENT_FILES:
            with self.subTest(file=relative):
                self.assertIn(f"`{relative}`", text)
                self.assertTrue((PROJECT_ROOT / relative).is_file())


class TestTheAnswers(unittest.TestCase):
    """The chat's facts, from the command line, on the committed model."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.toolchain = gate.toolchain_or_skip()

    def swcraft(self, command: str) -> list[str]:
        argv = command.split()
        self.assertEqual("swcraft", argv[0])
        completed = run([str(self.toolchain.swcraft), *argv[1:]])
        self.assertEqual(0, completed.returncode, completed.stderr)
        return completed.stdout.splitlines()

    def rows(self, command: str) -> list[str]:
        return [line for line in self.swcraft(command) if line.startswith("swc: ")]

    def test_the_architects_question(self) -> None:
        for command, expected in QUERIES.items():
            with self.subTest(command=command):
                self.assertEqual(expected, self.rows(command))

    def test_the_impact_question(self) -> None:
        completed = run([str(self.toolchain.swcraft), *IMPACT_COMMAND.split()[1:]])
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(IMPACT_TEXT, completed.stdout)
        self.assertNotIn(" NvM ", completed.stdout)

    def test_the_rejected_proposal_passes_the_model_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            shutil.copy2(PROJECT_ROOT / "swcraft.yaml", project / "swcraft.yaml")
            shutil.copytree(PROJECT_ROOT / "model", project / "model")
            interface = project / MODEL_FILE
            text = interface.read_text(encoding="utf-8")
            self.assertEqual(1, text.count("- GetErrorStatus\n"))
            self.assertNotIn("EraseBlock", text)
            interface.write_text(
                text.replace("- GetErrorStatus\n", "- GetErrorStatus\n- EraseBlock\n"), encoding="utf-8", newline="\n"
            )
            completed = run([str(self.toolchain.swcraft), "check-model", "--project", "swcraft.yaml"], cwd=project)
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual("Validation passed (no artifacts generated).", completed.stdout.strip())
        self.assertIn("0 error(s), 4 warning(s).", completed.stderr)


class TestTheGuards(unittest.TestCase):
    """Each client's guard decides the page's steps as the page says; nothing is written."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.toolchain = gate.toolchain_or_skip()

    def guard(
        self, tool: str, arguments: dict[str, str], *host: str, home: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        payload = {"tool_name": tool, "tool_input": arguments, "hook_event_name": "PreToolUse", "cwd": str(PROJECT_ROOT)}
        env = None if home is None else {**os.environ, "HOME": home, "USERPROFILE": home}
        return run([str(self.toolchain.swcraft), "guard", *host], stdin=json.dumps(payload), env=env)

    def copilot(self, tool: str, arguments: dict[str, str]) -> dict:
        completed = self.guard(tool, arguments)
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def kiro(
        self, tool: str, arguments: dict[str, str], home: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return self.guard(tool, arguments, "--host", "kiro", home=home)

    def test_copilot_denies_a_read_of_the_model_file(self) -> None:
        answer = self.copilot("view", {"path": MODEL_FILE})
        self.assertEqual("deny", answer["permissionDecision"])
        self.assertEqual(READ_DENIED, answer["permissionDecisionReason"])

    def test_copilot_allows_a_read_outside_the_model(self) -> None:
        self.assertEqual({}, self.copilot("view", {"path": "README.md"}))

    def test_copilot_does_not_judge_an_edit(self) -> None:
        self.assertEqual({}, self.copilot("Edit", {"path": MODEL_FILE}))

    def test_kiro_denies_the_direct_edit(self) -> None:
        before = (PROJECT_ROOT / MODEL_FILE).read_bytes()
        completed = self.kiro("fs_write", {"path": MODEL_FILE, "text": "x"})
        self.assertEqual(2, completed.returncode)
        self.assertEqual(EDIT_DENIED, completed.stderr.strip())
        self.assertEqual(before, (PROJECT_ROOT / MODEL_FILE).read_bytes())

    def test_kiro_denies_a_read_of_the_model_file(self) -> None:
        completed = self.kiro("read_file", {"path": MODEL_FILE})
        self.assertEqual(2, completed.returncode)
        self.assertEqual(READ_DENIED, completed.stderr.strip())

    def test_kiro_allows_a_write_outside_the_model(self) -> None:
        completed = self.kiro("fs_write", {"path": "notes/chat.md", "text": "x"})
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stderr.strip())

    def test_copilot_denies_a_read_of_a_path_that_names_the_model(self) -> None:
        for path in PATHS_NAMING_THE_MODEL:
            with self.subTest(path=path):
                self.assertEqual("deny", self.copilot("view", {"path": path}).get("permissionDecision"))

    def test_kiro_denies_an_edit_of_a_path_that_names_the_model(self) -> None:
        for path in PATHS_NAMING_THE_MODEL:
            with self.subTest(path=path):
                completed = self.kiro("fs_write", {"path": path, "text": "x"})
                self.assertEqual(2, completed.returncode, completed.stderr)
                self.assertNotEqual("", completed.stderr.strip())

    def test_copilot_allows_a_read_of_a_path_that_does_not_name_the_model(self) -> None:
        for path in PATHS_NOT_NAMING_THE_MODEL:
            with self.subTest(path=path):
                self.assertEqual({}, self.copilot("view", {"path": path}))

    def test_kiro_allows_an_edit_of_a_path_that_does_not_name_the_model(self) -> None:
        for path in PATHS_NOT_NAMING_THE_MODEL:
            with self.subTest(path=path):
                completed = self.kiro("fs_write", {"path": path, "text": "x"})
                self.assertEqual(0, completed.returncode, completed.stderr)

    def test_kiro_denies_a_home_path_when_the_home_folder_holds_a_pattern_character(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            admin, ordinary = Path(temporary) / "John (Admin)", Path(temporary) / "john"
            cases = (
                (admin, "~/notes.md", 2),
                (admin, str(admin / "notes.md"), 0),
                (ordinary, "~/notes.md", 0),
            )
            for home, path, expected in cases:
                with self.subTest(home=home.name, path=path):
                    home.mkdir(exist_ok=True)
                    completed = self.kiro("fs_write", {"path": path, "text": "x"}, home=str(home))
                    self.assertEqual(expected, completed.returncode, completed.stderr)
                    if expected == 2:
                        self.assertNotEqual("", completed.stderr.strip())


if __name__ == "__main__":
    unittest.main()
