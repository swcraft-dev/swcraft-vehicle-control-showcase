"""The ``swcraft`` on ``PATH`` held to the release ``swcraft.yaml`` pins: what the generators share.

``scripts/generate_requirements_prepared.py`` and ``scripts/generate_test_annotations.py``
write files that are the pinned release's output. Both run through :func:`run_generator`,
which refuses, before any work, a missing ``swcraft`` or one whose ``--version`` is not the
pin (:func:`require_pinned_swcraft`), turns a failed step into one ``Error:`` line and exit 2,
reports ``--check``'s differences with exit 1 and prints what a write wrote. Every command
runs with a timeout (:func:`run_command`), and each generator copies the project it works on
with :func:`copy_project`. The pin is read by ``scripts/repository_rules.py``'s parser, the
one parser of ``toolchain_version`` the repository has (the kit builder and the publish
workflow ask it too). ``tests/swcraft_on_path.py`` asks :func:`installed_version` and
:func:`pin_mismatch` as well, so the answer to ``swcraft --version`` is read in one place.

A generator imports this module from its own directory, which Python puts first on
``sys.path`` when the script runs; the tests load the scripts the same way
(``tests/swcraft_on_path.py``'s ``load_script``). Maintainer tooling, not a kit member.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from repository_rules import ManifestError, parse_toolchain_version

#: Seconds any one command (a ``swcraft`` step, a Sphinx build, ``swcraft --version``) may take.
COMMAND_TIMEOUT = 600
#: What ``swcraft --version`` answers: ``swcraft`` and the bare version.
VERSION_ANSWER_RE = re.compile(r"^swcraft\s+(\S+)\s*$")


class ToolchainError(RuntimeError):
    """A step failed; the message is printed as it is. Each generator's own error derives from it."""


def run_command(command: list[str], what: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """*command* run with :data:`COMMAND_TIMEOUT`; a start failure or a timeout is a :class:`ToolchainError`."""
    try:
        return subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", check=False, timeout=COMMAND_TIMEOUT, **kwargs
        )
    except subprocess.TimeoutExpired:
        raise ToolchainError(f"{what} did not finish within {COMMAND_TIMEOUT} s") from None
    except OSError as error:
        raise ToolchainError(f"{what} could not be started: {error}") from None


def pinned_version(manifest: Path) -> str:
    """The one exact release the ``swcraft.yaml`` at *manifest* pins."""
    try:
        return parse_toolchain_version(manifest.read_text(encoding="utf-8"))
    except OSError as error:
        raise ToolchainError(f"swcraft.yaml could not be read: {error}") from None
    except ManifestError as error:
        raise ToolchainError(str(error)) from None


def installed_version(swcraft: str) -> str:
    """What *swcraft* ``--version`` answers, as the bare version string."""
    completed = run_command([swcraft, "--version"], "swcraft --version")
    answer = completed.stdout.strip()
    match = VERSION_ANSWER_RE.match(answer)
    if completed.returncode != 0 or match is None:
        raise ToolchainError(f"swcraft --version exited {completed.returncode} with {answer!r}, not 'swcraft <version>'")
    return match.group(1)


def pin_mismatch(version: str, pin: str) -> str:
    """The sentence that refuses a ``swcraft`` answering *version* where the manifest pins *pin*."""
    return f"swcraft on PATH is {version}, but swcraft.yaml pins toolchain_version {pin}"


def require_pinned_swcraft(swcraft: str, project_root: Path, outputs: str) -> None:
    """Refuse *swcraft* unless it answers the pin; *outputs* names the files that are the pinned release's output."""
    pin = pinned_version(project_root / "swcraft.yaml")
    version = installed_version(swcraft)
    if version != pin:
        raise ToolchainError(f"{pin_mismatch(version, pin)}: {outputs} are the pinned release's output")


def copy_project(project_root: Path, target: Path, names: Iterable[str], ignore: Callable[..., Any] | None = None) -> None:
    """Each of *names* (a file or a folder of *project_root*) copied into *target*; *ignore* as ``copytree``'s."""
    for name in names:
        source = project_root / name
        if source.is_dir():
            shutil.copytree(source, target / name, ignore=ignore)
        else:
            shutil.copy2(source, target / name)


def run_generator(
    *,
    project_root: Path,
    output_dir: Path,
    outputs: str,
    check: bool,
    produce: Callable[[str], dict[str, bytes]],
    differing: Callable[[dict[str, bytes]], list[str]],
    write: Callable[[dict[str, bytes]], None],
) -> int:
    """A generator's run: the pinned ``swcraft``, then *produce*, then ``--check`` or *write*.

    Exit 0 when the committed files are current (``--check``) or were written; 1 when
    ``--check`` finds a difference (named on one line); 2 with one ``Error:`` line when
    ``swcraft`` is missing or not the pin, or when any step fails (a :class:`ToolchainError`
    or a file that cannot be read or written). *outputs* names the files the pin governs.
    """
    swcraft = shutil.which("swcraft")
    if swcraft is None:
        print("Error: swcraft is not on PATH", file=sys.stderr)
        return 2
    try:
        require_pinned_swcraft(swcraft, project_root, outputs)
        produced = produce(swcraft)
        if check:
            names = differing(produced)
            if names:
                print(f"differs from the generator's output: {', '.join(names)}", file=sys.stderr)
                return 1
            return 0
        write(produced)
    except (ToolchainError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    shown = output_dir.relative_to(project_root) if output_dir.is_relative_to(project_root) else output_dir
    print(f"wrote {len(produced)} files under {shown.as_posix()}/")
    return 0
