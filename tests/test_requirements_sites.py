"""The requirements team's ready-made sites against their needs files, and the generator's guards.

Each site under ``demos/requirements-exchange/sites/<state>/`` is the team's Sphinx build of
``sites/<state>.needs.json`` (``scripts/generate_requirements_prepared.py --sphinx-build``);
``sites/1.0-original/`` is delivery 1.0 built with no needs file, and must show every delivered
requirement and no link into the architecture.
No test runs Sphinx, so this module holds the pair together without it (stdlib only): for
every requirement of the delivery the site shows, ``index.html`` has its table, and the links
it lists as incoming -- *satisfied by*, *satisfied by (unconfirmed)*, *derives*, *derives
(unconfirmed)* -- name exactly the architecture needs whose links in the needs file point at it. The comparison is **by need
id** (an anchor's text), never by ``href``: the ``target_url`` of the team's ``conf.py`` may
change where a link leads without changing what it links. Where the links lead is held
separately: every architecture link on a committed site is the ``vscode://`` address of the
need's ``swcraft_path``, as the team's ``conf.py`` writes it.

The generator's guards are held on fixtures, not on the committed files: a needs file is
never changed without its site (``--sphinx-build``), a rebuilt site replaces its folder whole,
the outputs are replaced as one set (a failed write puts the previous ones back),
the ``swcraft`` on ``PATH`` must answer the pin, a missing ``sphinx-build`` is refused before
any work, every command has a timeout, operating-system litter in a site folder is no
difference, ``--check`` masks Sphinx-Needs' random container ids and nothing else, and a
file that cannot be read is one ``Error:`` line. The kit builder's refusal of the same files
is in ``tests/test_build_colleague_kit.py``.

What this does not reach: anything on a site page but the incoming links (titles, content,
the needs table); the pages other than ``index.html``; whether the generator's real run
produces these files (``tests/test_requirements_exchange.py`` runs ``--check`` without
Sphinx, and the sites' bytes are checked with Sphinx on the maintainer's machine only).
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate
from swcraft_on_path import fake_swcraft

PROJECT_ROOT = gate.PROJECT_ROOT
EXCHANGE = PROJECT_ROOT / "demos" / "requirements-exchange"
PREPARED = gate.load_script("generate_requirements_prepared")

#: The link types the team's ``conf.py`` declares; a site page renders each incoming list in a
#: ``span`` of the link type's own name.
LINK_TYPES = ("satisfies", "satisfies_unconfirmed", "derived_from", "derived_from_unconfirmed")
Links = dict[str, dict[str, set[str]]]
#: Where an architecture need's link leads: the team's ``conf.py`` ``target_url`` with
#: ``{{need.swcraft_path | urlencode}}`` (Jinja's ``urlencode`` keeps ``/``).
VSCODE_LINK = "vscode://swcraft-local.swcraft-vscode/model?path="
#: An architecture need's link on a site page: its ``href`` and the need id it shows.
ARCHITECTURE_ANCHOR_RE = re.compile(r'<a class="swcraft reference external" href="([^"]*)">([^<]+)</a>')


class _SiteLinks(HTMLParser):
    """Need id -> link type -> the need ids its incoming list of that type names."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: Links = {}
        self.need: str | None = None
        self.table_depth = 0
        self.link: str | None = None
        self.span_depth = 0
        self.anchor: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag == "table":
            if self.need is not None:
                self.table_depth += 1
            elif "need" in classes and attributes.get("id"):
                self.need = attributes["id"]
                self.table_depth = 1
                self.links.setdefault(self.need, {})
        elif tag == "span" and self.need is not None:
            if self.link is not None:
                self.span_depth += 1
            elif len(classes) == 1 and classes[0] in LINK_TYPES:
                self.link = classes[0]
                self.span_depth = 1
                self.links[self.need].setdefault(self.link, set())
        elif tag == "a" and self.link is not None:
            self.anchor = []

    def handle_data(self, data: str) -> None:
        if self.anchor is not None:
            self.anchor.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchor is not None:
            assert self.need is not None and self.link is not None
            self.links[self.need][self.link].add("".join(self.anchor).strip())
            self.anchor = None
        elif tag == "span" and self.link is not None:
            self.span_depth -= 1
            if self.span_depth == 0:
                self.link = None
        elif tag == "table" and self.need is not None:
            self.table_depth -= 1
            if self.table_depth == 0:
                self.need = None


