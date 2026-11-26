"""Build the colleague kit: one zip of this showcase, pinned to one SWCraft release.

The kit is what a colleague unpacks next to an installed SWCraft toolchain (the
workstation archive, ``swcraft-<version>-windows-x64.zip``): the project manifest
with ``toolchain_version`` set, the model, the editor settings, the repository's
``.gitattributes`` (so a kit turned into a repository checks out LF on Windows too,
whatever ``core.autocrlf`` says), the Copilot agent profile and model-guard hook, Kiro's three
files (its MCP server settings, its steering file and its model-guard hook), the kit's own
Copilot instructions,
the trace link search's configuration (``experiments/trace.yaml``), the three legal files
(``LICENSE``, ``NOTICE`` and ``THIRD-PARTY-NOTICES.md``: the kit ships the third-party code the
notices name -- Sphinx with its theme alabaster, its extensions sphinx-needs and sphinx-data-viewer,
the Snowball stemmers, Pygments' style and jQuery in the sites, Marp in the presentation), the
demonstrations (``demos/README.md``,
which holds the diagrams and the rejected changes, with ``demos/rejected-changes.json``; the chat
with the model, ``demos/chat-with-the-model.md``; and the requirements exchange: its walkthrough
``demos/requirements-exchange.md`` and its files under ``demos/requirements-exchange/``:
the requirements team's Sphinx project, its two deliveries, the architect's mapping,
the answer key, the prepared links and the team's four ready-made sites, and the public
copy of its presentation, ``demos/requirements-exchange-presentation-public.html``; and the
test tables: their walkthrough ``demos/test-tables.md`` and the test team's annotations
folder ``demos/test-tables/annotations/``, by a
second allowlist and a list of site folders: the
rules and the exchange are shown to a colleague the way they are shown on stage, while
the tests that run them stay out) and the install page, ``docs/guide/install-on-a-workstation.md``,
as ``README.md``.
It carries nothing that needs git, moon, Node or a network -- the two allowlists below
plus the overlay is the whole of it, and the tests assert what stays out (the
moon build graph and its launchers, the generated outputs, the evidence, the
licensed schema).

The agent profile, the Copilot hook and Kiro's files are the repository's own ``.github/`` and ``.kiro/``
files, verbatim: the repository and the kit are at the same SWCraft release, so there is one copy.
Codex's hook (``.codex/hooks.json``) is not carried: the showcase is set up for Copilot and Kiro.
The overlay (``kit/overlay/``) holds only what differs for the kit -- the Copilot
instructions whose *Building* section names ``swcraft validate`` because the kit
ships no ``moon.yml``, and a ``.gitignore`` that also hides the licensed schema.

Stdlib only, no shell: every path is built with ``pathlib`` and the zip is
written by ``zipfile`` with a fixed timestamp and a sorted member order, so two
builds from the same inputs are byte-identical and one SHA-256 identifies a kit.

Usage::

    python scripts/build_colleague_kit.py                 # dist/colleague-kit/
    python scripts/build_colleague_kit.py --swcraft-version 0.7.1 --output-dir DIR
    python scripts/build_colleague_kit.py --tagged        # drop the tag-pending note

``--swcraft-version`` defaults to :data:`DEFAULT_VERSION`; the note that its tag
is pending is written into ``kit-manifest.json`` until ``--tagged`` says otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

# The pin's parser and the two name lists live in a leaf the generators share; the verify
# workflow imports ``parse_toolchain_version`` from this module, so it is re-exported here.
from repository_rules import IGNORED_NAMES, SITE_REFUSED_NAMES, VERSION_RE, ManifestError, parse_toolchain_version

__all__ = ["IGNORED_NAMES", "SITE_REFUSED_NAMES", "ManifestError", "parse_toolchain_version"]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KIT_NAME = "vehicle-control-showcase"
DEFAULT_VERSION = "0.24.0"
OVERLAY_DIR = PROJECT_ROOT / "kit" / "overlay"
#: The install page, relative to a project root: the one path both the default and ``main``'s
#: ``--project-root`` read, so it is written once.
INSTALL_PAGE_PATH = "docs/guide/install-on-a-workstation.md"
INSTALL_PAGE = PROJECT_ROOT / INSTALL_PAGE_PATH
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "dist" / "colleague-kit"
MANIFEST_NAME = "kit-manifest.json"
README_NAME = "README.md"
SUMS_NAME = "SHA256SUMS"
#: One fixed timestamp for every member: the zip is identified by its digest, and
#: a build time inside it would make two identical kits differ.
ZIP_DATE_TIME = (2026, 1, 1, 0, 0, 0)
FILE_MODE = 0o644

#: The legal files: the showcase's licence and notice, and the licences of the vendored code its
#: sites and presentation carry. The kit ships them verbatim with :data:`PROJECT_FILES`.
LEGAL_FILES = ("LICENSE", "NOTICE", "THIRD-PARTY-NOTICES.md")
#: The project files the kit carries, by allowlist. Anything not named here stays
#: out; ``tests/test_build_colleague_kit.py`` asserts the absentees by name.
PROJECT_FILES = (
    "swcraft.yaml",
    ".vscode/settings.json",
    ".gitattributes",
    ".github/agents/swcraft-architect.agent.md",
    ".github/hooks/swcraft.json",
    ".kiro/settings/mcp.json",
    ".kiro/steering/swcraft.md",
    ".kiro/hooks/swcraft-guard.json",
    "experiments/trace.yaml",
    *LEGAL_FILES,
)
#: The demonstrations, by a second allowlist: the demos page (the diagrams and the rejected
#: changes) with the data a presenter applies by hand, the chat scenario
#: ``demos/chat-with-the-model.md``, and the requirements exchange: its walkthrough
#: ``demos/requirements-exchange.md``, the public HTML of its presentation and its twelve files --
#: the architect's mapping, the answer key, the prepared links, the team's two
#: deliveries, the team's Sphinx project (its ``conf.py``, its ``requirements.txt`` and
#: both sources) and the three needs files the ready-made sites were built from; and the
#: test tables: ``demos/test-tables.md`` and the test team's three annotated tables, which
#: ``.vscode/settings.json`` names as the annotations folder. Nothing
#: else under ``demos/`` ships beyond :data:`DEMO_TREES`: not the team's copy of the
#: architecture (``team/swcraft/``, written in step 4), not the tests that run the demos,
#: not the scripts that generate the team's sources, the prepared files and the test team's
#: annotations (``scripts/generate_requirements_deliveries.py``,
#: ``scripts/generate_requirements_prepared.py``, ``scripts/generate_test_annotations.py``
#: and their shared ``scripts/pinned_swcraft.py`` and ``scripts/repository_rules.py``),
#: and not the presentation's source, its presenter copy with the speaker notes, its public
#: Markdown or ``demos/build_public.py``, which renders them.
DEMO_FILES = (
    "demos/README.md",
    "demos/chat-with-the-model.md",
    "demos/rejected-changes.json",
    "demos/requirements-exchange.md",
    "demos/requirements-exchange-presentation-public.html",
    "demos/requirements-exchange/team.needs-mapping.yaml",
    "demos/requirements-exchange/answer-key.json",
    "demos/requirements-exchange/prepared-links.json",
    "demos/requirements-exchange/deliveries/1.0/needs.json",
    "demos/requirements-exchange/deliveries/1.1/needs.json",
    "demos/requirements-exchange/team/conf.py",
    "demos/requirements-exchange/team/requirements.txt",
    "demos/requirements-exchange/team/delivery-1.0/index.rst",
    "demos/requirements-exchange/team/delivery-1.1/index.rst",
    "demos/requirements-exchange/sites/1.0.needs.json",
    "demos/requirements-exchange/sites/1.1-unconfirmed.needs.json",
    "demos/requirements-exchange/sites/1.1-confirmed.needs.json",
    "demos/test-tables.md",
    "demos/test-tables/annotations/components.csv",
    "demos/test-tables/annotations/component-placement.csv",
    "demos/test-tables/annotations/runnable-scheduling.csv",
)
#: The requirements team's ready-made sites, which steps 4 and 5 open, and delivery 1.0's site
#: as the team built it before any handover (``1.0-original``): every file under each
#: folder ships (Sphinx's pages, scripts, style sheets and images). A folder that is
#: missing or empty is refused by name, and so is a file no reader opens: a dotfile or a
#: dot folder (Sphinx's ``.buildinfo``, a ``.doctrees``) or Sphinx-Needs' build report
#: (:data:`SITE_REFUSED_NAMES`) -- a site folder holds what the generator wrote, and such a
#: file is a working-tree leftover the kit must not carry.
DEMO_TREES = (
    "demos/requirements-exchange/sites/1.0-original",
    "demos/requirements-exchange/sites/1.0",
    "demos/requirements-exchange/sites/1.1-unconfirmed",
    "demos/requirements-exchange/sites/1.1-confirmed",
)
MODEL_DIR = "model"
MODEL_SUFFIXES = (".yaml",)
MODEL_KEEP_NAMES = (".gitkeep",)
# IGNORED_NAMES (operating-system litter never shipped from a site folder) and
# SITE_REFUSED_NAMES (Sphinx's bookkeeping a site folder must not hold) are
# ``scripts/repository_rules.py``'s, the one list of each.

TAG_PENDING_NOTE = (
    "SWCraft {version} is the release this kit is pinned to. When the kit was built "
    "the {version} tag was still pending; the workstation archive "
    "swcraft-{version}-windows-x64.zip is what carries the release. Against any "
    "other version, the commands that write, check or start the assistant refuse by name, and "
    "the six read-only ones warn and answer anyway."
)
TAGGED_NOTE = (
    "SWCraft {version} is the release this kit is pinned to; install the workstation "
    "archive swcraft-{version}-windows-x64.zip beside it."
)

MANIFEST_HEADER = """\
# Project manifest of the Vehicle Control Showcase, packaged as the colleague kit
# by scripts/build_colleague_kit.py in the showcase repository.
#
# `toolchain_version` is the SWCraft release this kit is built for. Every
# `swcraft` command compares it with the installed toolchain before it does
# anything else. On a mismatch the commands that write, check or start the
# assistant refuse in one sentence naming both versions, and the six read-only
# ones (diff, impact, list, metrics, query, resource-report) print that sentence
# and answer anyway. The remedy is to install that release's workstation
# archive, not to edit the pin. The kit carries no build graph and installs
# nothing.
"""


class KitError(RuntimeError):
    """A kit precondition failed with a message the caller prints as it is."""


def require_version(version: str) -> str:
    """Return *version* when it is one exact release (``X.Y.Z``), else refuse."""
    if not VERSION_RE.match(version):
        raise KitError(
            f"--swcraft-version must be one exact release such as 0.7.0, not {version!r}: "
            "the project pins a version, never a range"
        )
    return version


def pin_manifest(text: str, version: str) -> str:
    """Return the manifest text with the kit header and ``toolchain_version`` set.

    The leading comment block of the repository's manifest describes its build
    graph and is replaced by :data:`MANIFEST_HEADER`; the keys are kept verbatim.
    An existing ``toolchain_version`` line is replaced, otherwise the pin is
    inserted right after ``schema_version``, which the manifest must declare.
    """
    lines = text.splitlines()
    while lines and (lines[0].startswith("#") or not lines[0].strip()):
        lines.pop(0)
    pin = f'toolchain_version: "{version}"'
    body: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("toolchain_version:"):
            body.append(pin)
            replaced = True
        else:
            body.append(line)
    if not replaced:
        anchors = [index for index, line in enumerate(body) if line.startswith("schema_version:")]
        if len(anchors) != 1:
            raise KitError("swcraft.yaml must declare schema_version exactly once")
        body.insert(anchors[0] + 1, pin)
    return MANIFEST_HEADER + "\n".join(body) + "\n"


def _read(path: Path) -> bytes:
    return path.read_bytes()


def collect_project_files(project_root: Path) -> dict[str, bytes]:
    """The project's own members: the two allowlists, the site folders and the model tree."""
    members: dict[str, bytes] = {}
    for relative in PROJECT_FILES + DEMO_FILES:
        path = project_root / relative
        if not path.is_file():
            raise KitError(f"{relative} is missing from {project_root.as_posix()}")
        members[relative] = _read(path)
    for relative in DEMO_TREES:
        tree = project_root / relative
        files = sorted((path for path in tree.rglob("*") if path.is_file()), key=lambda item: item.as_posix())
        files = [path for path in files if path.name not in IGNORED_NAMES]
        if not files:
            raise KitError(f"{relative}/ is missing or empty in {project_root.as_posix()}")
        refused = [
            path.relative_to(project_root).as_posix()
            for path in files
            if path.name in SITE_REFUSED_NAMES
            or any(part.startswith(".") for part in path.relative_to(tree).parts)
        ]
        if refused:
            raise KitError(
                f"{relative}/ holds files that are no part of a site: {', '.join(refused)}; "
                "remove them or regenerate the site"
            )
        for path in files:
            members[path.relative_to(project_root).as_posix()] = _read(path)
    model_root = project_root / MODEL_DIR
    if not model_root.is_dir():
        raise KitError(f"{MODEL_DIR}/ is missing from {project_root.as_posix()}")
    model_files = 0
    for path in sorted(model_root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        if path.suffix in MODEL_SUFFIXES:
            model_files += 1
        elif path.name not in MODEL_KEEP_NAMES:
            continue
        members[path.relative_to(project_root).as_posix()] = _read(path)
    if model_files == 0:
        raise KitError(f"{MODEL_DIR}/ holds no element file")
    return members


def collect_overlay(overlay_dir: Path) -> dict[str, bytes]:
    """Every file under the overlay, keyed by its path relative to the overlay."""
    if not overlay_dir.is_dir():
        raise KitError(f"the overlay directory {overlay_dir.as_posix()} is missing")
    members: dict[str, bytes] = {}
    for path in sorted(overlay_dir.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file():
            members[path.relative_to(overlay_dir).as_posix()] = _read(path)
    if not members:
        raise KitError(f"the overlay directory {overlay_dir.as_posix()} is empty")
    return members


def model_digest(members: dict[str, bytes]) -> str:
    """SHA-256 over the model members, name then content, in sorted order."""
    digest = hashlib.sha256()
    for name in sorted(members):
        if name.startswith(MODEL_DIR + "/"):
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(members[name])
            digest.update(b"\0")
    return digest.hexdigest()


def build_members(
    project_root: Path,
    overlay_dir: Path,
    install_page: Path,
    version: str,
    *,
    tagged: bool = False,
) -> dict[str, bytes]:
    """The kit's members, keyed by their path inside the ``<KIT_NAME>/`` folder."""
    version = require_version(version)
    if not install_page.is_file():
        raise KitError(f"the install page {install_page.as_posix()} is missing")
    members = collect_project_files(project_root)
    overlay = collect_overlay(overlay_dir)
    clash = sorted(set(overlay) & set(members))
    if clash:
        raise KitError(f"the overlay would replace a project file the kit already carries: {clash}")
    members.update(overlay)
    members["swcraft.yaml"] = pin_manifest(members["swcraft.yaml"].decode("utf-8"), version).encode(
        "utf-8"
    )
    members[README_NAME] = _read(install_page)
    note = (TAGGED_NOTE if tagged else TAG_PENDING_NOTE).format(version=version)
    manifest = {
        "kit": KIT_NAME,
        "swcraft_version": version,
        "swcraft_archive": f"swcraft-{version}-windows-x64.zip",
        "note": note,
        "model_sha256": model_digest(members),
        "members": sorted(members) + [MANIFEST_NAME],
    }
    members[MANIFEST_NAME] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return members


def zip_bytes(members: dict[str, bytes]) -> bytes:
    """The kit zip as bytes: sorted members under ``<KIT_NAME>/``, one timestamp."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(f"{KIT_NAME}/{name}", date_time=ZIP_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = FILE_MODE << 16
            archive.writestr(info, members[name])
    return buffer.getvalue()


def kit_filename(version: str) -> str:
    return f"{KIT_NAME}-kit-{version}.zip"


def write_kit(output_dir: Path, version: str, payload: bytes) -> tuple[Path, str]:
    """Write the zip and a ``SHA256SUMS`` beside it; return the path and digest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    name = kit_filename(version)
    target = output_dir / name
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    (output_dir / SUMS_NAME).write_text(f"{digest}  {name}\n", encoding="utf-8", newline="\n")
    return target, digest


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--swcraft-version",
        default=DEFAULT_VERSION,
        help=f"the exact SWCraft release the kit pins (default {DEFAULT_VERSION})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="where the zip and SHA256SUMS go (default dist/colleague-kit/, git-ignored)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="the showcase checkout to package (default: the one this script lives in)",
    )
    parser.add_argument(
        "--tagged",
        action="store_true",
        help="the release is tagged: write the plain note instead of the tag-pending one",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    try:
        members = build_members(
            project_root,
            project_root / "kit" / "overlay",
            project_root / INSTALL_PAGE_PATH,
            args.swcraft_version,
            tagged=args.tagged,
        )
        target, digest = write_kit(args.output_dir.resolve(), args.swcraft_version, zip_bytes(members))
    except (KitError, ManifestError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"{target.as_posix()}")
    print(f"sha256 {digest}")
    print(f"{len(members)} members, pinned to SWCraft {args.swcraft_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
