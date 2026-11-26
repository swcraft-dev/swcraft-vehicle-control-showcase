"""The SWCraft installation on PATH, as the model gates find and trust it.

Not a test file: the model-coverage gate (and the rejected-change demonstrations)
import it. Stdlib only, so test discovery runs on any Python 3.11 -- the probe it
starts runs under the installation's own interpreter instead.

The lookup:

* ``swcraft`` is found with :func:`shutil.which` on PATH;
* the interpreter is the ``python``, ``python3`` or ``python.exe`` in the **same**
  directory, taken as spelled and **not** resolved through symlinks -- the
  installation is a virtual environment and that interpreter is the one whose
  ``site-packages`` holds the ``swcraft_tools`` that ``swcraft`` runs;
* ``swcraft --version`` must equal ``swcraft.yaml``'s ``toolchain_version``.

The policy: when any of the three fails the gate **skips**, naming the reason --
the CI runner has no SWCraft, and a runner serving several repositories may
carry another release. ``SHOWCASE_REQUIRE_SWCRAFT=1`` turns each skip into a
failure; the maintainer's runs and the evidence set it.

What this does not reach: the version check compares strings, and a
``swcraft`` that answers the pin but whose interpreter imports a different
``swcraft_tools`` is caught only by :func:`assert_tools_path_inside`, which the
gate calls with the probe's answer.

It also loads the repository's scripts for the tests (:func:`load_script`), the one way
they are loaded: ``scripts/`` goes on ``sys.path``, as running a script puts it there,
and each script is imported under its own name, once. The answer to ``swcraft --version``,
the refusal of another release and every command's timeout (:data:`COMMAND_TIMEOUT`) are
the generators' own (``scripts/pinned_swcraft.py``); and the generators' tests share a fake
``swcraft`` (:func:`fake_swcraft`) and a fixture (:class:`GeneratorCase`).
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_ROOT / "swcraft.yaml"
MODEL_ROOT = PROJECT_ROOT / "model"
PROBE = Path(__file__).resolve().parent / "model_coverage_probe.py"
REQUIRE_ENV = "SHOWCASE_REQUIRE_SWCRAFT"
INTERPRETER_NAMES = ("python", "python3", "python.exe")
SCRIPTS = PROJECT_ROOT / "scripts"


def load_script(name: str, directory: Path = SCRIPTS) -> ModuleType:
    """The script *name* (``<directory>/<name>.py``), imported under its own name with *directory* on ``sys.path``.

    A script imports its siblings by name, as it does when it runs; a script loaded twice is
    the same module, so a test patching it patches what the script itself uses.
    """
    if str(directory) not in sys.path:
        sys.path.append(str(directory))
    module = importlib.import_module(name)
    if Path(module.__file__ or "").resolve() != (directory / f"{name}.py").resolve():
        raise ImportError(f"{name} was imported from {module.__file__}, not from {directory.as_posix()}")
    return module


# The kit builder, and the generators' pin check (the manifest's parser, ``swcraft --version``).
KIT = load_script("build_colleague_kit")
PINNED = load_script("pinned_swcraft")
#: Seconds any one command a test starts may take: the generators' own limit.
COMMAND_TIMEOUT = PINNED.COMMAND_TIMEOUT


class ToolchainUnavailable(Exception):
    """No usable SWCraft installation; the message is the reason."""


@dataclass(frozen=True)
class Toolchain:
    swcraft: Path
    python: Path
    version: str


def pinned_version(manifest: Path = MANIFEST) -> str:
    """The one exact release ``swcraft.yaml`` pins: the generators' :func:`pinned_version`, on this repository's manifest."""
    return PINNED.pinned_version(manifest)


def require_requested(environ: Mapping[str, str] = os.environ) -> bool:
    return environ.get(REQUIRE_ENV, "") == "1"


def installed_version(swcraft: Path) -> str:
    """What ``swcraft --version`` answers, as the bare version string (the generators' probe)."""
    try:
        return PINNED.installed_version(str(swcraft))
    except PINNED.ToolchainError as error:
        raise ToolchainUnavailable(f"{error} ({swcraft.as_posix()})") from None


def locate(path_value: str | None) -> tuple[Path, Path]:
    """``swcraft`` on ``path_value`` (PATH when ``None``) and the interpreter beside it."""
    found = shutil.which("swcraft", path=path_value)
    if found is None:
        raise ToolchainUnavailable("swcraft is not on PATH")
    swcraft = Path(found)
    for name in INTERPRETER_NAMES:
        candidate = swcraft.parent / name  # deliberately not resolved
        if candidate.is_file():
            return swcraft, candidate
    raise ToolchainUnavailable(
        f"no Python interpreter ({', '.join(INTERPRETER_NAMES)}) beside {swcraft}: "
        "not a SWCraft installation this gate can probe"
    )


def toolchain_or_skip(
    path_value: str | None = None,
    *,
    pin: str | None = None,
    require: bool | None = None,
    version_of: Callable[[Path], str] = installed_version,
) -> Toolchain:
    """The pinned installation, or :class:`unittest.SkipTest` -- an ``AssertionError`` under require."""
    pin = pinned_version() if pin is None else pin
    require = require_requested() if require is None else require
    try:
        swcraft, python = locate(path_value)
        version = version_of(swcraft)
        if version != pin:
            raise ToolchainUnavailable(PINNED.pin_mismatch(version, pin))
        return Toolchain(swcraft=swcraft, python=python, version=version)
    except ToolchainUnavailable as unavailable:
        if require:
            raise AssertionError(f"{REQUIRE_ENV}=1 and {unavailable}") from None
        raise unittest.SkipTest(f"{unavailable} (set {REQUIRE_ENV}=1 to make this a failure)") from None


def assert_tools_path_inside(tools_path: str, python: Path) -> None:
    """``swcraft_tools`` must be imported from the interpreter's own environment.

    The environment is the directory above the interpreter's ``bin``/``Scripts``;
    both sides are resolved before the comparison, so a ``python3`` beside a
    symlinked ``swcraft`` that leads into another environment is caught.
    """
    environment = python.parent.parent.resolve()
    imported = Path(tools_path).resolve()
    if not imported.is_relative_to(environment):
        raise AssertionError(
            f"the probe imported swcraft_tools from {imported.as_posix()}, "
            f"outside the interpreter's environment {environment.as_posix()}"
        )


def _probe(toolchain: Toolchain, *args: str) -> dict[str, Any]:
    """The probe's JSON answer to *args*, run isolated under the installation's interpreter."""
    command = [str(toolchain.python), "-I", str(PROBE), *args]
    completed = PINNED.run_command(command, "the model coverage probe")
    if completed.returncode != 0:
        raise AssertionError(f"{command} exited {completed.returncode}:\n{completed.stderr}")
    return json.loads(completed.stdout)


def run_probe(toolchain: Toolchain, *extra: str, model_root: Path = MODEL_ROOT) -> dict[str, Any]:
    """The coverage report; the installed contract unless *extra* names a contract file."""
    return _probe(toolchain, str(model_root), *extra)


def dump_contract(toolchain: Toolchain) -> dict[str, Any]:
    """The installed contract as JSON."""
    return _probe(toolchain, "--dump-contract")


def rule_records(toolchain: Toolchain, model_root: Path = MODEL_ROOT) -> list[str]:
    """The sorted rule ids the cross-layer validator records for *model_root*."""
    return _probe(toolchain, "--rules", str(model_root))["records"]


def model_links(toolchain: Toolchain, model_root: Path = MODEL_ROOT) -> dict[str, Any]:
    """Every ``satisfies`` site of *model_root* and the records of the project's ``trace-decisions.yaml``."""
    return _probe(toolchain, "--links", str(model_root))


def check_model(toolchain: Toolchain, manifest: Path = MANIFEST, *extra: str) -> subprocess.CompletedProcess[str]:
    return PINNED.run_command(
        [str(toolchain.swcraft), "check-model", "--project", str(manifest), *extra], "swcraft check-model"
    )


def fake_swcraft(directory: Path, version: str) -> Path:
    """An executable ``swcraft`` in *directory* that answers ``swcraft <version>`` to ``--version``."""
    path = directory / "swcraft"
    path.write_text(
        f"#!{sys.executable}\nimport sys\nprint('swcraft {version}')\nsys.exit(0 if sys.argv[1:] == ['--version'] else 3)\n",
        encoding="utf-8",
        newline="\n",
    )
    path.chmod(0o755)
    return path


class GeneratorCase:
    """A generator's ``main`` run with its SWCraft steps replaced: the fixture both generators' tests share.

    Mixed into a :class:`unittest.TestCase` that sets :attr:`generator` (the loaded script),
    fills :attr:`output_dir` and :attr:`produced` in its ``setUp`` after this one's, and names
    the output folder's ``main`` keyword in :meth:`main_hooks`. Each test gets a temporary
    root (removed by ``addCleanup``) holding an empty ``bin/``, which is all ``PATH`` holds
    while ``main`` runs, and ``project/`` with a ``swcraft.yaml`` pinned to :attr:`PIN`.
    ``produce`` records each call and returns :attr:`produced`. The refusals before any work
    are tested here once for both generators.
    """

    PIN = "9.8.7"
    generator: ModuleType

    def setUp(self) -> None:
        super().setUp()  # type: ignore[misc]
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)  # type: ignore[attr-defined]
        self.root = Path(temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "swcraft.yaml").write_text(
            f'name: x\ntoolchain_version: "{self.PIN}"\n', encoding="utf-8", newline="\n"
        )
        self.output_dir = self.project / "outputs"
        self.produced: dict[str, bytes] = {}
        self.calls: list[tuple[Any, ...]] = []

    def main_hooks(self) -> dict[str, Path]:
        raise NotImplementedError

    def produce(self, swcraft: str, *rest: Any) -> dict[str, bytes]:
        self.calls.append((swcraft, *rest))
        return dict(self.produced)

    def run_main(self, *argv: str) -> tuple[int, str]:
        """``main`` with *argv*, only :attr:`bin` on ``PATH``: its exit code and its standard error."""
        stderr = io.StringIO()
        with (
            mock.patch.dict(os.environ, {"PATH": str(self.bin)}),
            contextlib.redirect_stderr(stderr),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            code = self.generator.main(list(argv), produce=self.produce, project_root=self.project, **self.main_hooks())
        return code, stderr.getvalue()

    def snapshot(self) -> dict[str, bytes]:
        """Every file under :attr:`output_dir`, by its relative path."""
        return {
            path.relative_to(self.output_dir).as_posix(): path.read_bytes()
            for path in self.output_dir.rglob("*")
            if path.is_file()
        }

    def test_no_swcraft_on_path_is_refused(self) -> None:
        code, stderr = self.run_main("--check")
        self.assertEqual(2, code)  # type: ignore[attr-defined]
        self.assertEqual("Error: swcraft is not on PATH\n", stderr)  # type: ignore[attr-defined]

    def test_a_swcraft_other_than_the_pin_is_refused_before_any_work(self) -> None:
        fake_swcraft(self.bin, "9.8.6")
        before = self.snapshot()
        code, stderr = self.run_main()
        self.assertEqual(2, code)  # type: ignore[attr-defined]
        self.assertIn(f"Error: {PINNED.pin_mismatch('9.8.6', self.PIN)}: ", stderr)  # type: ignore[attr-defined]
        self.assertEqual([], self.calls)  # type: ignore[attr-defined]
        self.assertEqual(before, self.snapshot())  # type: ignore[attr-defined]