def site_links(page: str) -> Links:
    """The incoming links a site page shows: need id -> link type -> source need ids (empty types dropped)."""
    parser = _SiteLinks()
    parser.feed(page)
    parser.close()
    return {need: {link: sources for link, sources in links.items() if sources} for need, links in parser.links.items()}


def needs_file_links(document: dict, shown: set[str]) -> Links:
    """The same map from a needs file: every link of :data:`LINK_TYPES` whose target is a need in *shown*."""
    links: Links = {need: {} for need in shown}
    for need_id, need in document["versions"][document["current_version"]]["needs"].items():
        for link in LINK_TYPES:
            for target in need.get(link, []):
                if target in shown:
                    links[target].setdefault(link, set()).add(need_id)
    return links


def stale_links(page: str, document: dict, team: set[str]) -> list[str]:
    """Each need of *team* the page has no table for (``id: not shown``), and each need whose shown
    links differ from the needs file's (``id: shown ... != handed over ...``)."""
    shown = site_links(page)
    expected = needs_file_links(document, set(shown))
    missing = [f"{need}: not shown" for need in sorted(team - set(shown))]
    return missing + [
        f"{need}: shown {sorted((k, sorted(v)) for k, v in shown[need].items())} "
        f"!= handed over {sorted((k, sorted(v)) for k, v in expected[need].items())}"
        for need in sorted(shown)
        if shown[need] != expected[need]
    ]


def delivered_ids(state: str) -> set[str]:
    """The requirement ids of the delivery the site of *state* shows."""
    path = EXCHANGE / "deliveries" / PREPARED.STATES[state] / "needs.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    return set(document["versions"][document["current_version"]]["needs"])


def need_table(need_id: str, **links: list[str]) -> str:
    """A site page's need table as Sphinx-Needs writes it, reduced to what :func:`site_links` reads."""
    lines = "".join(
        f'<div class="line">{link}: <span class="{link}"><span>'
        + ", ".join(f'<a class="swcraft reference external" href="https://example.invalid/{source}">{source}</a>' for source in sources)
        + "</span></span></div>"
        for link, sources in links.items()
    )
    return (
        f'<div class="need_container docutils container" id="SNCB-0000abcd">'
        f'<table class="need needs_grid_simple docutils" id="{need_id}"><tbody><tr><td>'
        f'<span class="needs-id"><a class="reference internal" href="#{need_id}">{need_id}</a></span>'
        f"{lines}</td></tr></tbody></table></div>"
    )


def handover(**needs: dict[str, list[str]]) -> dict:
    """A needs file whose architecture needs carry *needs*' links."""
    return {"current_version": "1.0", "versions": {"1.0": {"needs": {need: {"id": need, **links} for need, links in needs.items()}}}}


class TestTheCommittedSites(unittest.TestCase):
    """Each committed site shows exactly the links of the needs file it was built from."""

    def test_each_site_shows_the_links_of_its_needs_file(self) -> None:
        for state in PREPARED.STATES:
            with self.subTest(state=state):
                sites = EXCHANGE / PREPARED.SITES_NAME
                page = (sites / state / "index.html").read_text(encoding="utf-8")
                document = json.loads((sites / f"{state}.needs.json").read_text(encoding="utf-8"))
                shown = site_links(page)
                self.assertGreater(sum(len(sources) for links in shown.values() for sources in links.values()), 0)
                self.assertEqual([], stale_links(page, document, delivered_ids(state)))

    def test_the_original_site_shows_every_requirement_and_no_architecture(self) -> None:
        """``1.0-original`` is delivery 1.0 as the team built it: each requirement's table, no link into SWCraft."""
        sites = EXCHANGE / PREPARED.SITES_NAME
        page = (sites / PREPARED.ORIGINAL / "index.html").read_text(encoding="utf-8")
        shown = site_links(page)
        self.assertEqual(delivered_ids("1.0"), set(shown))
        self.assertEqual({}, {need: links for need, links in shown.items() if any(links.values())})
        self.assertNotIn("swcraft reference external", page)
        self.assertFalse((sites / f"{PREPARED.ORIGINAL}.needs.json").exists())

    def test_a_site_beside_another_states_needs_file_is_stale(self) -> None:
        """The check is not vacuous on real pages: the one link awaiting confirmation tells 1.1's two states apart."""
        sites = EXCHANGE / PREPARED.SITES_NAME
        page = (sites / "1.1-unconfirmed" / "index.html").read_text(encoding="utf-8")
        document = json.loads((sites / "1.1-confirmed.needs.json").read_text(encoding="utf-8"))
        stale = stale_links(page, document, delivered_ids("1.1-confirmed"))
        self.assertEqual(1, len(stale), stale)
        self.assertTrue(stale[0].startswith("SWR-THP-003: "), stale)

    def test_every_architecture_link_opens_its_file_in_vs_code(self) -> None:
        """The sites link as the team's ``conf.py`` says: ``vscode://`` and the need's ``swcraft_path``.

        This holds the rebuilt sites to the link of ``conf.py``'s one ``needs_external_needs``
        entry (``tests/test_requirements_deliveries.py`` holds the entry itself); the links
        compared by need id above would hold an old link too.
        """
        for state in PREPARED.STATES:
            with self.subTest(state=state):
                sites = EXCHANGE / PREPARED.SITES_NAME
                page = (sites / state / "index.html").read_text(encoding="utf-8")
                document = json.loads((sites / f"{state}.needs.json").read_text(encoding="utf-8"))
                needs = document["versions"][document["current_version"]]["needs"]
                anchors = ARCHITECTURE_ANCHOR_RE.findall(page)
                self.assertTrue(anchors)
                self.assertEqual(len(anchors), page.count('class="swcraft reference external"'))
                for href, need_id in set(anchors):
                    self.assertEqual(VSCODE_LINK + quote(needs[need_id]["swcraft_path"], safe="/"), href, need_id)
                self.assertNotIn("https://", "".join(href for href, _ in anchors))


