"""Write the requirements exchange's prepared files: the prepared links and the team's sites.

The showcase's requirements exchange (``demos/requirements-exchange.md``) links delivery
1.0 in two parts on stage: two links and one rejection by hand, then the rest of the
answer key in one Apply of a prepared proposals file. Its step 4 shows the requirements
team's Sphinx site, which the kit carries ready-made. This script writes both, from the
installed SWCraft (``swcraft`` on ``PATH``) and the committed project, on a temporary
copy:

* ``demos/requirements-exchange/prepared-links.json`` -- after importing delivery 1.0, a
  Review search of every requirement (``--labelling '[]'``) with each answer-key target
  accepted (its row, or a ``chosen`` entry where the search lists none) and every row of
  the eight distractors rejected; nothing else decided;
* ``demos/requirements-exchange/sites/<state>.needs.json`` -- the architecture's
  ``dist/needs.json`` at the page's three states, reached by the page's own steps: the hand
  links of step 2 (:data:`HAND_LINKS`, :data:`HAND_REJECT`), the prepared links applied
  from a copy in ``dist/``, the build (``1.0``); delivery 1.1 imported (``1.1-unconfirmed``);
  the link to ``SWR-THP-003`` confirmed (``1.1-confirmed``);
* with ``--sphinx-build``, ``demos/requirements-exchange/sites/<state>/`` -- the team's
  site built from that state's needs file with the team's ``conf.py`` unchanged
  (``-W``, ``SOURCE_DATE_EPOCH`` fixed, the doctrees outside the site) -- and
  ``sites/1.0-original/`` (:data:`ORIGINAL`), delivery 1.0's site as the team built it, with
  no needs file handed over and so none beside it: the "before" of the three states. Sphinx's
  bookkeeping files that a reader does not open (``scripts/repository_rules.py``'s
  ``SITE_REFUSED_NAMES``, which the kit refuses in a site folder) are left out.
  Sphinx-Needs 9.2.0 gives each need's container a random id (``SNCB-`` and eight hex
  digits, ``uuid.uuid4()`` in its ``layout.py``, unconditionally: no configuration value
  reaches it), so two builds of one site differ in those ids and nowhere else: the
  committed pages are Sphinx's output as written, and ``--check`` compares them with those
  ids masked (:data:`RANDOM_ID_RE`).

A site is built from its needs file, so the two change together: without
``--sphinx-build`` the script **refuses** to write when a needs file would change, naming
it, and writes nothing (:func:`refuse_unbuilt_sites`); with it, each site folder is
written beside the old one first and then put in its place. Operating-system litter in a site
folder (``scripts/repository_rules.py``'s ``IGNORED_NAMES``) is no part of a site and never counts as a
difference.

Before anything runs, the ``swcraft`` on ``PATH`` must answer the release
``swcraft.yaml`` pins (``toolchain_version``), and the ``--sphinx-build`` given must be
an executable: the outputs depend on the toolchain, and a wrong one would be found only
after minutes of work, or not at all (``scripts/pinned_swcraft.py``, which the test
annotations' generator shares). Every command runs with a timeout (``COMMAND_TIMEOUT``);
a failure of any step, a file that cannot be read or written among them, is one
``Error:`` line and exit 2.

``--check`` writes nothing and exits 1 when a committed file differs, byte for byte, from
what this script would write (the sites only with ``--sphinx-build``). It needs SWCraft,
and Sphinx for the sites: maintainer tooling, run on the maintainer's machine, not a kit
member. The walk test (``tests/test_requirements_exchange.py``) holds the committed needs
files to the page's steps and the committed links file to the answer key, and runs
``--check`` without Sphinx; ``tests/test_requirements_sites.py`` holds each committed site
to its needs file without Sphinx, by need id.

Usage::

    python scripts/generate_requirements_prepared.py            # the links and the needs files
    python scripts/generate_requirements_prepared.py --check
    python scripts/generate_requirements_prepared.py --sphinx-build <venv>/bin/sphinx-build [--check]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pinned_swcraft import ToolchainError, copy_project, run_command, run_generator
from repository_rules import IGNORED_NAMES, SITE_REFUSED_NAMES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
#: The scenario's folder, relative to a project root: every path of the exchange is derived from it.
EXCHANGE = Path("demos") / "requirements-exchange"
EXCHANGE_DIR = PROJECT_ROOT / EXCHANGE
PREPARED_NAME = "prepared-links.json"
SITES_NAME = "sites"
#: What a temporary copy of the project holds: the project as a colleague has it.
COPIED = ("swcraft.yaml", "model", "experiments", "demos")
MAPPING = (EXCHANGE / "team.needs-mapping.yaml").as_posix()
#: Step 2 by hand, in the Labelling of everything: the requirements linked to their key
#: targets, and the one requirement whose first row (in the panel's order) is rejected.
HAND_LINKS = ("SWR-THP-003", "SWR-BRK-008")
HAND_REJECT = "SWR-BRK-011"
CHANGED = "SWR-THP-003"
#: The three states: name -> the delivery its site shows.
STATES = {"1.0": "1.0", "1.1-unconfirmed": "1.1", "1.1-confirmed": "1.1"}
#: The site of delivery 1.0 before any handover: built without ``team/swcraft/needs.json``, which
#: the team's ``conf.py`` then leaves out, so it shows the requirements and no architecture link.
ORIGINAL = "1.0-original"
ORIGINAL_DELIVERY = "1.0"
#: Every site folder this script writes: the three states' and the original.
SITES = (*STATES, ORIGINAL)
BANDS = ("strong", "medium", "weak")
#: One fixed build date for the sites (2026-01-01T00:00:00Z), as the kit's zip has one.
SOURCE_DATE_EPOCH = "1767225600"
#: The one part of a site page that differs between two builds of the same input.
RANDOM_ID_RE = re.compile(rb"SNCB-[0-9a-f]{8}")


class PrepareError(ToolchainError):
    """A step of this generator failed; the message is printed as it is."""


def read_json(path: Path, what: str) -> Any:
    """The JSON document at *path*; a missing or malformed file is a :class:`PrepareError` naming *what*."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PrepareError(f"{what} could not be read: {error}") from None


