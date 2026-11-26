"""The chat clients' files are the pinned release's own: Copilot's and Kiro's, nothing else.

The showcase is set up for two chat clients, GitHub Copilot and Kiro, the way SWCraft's
upgrading guide says for a project made with ``swcraft init --integration moon``: the
chosen clients' files are copied from a fresh scaffold made with ``--client``, and a
client's files that are not wanted (Codex's ``.codex/hooks.json``) are deleted.

This test makes that scaffold in a temporary folder with the SWCraft on ``PATH``
(``swcraft_on_path``: skipped without it or with another release, a failure under
``SHOWCASE_REQUIRE_SWCRAFT=1``) and holds every committed client file byte-equal to the
scaffold's. Which files belong to which client is read from the installation's own
``clients.json`` through its interpreter, so a release that adds a file to a client's
row turns this test red instead of leaving the file out.

What this does not reach: the files a client reads that the scaffold does not write
(``.vscode/settings.json`` is the project's own, with the showcase's settings in it),
and whether the clients themselves accept the files -- that is the maintainer's look in
VS Code and Kiro.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate

PROJECT_ROOT = gate.PROJECT_ROOT
#: The clients the showcase is set up for, in ``swcraft init --client`` spelling.
CLIENTS = ("copilot", "kiro")
#: Every file of the two rows at the pinned release (``clients.json``); held equal to the installation's rows.
EXPECTED_FILES = frozenset(
    {
        ".github/agents/swcraft-architect.agent.md",
        ".github/copilot-instructions.md",
        ".github/hooks/swcraft.json",
        ".kiro/settings/mcp.json",
        ".kiro/steering/swcraft.md",
        ".kiro/hooks/swcraft-guard.json",
    }
)
#: Read by the installation's interpreter: the table ``swcraft init --client`` chooses from.
CLIENTS_JSON_SCRIPT = (
    "import importlib.resources, sys; "
    "sys.stdout.write(importlib.resources.files('swcraft_tools')"
    ".joinpath('templates/clients.json').read_text(encoding='utf-8'))"
)


def installed_clients(toolchain: gate.Toolchain) -> dict[str, list[str]]:
    """Each client's files, by name, from the installation's ``clients.json``."""
    completed = subprocess.run(
        [str(toolchain.python), "-I", "-c", CLIENTS_JSON_SCRIPT],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=gate.COMMAND_TIMEOUT,
    )
    if completed.returncode != 0:
        raise AssertionError(f"reading clients.json exited {completed.returncode}:\n{completed.stderr}")
    table = json.loads(completed.stdout)
    return {row["name"]: list(row["files"]) for row in table["clients"]}


class TestTheCommittedFiles(unittest.TestCase):
    """What holds without SWCraft: each client's guard and server settings, as committed."""

    def test_the_guards_are_the_two_clients_own(self) -> None:
        copilot = json.loads((PROJECT_ROOT / ".github" / "hooks" / "swcraft.json").read_text(encoding="utf-8"))
        kiro = json.loads((PROJECT_ROOT / ".kiro" / "hooks" / "swcraft-guard.json").read_text(encoding="utf-8"))
        self.assertIn("swcraft guard", json.dumps(copilot))
        self.assertEqual("swcraft guard --host kiro", kiro["hooks"][0]["action"]["command"])
        server = json.loads((PROJECT_ROOT / ".kiro" / "settings" / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual("panel", server["mcpServers"]["swcraft"]["env"]["SWCRAFT_REVIEW"])


class TestClientFiles(unittest.TestCase):
    """The committed files against a fresh scaffold of the SWCraft on ``PATH``."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.toolchain = gate.toolchain_or_skip()
        cls.clients = installed_clients(cls.toolchain)
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.scaffold = Path(tmp.name) / "scaffold"
        command = [str(cls.toolchain.swcraft), "init", "--integration", "moon"]
        for client in CLIENTS:
            command += ["--client", client]
        completed = subprocess.run(
            [*command, str(cls.scaffold)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=gate.COMMAND_TIMEOUT,
        )
        if completed.returncode != 0:
            raise AssertionError(f"{command} exited {completed.returncode}:\n{completed.stderr}")

    def test_the_two_rows_name_the_files_this_test_expects(self) -> None:
        chosen = {relative for client in CLIENTS for relative in self.clients[client]}
        self.assertEqual(EXPECTED_FILES, chosen)

    def test_every_client_file_is_the_scaffold_copy(self) -> None:
        for relative in sorted(EXPECTED_FILES):
            with self.subTest(relative=relative):
                scaffolded = self.scaffold / relative
                committed = PROJECT_ROOT / relative
                self.assertTrue(scaffolded.is_file(), f"the scaffold wrote no {relative}")
                self.assertTrue(committed.is_file(), f"the project has no {relative}")
                self.assertEqual(scaffolded.read_bytes(), committed.read_bytes(), relative)

    def test_no_other_client_file_is_committed(self) -> None:
        """Codex and Claude Code are not set up: none of their files is in the project."""
        others = {
            relative
            for client, files in self.clients.items()
            if client not in CLIENTS
            for relative in files
        } - EXPECTED_FILES
        self.assertTrue(others, "the installation lists no other client")
        for relative in sorted(others):
            with self.subTest(relative=relative):
                self.assertFalse((PROJECT_ROOT / relative).exists(), relative)
        self.assertFalse((PROJECT_ROOT / ".codex").exists())


if __name__ == "__main__":
    unittest.main()