class TestTheSiteCheck(unittest.TestCase):
    """:func:`stale_links` on fixtures."""

    PAGE = need_table("SWR-A-001", satisfies=["RUN-X-Run", "SWC-X"]) + need_table("SWR-A-002")
    TEAM = {"SWR-A-001", "SWR-A-002"}

    def test_a_site_built_from_its_needs_file_passes(self) -> None:
        document = handover(**{"RUN-X-Run": {"satisfies": ["SWR-A-001"]}, "SWC-X": {"satisfies": ["SWR-A-001", "REQ_ELSEWHERE"]}})
        self.assertEqual([], stale_links(self.PAGE, document, self.TEAM))

    def test_a_link_the_needs_file_no_longer_holds_is_refused(self) -> None:
        document = handover(**{"SWC-X": {"satisfies": ["SWR-A-001"]}})
        stale = stale_links(self.PAGE, document, self.TEAM)
        self.assertEqual(1, len(stale))
        self.assertIn("SWR-A-001", stale[0])

    def test_a_link_the_site_does_not_show_is_refused(self) -> None:
        document = handover(
            **{"RUN-X-Run": {"satisfies": ["SWR-A-001"]}, "SWC-X": {"satisfies": ["SWR-A-001", "SWR-A-002"]}}
        )
        self.assertEqual(["SWR-A-002"], [line.split(":")[0] for line in stale_links(self.PAGE, document, self.TEAM)])

    def test_a_requirement_whose_table_is_missing_is_refused(self) -> None:
        """A table missing from the page entirely is no table whose links agree: it is named."""
        page = need_table("SWR-A-001", satisfies=["RUN-X-Run", "SWC-X"])
        document = handover(
            **{"RUN-X-Run": {"satisfies": ["SWR-A-001"]}, "SWC-X": {"satisfies": ["SWR-A-001", "SWR-A-002"]}}
        )
        self.assertEqual(["SWR-A-002: not shown"], stale_links(page, document, self.TEAM))

    def test_a_confirmed_link_is_not_an_unconfirmed_one(self) -> None:
        document = handover(**{"RUN-X-Run": {"satisfies": ["SWR-A-001"]}, "SWC-X": {"satisfies_unconfirmed": ["SWR-A-001"]}})
        self.assertEqual(["SWR-A-001"], [line.split(":")[0] for line in stale_links(self.PAGE, document, self.TEAM)])

    def test_the_href_is_not_compared(self) -> None:
        page = self.PAGE.replace("https://example.invalid/", "vscode://swcraft-local.swcraft-vscode/model?path=")
        document = handover(**{"RUN-X-Run": {"satisfies": ["SWR-A-001"]}, "SWC-X": {"satisfies": ["SWR-A-001"]}})
        self.assertEqual([], stale_links(page, document, self.TEAM))