def require_sphinx_build(sphinx_build: str) -> str:
    """The executable *sphinx-build* names, or a :class:`PrepareError` before any work starts."""
    found = shutil.which(sphinx_build)
    if found is None:
        raise PrepareError(f"--sphinx-build {sphinx_build} is not an executable")
    return found


def answer_key(project_root: Path = PROJECT_ROOT) -> dict[str, list[dict[str, Any]]]:
    """Requirement id -> the elements the answer key links it to (empty: a distractor)."""
    document = read_json(project_root / EXCHANGE / "answer-key.json", "the answer key")
    try:
        return {need_id: entry["targets"] for need_id, entry in document["requirements"].items()}
    except (KeyError, TypeError, AttributeError) as error:
        raise PrepareError(f"the answer key is not shaped as expected: {error!r}") from None


def rows_by_strength(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The panel's row order (``traceCore.ts`` ``rowsByStrength``): band, then score, then place."""
    indexed = list(enumerate(rows))
    indexed.sort(
        key=lambda pair: (BANDS.index(pair[1]["band"]), -pair[1]["score"]["n"], pair[1]["place"], pair[0])
    )
    return [row for _, row in indexed]


def accept_key(entry: dict[str, Any], targets: list[dict[str, Any]]) -> None:
    """Accept each target not yet linked: its row when it is one, a ``chosen`` entry otherwise."""
    linked = [link["target"] for link in entry["linked"]]
    for target in targets:
        if target in linked:
            continue
        rows = [row for row in entry["candidates"] if row["target"] == target]
        if rows:
            rows[0]["decision"] = "accept"
        elif {"target": target} not in entry["chosen"]:
            entry["chosen"].append({"target": target})


def decide_prepared(proposals: dict[str, Any], key: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """The whole key accepted, every distractor's rows rejected, nothing else decided."""
    for entry in proposals["requirements"]:
        if entry["id"] not in key:
            continue
        if key[entry["id"]]:
            accept_key(entry, key[entry["id"]])
        else:
            for row in entry["candidates"]:
                row["decision"] = "reject"
    return proposals


def decide_by_hand(proposals: dict[str, Any], key: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Step 2's hand part: the key on :data:`HAND_LINKS`, one ✕ on :data:`HAND_REJECT`'s first row."""
    entries = {entry["id"]: entry for entry in proposals["requirements"]}
    for need_id in (*HAND_LINKS, HAND_REJECT):
        if need_id not in entries:
            raise PrepareError(f"the search after delivery 1.0 lists no {need_id}, which step 2 decides by hand")
    for need_id in HAND_LINKS:
        if not key.get(need_id):
            raise PrepareError(f"the answer key links {need_id}, which step 2 links by hand, to nothing")
        accept_key(entries[need_id], key[need_id])
    rows = rows_by_strength(entries[HAND_REJECT]["candidates"])
    if not rows:
        raise PrepareError(f"the search lists no candidate for {HAND_REJECT}, whose first row step 2 rejects")
    rows[0]["decision"] = "reject"
    return proposals


def dumps(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2) + "\n"


class Stage:
    """A temporary copy of the project and the commands the page runs on it."""

    def __init__(self, root: Path, swcraft: str, project_root: Path) -> None:
        self.root = root
        self.swcraft_path = swcraft
        copy_project(project_root, root, COPIED, ignore=shutil.ignore_patterns("swcraft", SITES_NAME))
        self.proposals_path = root / "dist" / "experiments" / "trace" / "proposals.json"

    def swcraft(self, *args: str) -> str:
        completed = run_command(
            [self.swcraft_path, *args, "--project", "swcraft.yaml"], f"swcraft {' '.join(args)}", cwd=self.root
        )
        output = completed.stdout + completed.stderr
        if completed.returncode != 0:
            raise PrepareError(f"swcraft {' '.join(args)} exited {completed.returncode}:\n{output}")
        return output

    def import_delivery(self, version: str) -> str:
        source = (EXCHANGE / "deliveries" / version / "needs.json").as_posix()
        return self.swcraft("import", "requirements", "--source", source, "--mapping", MAPPING)

    def search(self, labelling: str) -> dict[str, Any]:
        self.swcraft("experiment", "trace", "--config", "experiments/trace.yaml", "--labelling", labelling)
        return read_json(self.proposals_path, "the trace search's proposals")

    def save(self, proposals: dict[str, Any]) -> Path:
        """*proposals* written to the search's own file, as the panel saves its decisions."""
        self.proposals_path.write_text(dumps(proposals), encoding="utf-8", newline="\n")
        return self.proposals_path

    def apply(self, path: Path) -> str:
        """Apply the proposals file at *path*."""
        return self.swcraft("experiment", "trace", "--apply", str(path))

    def generate_needs(self) -> bytes:
        self.swcraft("generate", "needs")
        try:
            return (self.root / "dist" / "needs.json").read_bytes()
        except OSError as error:
            raise PrepareError(f"generate needs wrote no dist/needs.json: {error}") from None


def prepared_links(swcraft: str, key: dict[str, list[dict[str, Any]]], project_root: Path) -> str:
    """The prepared proposals file's text: a Review search after delivery 1.0, decided by the key."""
    with tempfile.TemporaryDirectory() as tmp:
        stage = Stage(Path(tmp), swcraft, project_root)
        stage.import_delivery("1.0")
        return dumps(decide_prepared(stage.search("[]"), key))


def handover_needs(
    swcraft: str, key: dict[str, list[dict[str, Any]]], prepared: str, project_root: Path
) -> dict[str, bytes]:
    """State name -> the ``dist/needs.json`` the page's steps produce at it."""
    states = {}
    with tempfile.TemporaryDirectory() as tmp:
        stage = Stage(Path(tmp), swcraft, project_root)
        stage.import_delivery("1.0")
        stage.apply(stage.save(decide_by_hand(stage.search('"all"'), key)))
        copy = stage.root / "dist" / PREPARED_NAME
        copy.write_text(prepared, encoding="utf-8", newline="\n")
        stage.apply(copy)
        states["1.0"] = stage.generate_needs()
        stage.import_delivery("1.1")
        states["1.1-unconfirmed"] = stage.generate_needs()
        proposals = stage.search("[]")
        entry = next((entry for entry in proposals["requirements"] if entry["id"] == CHANGED), None)
        if entry is None:
            raise PrepareError(f"the Review search after delivery 1.1 lists no {CHANGED}")
        pending = [link for link in entry["linked"] if not link["confirmed"]]
        if len(pending) != 1:
            raise PrepareError(f"{CHANGED} has {len(pending)} links awaiting confirmation, not 1")
        pending[0]["decision"] = "confirm"
        stage.apply(stage.save(proposals))
        states["1.1-confirmed"] = stage.generate_needs()
    return states


def build_site(sphinx_build: str, version: str, needs: bytes | None, project_root: Path) -> dict[str, bytes]:
    """The team's site of *version* with *needs* handed over (``None``: nothing handed over): relative path -> bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        team = Path(tmp) / "team"
        shutil.copytree(project_root / EXCHANGE / "team", team, ignore=shutil.ignore_patterns("swcraft", "__pycache__"))
        if needs is not None:
            (team / "swcraft").mkdir()
            (team / "swcraft" / "needs.json").write_bytes(needs)
        out = Path(tmp) / "html"
        environment = {**os.environ, "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH, "PYTHONHASHSEED": "0"}
        completed = run_command(
            [sphinx_build, "-W", "-q", "-c", str(team), "-D", f"version={version}", "-b", "html",
             "-d", str(Path(tmp) / "doctrees"), str(team / f"delivery-{version}"), str(out)],
            f"sphinx-build of delivery {version}", env=environment,
        )
        if completed.returncode != 0 or completed.stderr.strip():
            raise PrepareError(f"sphinx-build of delivery {version} failed:\n{completed.stdout}{completed.stderr}")
        files = {}
        for path in sorted(out.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_file() and path.name not in SITE_REFUSED_NAMES:
                files[path.relative_to(out).as_posix()] = path.read_bytes()
        return files


def outputs(swcraft: str, sphinx_build: str | None, project_root: Path = PROJECT_ROOT) -> dict[str, bytes]:
    """Each output's path, relative to the scenario's folder, and its bytes: *project_root*'s exchange."""
    key = answer_key(project_root)
    prepared = prepared_links(swcraft, key, project_root)
    files = {PREPARED_NAME: prepared.encode("utf-8")}
    for state, needs in handover_needs(swcraft, key, prepared, project_root).items():
        files[f"{SITES_NAME}/{state}.needs.json"] = needs
        if sphinx_build:
            for relative, data in build_site(sphinx_build, STATES[state], needs, project_root).items():
                files[f"{SITES_NAME}/{state}/{relative}"] = data
    if sphinx_build:
        for relative, data in build_site(sphinx_build, ORIGINAL_DELIVERY, None, project_root).items():
            files[f"{SITES_NAME}/{ORIGINAL}/{relative}"] = data
    return files


def committed(exchange_dir: Path, with_sites: bool) -> dict[str, bytes]:
    """The committed outputs this script owns: the links, the needs files and, *with_sites*, the sites."""
    files = {}
    if (exchange_dir / PREPARED_NAME).is_file():
        files[PREPARED_NAME] = (exchange_dir / PREPARED_NAME).read_bytes()
    for state in STATES:
        needs = exchange_dir / SITES_NAME / f"{state}.needs.json"
        if needs.is_file():
            files[needs.relative_to(exchange_dir).as_posix()] = needs.read_bytes()
    for state in SITES:
        site = exchange_dir / SITES_NAME / state
        if with_sites and site.is_dir():
            for path in site.rglob("*"):
                if path.is_file() and path.name not in IGNORED_NAMES:
                    files[path.relative_to(exchange_dir).as_posix()] = path.read_bytes()
    return files


def comparable(name: str, data: bytes | None) -> bytes | None:
    """*data* as ``--check`` compares it: a site page with its random container ids masked."""
    if data is not None and name.startswith(f"{SITES_NAME}/") and name.endswith(".html"):
        return RANDOM_ID_RE.sub(b"SNCB-********", data)
    return data


def refuse_unbuilt_sites(produced: dict[str, bytes], present: dict[str, bytes]) -> None:
    """A needs file may change only with its site rebuilt: without the sites, refuse any change (a new one counts)."""
    changed = sorted(
        name
        for name in produced
        if name.startswith(f"{SITES_NAME}/") and name.endswith(".needs.json") and produced[name] != present.get(name)
    )
    if changed:
        raise PrepareError(
            f"{', '.join(changed)} would change, and the site built from each would be left stale: "
            "run again with --sphinx-build <venv>/bin/sphinx-build to rebuild the sites with them; nothing was written"
        )


def differing(produced: dict[str, bytes], present: dict[str, bytes]) -> list[str]:
    """The outputs ``--check`` reports: produced or committed, and not equal as compared."""
    return sorted(
        name
        for name in set(produced) | set(present)
        if comparable(name, produced.get(name)) != comparable(name, present.get(name))
    )


def write_files(files: dict[str, bytes], root: Path) -> None:
    """Each of *files* written under *root* at its relative path."""
    for relative, data in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def remove(path: Path) -> None:
    """*path* removed, a folder with everything in it."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def write_outputs(produced: dict[str, bytes], exchange_dir: Path, with_sites: bool) -> None:
    """Write *produced* under *exchange_dir* as one set: every output replaced, or none.

    Every output is first written into a staging folder beside them. Only then is each
    output this run owns -- the links, the needs files and, *with_sites*, each site folder
    whole -- moved aside into the staging folder and its new copy moved into its place. A
    failure while staging leaves every committed output as it was; a failure while moving
    puts the outputs already moved back, so new sites are never left beside old needs files.
    If putting them back fails too, the staging folder is kept and the error names it.
    """
    if not with_sites:
        refuse_unbuilt_sites(produced, committed(exchange_dir, with_sites=False))
    site_prefixes = tuple(f"{SITES_NAME}/{state}/" for state in SITES)
    files = {name: data for name, data in produced.items() if not name.startswith(site_prefixes)}
    owned = sorted(files)
    if with_sites:
        files = dict(produced)
        owned = [f"{SITES_NAME}/{state}" for state in SITES] + owned
    try:
        exchange_dir.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(dir=exchange_dir, prefix=".staging-"))
    except OSError as error:
        raise PrepareError(f"writing the outputs failed: {error}") from None
    new, old = staging / "new", staging / "old"
    moved: list[tuple[str, bool]] = []
    try:
        write_files(files, new)
        for relative in owned:
            target = exchange_dir / relative
            had_old = target.exists()
            if had_old:
                (old / relative).parent.mkdir(parents=True, exist_ok=True)
                target.rename(old / relative)
            moved.append((relative, had_old))
            if (new / relative).exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                (new / relative).rename(target)
    except OSError as error:
        try:
            for relative, had_old in reversed(moved):
                target = exchange_dir / relative
                if target.exists():
                    remove(target)
                if had_old:
                    (old / relative).rename(target)
        except OSError as restore_error:
            raise PrepareError(
                f"writing the outputs failed: {error}; putting the previous outputs back failed too: "
                f"{restore_error}; they are kept in {staging.relative_to(exchange_dir).as_posix()}/old"
            ) from None
        try:
            shutil.rmtree(staging)
        except OSError:
            pass  # the outputs are restored; the first error is the one to report
        raise PrepareError(f"writing the outputs failed, the previous outputs are kept: {error}") from None
    try:
        shutil.rmtree(staging)
    except OSError as error:
        raise PrepareError(
            f"the outputs are written, but removing {staging.relative_to(exchange_dir).as_posix()} failed: {error}"
        ) from None


def main(
    argv: list[str] | None = None,
    *,
    produce: Callable[[str, str | None, Path], dict[str, bytes]] = outputs,
    exchange_dir: Path = EXCHANGE_DIR,
    project_root: Path = PROJECT_ROOT,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare the committed files, write nothing")
    parser.add_argument("--sphinx-build", help="the team's sphinx-build: also build (or check) the four sites")
    args = parser.parse_args(argv)
    with_sites = bool(args.sphinx_build)

    def produce_after_the_checks(swcraft: str) -> dict[str, bytes]:
        # The pin is checked first (run_generator); a missing sphinx-build is refused before any work.
        sphinx_build = require_sphinx_build(args.sphinx_build) if with_sites else None
        return produce(swcraft, sphinx_build, project_root)

    return run_generator(
        project_root=project_root,
        output_dir=exchange_dir,
        outputs="the prepared files",
        check=args.check,
        produce=produce_after_the_checks,
        differing=lambda produced: differing(produced, committed(exchange_dir, with_sites)),
        write=lambda produced: write_outputs(produced, exchange_dir, with_sites),
    )


if __name__ == "__main__":
    sys.exit(main())