@unittest.skipIf(os.name == "nt", "the fake swcraft is a POSIX script")
class TestTheGenerator(gate.GeneratorCase, unittest.TestCase):
    """``scripts/generate_requirements_prepared.py``'s guards, with its SWCraft steps replaced.

    The refusals of no ``swcraft`` and of another release are :class:`gate.GeneratorCase`'s.
    """

    generator = PREPARED

    def setUp(self) -> None:
        super().setUp()
        self.exchange = self.output_dir
        sites = self.exchange / PREPARED.SITES_NAME
        for state in PREPARED.STATES:
            (sites / state).mkdir(parents=True)
            (sites / f"{state}.needs.json").write_text("{}\n", encoding="utf-8", newline="\n")
            (sites / state / "index.html").write_text(f"<p>{state}</p>\n", encoding="utf-8", newline="\n")
        (self.exchange / PREPARED.PREPARED_NAME).write_text("{}\n", encoding="utf-8", newline="\n")
        self.produced = {
            PREPARED.PREPARED_NAME: b'{"new": true}\n',
            **{f"{PREPARED.SITES_NAME}/{state}.needs.json": b"{}\n" for state in PREPARED.STATES},
        }

    def main_hooks(self) -> dict[str, Path]:
        return {"exchange_dir": self.exchange}

    def test_the_pinned_swcraft_writes_when_no_needs_file_changes(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        code, stderr = self.run_main()
        self.assertEqual(0, code, stderr)
        self.assertEqual(b'{"new": true}\n', (self.exchange / PREPARED.PREPARED_NAME).read_bytes())

    def test_a_changed_needs_file_without_its_site_is_refused_and_nothing_is_written(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        self.produced[f"{PREPARED.SITES_NAME}/1.1-confirmed.needs.json"] = b'{"changed": true}\n'
        before = self.snapshot()
        code, stderr = self.run_main()
        self.assertEqual(2, code)
        self.assertIn("sites/1.1-confirmed.needs.json would change", stderr)
        self.assertIn("--sphinx-build", stderr)
        self.assertEqual(before, self.snapshot())

    def test_a_changed_needs_file_with_its_site_rebuilt_is_written(self) -> None:
        """Each site folder is replaced whole: what the build wrote, and no file of the old one; the original gets no needs file."""
        fake_swcraft(self.bin, "9.8.7")
        sphinx = fake_swcraft(self.root, "0")  # any executable: the build itself is replaced
        changed = f"{PREPARED.SITES_NAME}/1.1-confirmed.needs.json"
        self.produced[changed] = b'{"changed": true}\n'
        for state in PREPARED.SITES:
            self.produced[f"{PREPARED.SITES_NAME}/{state}/index.html"] = f"<p>rebuilt {state}</p>\n".encode()
        self.produced[f"{PREPARED.SITES_NAME}/1.0/_static/new.css"] = b"p {}\n"
        sites = self.exchange / PREPARED.SITES_NAME
        (sites / "1.0" / "stray.html").write_bytes(b"<p>left from an earlier build</p>\n")
        (sites / "1.1-unconfirmed" / "_images").mkdir()
        (sites / "1.1-unconfirmed" / "_images" / "old.png").write_bytes(b"old")
        code, stderr = self.run_main("--sphinx-build", str(sphinx))
        self.assertEqual(0, code, stderr)
        self.assertEqual([(str(self.bin / "swcraft"), str(sphinx), self.project)], self.calls)
        self.assertEqual(b'{"changed": true}\n', (self.exchange / changed).read_bytes())
        for state in PREPARED.SITES:
            with self.subTest(state=state):
                written = {path.relative_to(sites / state).as_posix() for path in (sites / state).rglob("*") if path.is_file()}
                expected = {"index.html", "_static/new.css"} if state == "1.0" else {"index.html"}
                self.assertEqual(expected, written)
                self.assertEqual(f"<p>rebuilt {state}</p>\n".encode(), (sites / state / "index.html").read_bytes())
        self.assertEqual(
            sorted([*PREPARED.SITES, *(f"{state}.needs.json" for state in PREPARED.STATES)]),
            sorted(path.name for path in sites.iterdir()),
            "no staging folder is left beside the sites",
        )
        self.assertEqual(
            sorted([PREPARED.PREPARED_NAME, PREPARED.SITES_NAME]),
            sorted(path.name for path in self.exchange.iterdir()),
            "no staging folder is left beside the outputs",
        )

    def rebuild_all(self) -> Path:
        """A run with the sites in which every output changes; the fake ``sphinx-build``."""
        fake_swcraft(self.bin, "9.8.7")
        sphinx = fake_swcraft(self.root, "0")
        for state in PREPARED.STATES:
            self.produced[f"{PREPARED.SITES_NAME}/{state}.needs.json"] = f'{{"new": "{state}"}}\n'.encode()
            self.produced[f"{PREPARED.SITES_NAME}/{state}/index.html"] = f"<p>rebuilt {state}</p>\n".encode()
        return sphinx

    def test_a_failure_after_the_sites_moved_puts_every_output_back(self) -> None:
        """The last needs file cannot be moved into place: the sites already swapped go back too."""
        sphinx = self.rebuild_all()
        before = self.snapshot()
        rename = Path.rename

        def failing_rename(path: Path, target: Path) -> Path:
            if path.name == "1.1-unconfirmed.needs.json" and "new" in path.parts:
                raise PermissionError("denied")
            return rename(path, target)

        with mock.patch.object(Path, "rename", failing_rename):
            code, stderr = self.run_main("--sphinx-build", str(sphinx))
        self.assertEqual(2, code)
        self.assertEqual("Error: writing the outputs failed, the previous outputs are kept: denied\n", stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], list(self.exchange.glob(".staging-*")))

    def test_a_failure_while_staging_changes_no_output(self) -> None:
        sphinx = self.rebuild_all()
        before = self.snapshot()
        with mock.patch.object(Path, "write_bytes", side_effect=OSError(28, "No space left on device")):
            code, stderr = self.run_main("--sphinx-build", str(sphinx))
        self.assertEqual(2, code)
        self.assertIn("No space left on device", stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], list(self.exchange.glob(".staging-*")))

    def test_a_failed_restore_keeps_the_previous_outputs_and_names_them(self) -> None:
        sphinx = self.rebuild_all()
        before = self.snapshot()
        rename = Path.rename

        def failing_rename(path: Path, target: Path) -> Path:
            if path.name == "1.1-unconfirmed.needs.json" and ("new" in path.parts or "old" in path.parts):
                raise PermissionError("denied")
            return rename(path, target)

        with mock.patch.object(Path, "rename", failing_rename):
            code, stderr = self.run_main("--sphinx-build", str(sphinx))
        self.assertEqual(2, code)
        self.assertRegex(
            stderr,
            r"^Error: writing the outputs failed: denied; putting the previous outputs back failed too: "
            r"denied; they are kept in \.staging-[^/\s]+/old\n$",
        )
        kept = next(self.exchange.glob(".staging-*")) / "old"
        self.assertEqual(
            before[f"{PREPARED.SITES_NAME}/1.1-unconfirmed.needs.json"],
            (kept / PREPARED.SITES_NAME / "1.1-unconfirmed.needs.json").read_bytes(),
        )

    def test_a_missing_sphinx_build_is_refused_before_any_work(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        code, stderr = self.run_main("--sphinx-build", str(self.root / "no-such-sphinx-build"))
        self.assertEqual(2, code)
        self.assertIn("is not an executable", stderr)
        self.assertEqual([], self.calls)

    def test_operating_system_litter_in_a_site_is_no_difference(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        sphinx = fake_swcraft(self.root, "0")
        self.produced = {**self.produced, PREPARED.PREPARED_NAME: b"{}\n"}
        for state in PREPARED.STATES:
            self.produced[f"{PREPARED.SITES_NAME}/{state}/index.html"] = f"<p>{state}</p>\n".encode()
        for name in PREPARED.IGNORED_NAMES:
            (self.exchange / PREPARED.SITES_NAME / "1.0" / name).write_bytes(b"litter")
        code, stderr = self.run_main("--check", "--sphinx-build", str(sphinx))
        self.assertEqual(0, code, stderr)
        (self.exchange / PREPARED.SITES_NAME / "1.0" / ".buildinfo").write_bytes(b"left over")
        code, stderr = self.run_main("--check", "--sphinx-build", str(sphinx))
        self.assertEqual(1, code)
        self.assertIn("sites/1.0/.buildinfo", stderr)

    def check_site_page(self, produced_page: bytes, committed_page: bytes) -> tuple[int, str]:
        """``--check`` with the sites, every file equal but 1.0's ``index.html``."""
        fake_swcraft(self.bin, "9.8.7")
        sphinx = fake_swcraft(self.root, "0")
        self.produced = {**self.produced, PREPARED.PREPARED_NAME: b"{}\n"}
        for state in PREPARED.STATES:
            self.produced[f"{PREPARED.SITES_NAME}/{state}/index.html"] = f"<p>{state}</p>\n".encode()
        self.produced[f"{PREPARED.SITES_NAME}/1.0/index.html"] = produced_page
        (self.exchange / PREPARED.SITES_NAME / "1.0" / "index.html").write_bytes(committed_page)
        return self.run_main("--check", "--sphinx-build", str(sphinx))

    def test_check_masks_sphinx_needs_random_container_ids(self) -> None:
        code, stderr = self.check_site_page(
            b'<div class="need_container" id="SNCB-0123abcd">x</div>\n',
            b'<div class="need_container" id="SNCB-fedc9876">x</div>\n',
        )
        self.assertEqual(0, code, stderr)

    def test_check_finds_a_difference_beside_a_masked_id(self) -> None:
        code, stderr = self.check_site_page(
            b'<div class="need_container" id="SNCB-0123abcd">x</div>\n',
            b'<div class="need_container" id="SNCB-fedc9876">y</div>\n',
        )
        self.assertEqual(1, code)
        self.assertIn("sites/1.0/index.html", stderr)

    def test_an_unreadable_committed_file_is_one_error_line(self) -> None:
        fake_swcraft(self.bin, "9.8.7")
        with mock.patch.object(Path, "read_bytes", side_effect=PermissionError("denied")):
            code, stderr = self.run_main("--check")
        self.assertEqual(2, code)
        self.assertEqual("Error: denied\n", stderr)


class TestTheGeneratorsSteps(unittest.TestCase):
    """The generator's error handling and timeouts, step by step."""

    def test_a_command_that_outlives_the_timeout_is_an_error(self) -> None:
        with mock.patch.object(gate.PINNED, "COMMAND_TIMEOUT", 0.2), self.assertRaisesRegex(gate.PINNED.ToolchainError, "did not finish within"):
            gate.PINNED.run_command([sys.executable, "-c", "import time; time.sleep(10)"], "the sleeper")

    def test_a_command_that_cannot_start_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(gate.PINNED.ToolchainError, "could not be started"):
            gate.PINNED.run_command([str(Path(tmp) / "missing")], "the missing command")

    def test_a_malformed_answer_key_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / "demos" / "requirements-exchange" / "answer-key.json"
            key.parent.mkdir(parents=True)
            key.write_text("{not json", encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(PREPARED.PrepareError, "the answer key could not be read"):
                PREPARED.answer_key(Path(tmp))
            key.write_text('{"requirements": []}', encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(PREPARED.PrepareError, "not shaped as expected"):
                PREPARED.answer_key(Path(tmp))

    def test_a_manifest_without_one_pin_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "swcraft.yaml").write_text("name: x\n", encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(gate.PINNED.ToolchainError, "declares no toolchain_version"):
                gate.PINNED.pinned_version(Path(tmp) / "swcraft.yaml")

    def hand_proposals(self) -> dict:
        """A search with one row for each requirement step 2 decides by hand."""
        row = {"target": {"kind": "swc", "name": "X"}, "band": "strong", "score": {"n": 1}, "place": 0}
        requirements = [
            {"id": need_id, "linked": [], "chosen": [], "candidates": [dict(row)]}
            for need_id in (*PREPARED.HAND_LINKS, PREPARED.HAND_REJECT)
        ]
        return {"requirements": requirements}

    def test_the_hand_decisions_name_a_requirement_the_search_or_the_key_lacks(self) -> None:
        key = {need_id: [{"kind": "swc", "name": "X"}] for need_id in PREPARED.HAND_LINKS}
        proposals = self.hand_proposals()
        PREPARED.decide_by_hand(proposals, key)
        proposals = self.hand_proposals()
        proposals["requirements"] = [entry for entry in proposals["requirements"] if entry["id"] != PREPARED.HAND_LINKS[0]]
        with self.assertRaisesRegex(PREPARED.PrepareError, f"lists no {PREPARED.HAND_LINKS[0]}"):
            PREPARED.decide_by_hand(proposals, key)
        with self.assertRaisesRegex(PREPARED.PrepareError, f"links {PREPARED.HAND_LINKS[1]}, which step 2"):
            PREPARED.decide_by_hand(self.hand_proposals(), {**key, PREPARED.HAND_LINKS[1]: []})
        proposals = self.hand_proposals()
        proposals["requirements"][-1]["candidates"] = []
        with self.assertRaisesRegex(PREPARED.PrepareError, f"no candidate for {PREPARED.HAND_REJECT}"):
            PREPARED.decide_by_hand(proposals, key)


if __name__ == "__main__":
    unittest.main()
