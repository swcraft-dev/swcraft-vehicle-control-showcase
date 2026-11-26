"""Stdlib test: the open copy's allow-list partitions this repository, and its legal files are in place.

``public-paths.txt`` names what the open copy holds; everything else is closed. This test holds the
partition in the repository's own suite, so a new top-level folder (or a new ``docs/`` child) forces a
decision in the commit that adds it:

* every tracked top-level entry, and every child of ``docs/``, is opened by an entry of the list or
  sits on the closed list :data:`CLOSED` -- the maintainer's records and the work repository's gate;
* every entry exists among the tracked files (``git ls-files``), and no entry is, holds or sits
  inside a closed path.

It reimplements only "is this path under an entry"; validating the list's syntax and assembling the
snapshot stay SWCraft's ``scripts/public_snapshot.py``. In the public tree the closed folders are
absent, and the partition holds there just the same.

The legal files: ``LICENSE`` is the Apache License 2.0 text verbatim (its SHA-256 is the one of
``https://www.apache.org/licenses/LICENSE-2.0.txt``), ``NOTICE`` is exactly its four lines, and
``THIRD-PARTY-NOTICES.md`` names each vendored component with its licence text and every file of the
ready-made sites' ``_static/`` folder.

The hygiene scan reads every open file that decodes as UTF-8 (the open paths: ``git ls-files`` within
the list's entries, so the closed records, which hold such strings by right, are not its business,
and the answer is the same in the public tree) and fails on:

* an RFC 1918 IPv4 address;
* an absolute home path -- ``/Users/<name>``, ``/home/<name>``, ``C:\\Users\\<name>`` -- whose user is
  not a placeholder (:data:`HOME_PLACEHOLDERS`; a ``<...>`` name is a placeholder by its form);
* an e-mail address, unless its local part is ``noreply``, its domain is an ``example`` domain,
  ``invalid`` or GitHub's ``users.noreply.github.com``, or it is one of the upstream attribution
  addresses (:data:`UPSTREAM_ADDRESSES`), each quoted in a vendored component's licence text, and
  only in ``THIRD-PARTY-NOTICES.md`` and the vendored files (:data:`VENDORED_PATHS`);
* in a Markdown file, a link whose relative target is not an open path (a link into a closed path
  would be dead in the open copy); code spans and fenced blocks are not links;
* in a user-facing file (``README.md`` and ``docs/guide/``), a closed path at all, link or not.

It names no private word: a public list of private names would publish them. The names are the
closed deny-list's, which the maintainer's publish step checks. This file's own negative vectors are
built by concatenation at run time, so it passes its own scan without an exemption.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALLOW_LIST = PROJECT_ROOT / "public-paths.txt"

#: The closed set: tracked, never opened.
CLOSED = ("docs/evidence/", "docs/plans/", "docs/notes/", ".gitea/")
#: The one folder whose children are opened or closed one by one.
SPLIT_FOLDER = "docs/"

APACHE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
NOTICE_LINES = [
    "SWCraft Vehicle Control Showcase",
    "Copyright 2026 Konstantin Tarandevich",
    "",
    '"SWCraft" is a name not licensed under the Apache License, Version 2.0 (section 6).',
]
#: The vendored components: each is named in the notices and has its licence text under a
#: ``### <name> <version>`` heading.
VENDORED = (
    "Sphinx",
    "Snowball",
    "Pygments",
    "alabaster",
    "jQuery",
    "sphinx-needs",
    "sphinx-data-viewer",
    "Marp CLI",
    "Marp Core",
)
SITES = PROJECT_ROOT / "demos" / "requirements-exchange" / "sites"
#: The SHA-256 of each licence text in THIRD-PARTY-NOTICES.md, the body of the ``text`` fence under
#: its ``###`` heading. Names and headings alone would let an emptied or altered text through; a
#: licence text is fixed for its version, so a digest is not brittle, and a version bump that
#: changes a text changes its digest here on purpose. Marp CLI and Marp Core ship the same MIT text.
_MARP_MIT = "f2b31d0b3aa8ec75832e76b5deb842d8889f7121e9419414b4e32ab37327e64b"
LICENCE_SHA256 = {
    "Sphinx 9.0.4": "64c96919bbaf3a13baa0f10e418cc1fc88768ce1b9c07f5b7bf49f0fb23db106",
    "Snowball 3.0.1": "f6f9e4c0e737728ca980de8595ded046d5e077017c1bb0ee05dc794a01434dae",
    "Pygments 2.21.0": "a9d66f1d526df02e29dce73436d34e56e8632f46c275bbdffc70569e882f9f17",
    "alabaster 1.0.0": "8253f0abaad05a7dee1a08a43705ac2de1f73bd7d44cfe01010ecc104cc42851",
    "jQuery 3.6.0": "d4db9ebe6f29f5168eac45ad713f055623ac5d0dcd5ba92da23d650ae012020d",
    "sphinx-needs 9.2.0": "2c15ddff5dbbf8fbfd146abb953ca2054aad2f847fd4c21f6e58efa7aa5defd5",
    "sphinx-data-viewer 0.1.5": "9327cd48d897af09ce0937a9a103f79325fd0c05311427c7ae9dfba80871c90b",
    "Marp CLI 4.4.1": _MARP_MIT,
    "Marp Core 4.3.1": _MARP_MIT,
    "bespoke 1.2.0-dev and vhtml 2.2.0, bundled in Marp CLI's viewer script"
    " (`lib/bespoke.js.LICENSE.txt` of Marp CLI 4.4.1)": "2d38c6129460545854b707145d6db8b2f6c85f0e5ed15b86df5df1561a9ad970",
}
LICENCE_SECTION = re.compile(r"^### ([^\n]+)\n\n```text\n(.*?)^```$", re.MULTILINE | re.DOTALL)


def parse_entries(text: str) -> list[str]:
    """The allow-list's entries: one per line, ``#`` comments and blank lines dropped."""
    entries = []
    for line in text.splitlines():
        value = line.split("#", 1)[0].strip()
        if value:
            entries.append(value)
    return entries


def under(path: str, entry: str) -> bool:
    """Whether *path* (a file, or a folder ending in ``/``) is *entry* or inside the folder *entry*."""
    return path == entry or (entry.endswith("/") and path.startswith(entry))


def units(tracked: list[str]) -> set[str]:
    """The partition's units: each top-level file or folder, with ``docs/`` split into its children."""
    found = set()
    for path in tracked:
        head, sep, rest = path.partition("/")
        if not sep:
            found.add(head)
        elif head + "/" == SPLIT_FOLDER:
            child, deeper, _ = rest.partition("/")
            found.add(SPLIT_FOLDER + child + ("/" if deeper else ""))
        else:
            found.add(head + "/")
    return found


def partition_problems(entries: list[str], tracked: list[str]) -> list[str]:
    """One sentence per way *entries* fail to partition *tracked* into opened and :data:`CLOSED`."""
    problems = []
    for entry in entries:
        if not any(under(path, entry) for path in tracked):
            problems.append(f"{entry} is listed but no tracked file is {'under it' if entry.endswith('/') else 'it'}")
        for closed in CLOSED:
            if under(entry, closed) or under(closed, entry):
                problems.append(f"{entry} opens the closed path {closed}")
    for unit in sorted(units(tracked)):
        opened = any(under(unit, entry) for entry in entries)
        closed = any(under(unit, path) for path in CLOSED)
        if not opened and not closed:
            problems.append(f"{unit} is neither opened by public-paths.txt nor on the closed list")
    return problems


def tracked_files(root: Path) -> list[str]:
    """``git ls-files`` of *root*, as POSIX paths."""
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True, timeout=60
    )
    return [name for name in completed.stdout.decode("utf-8").split("\0") if name]


# --- Hygiene -------------------------------------------------------------------------------------

#: User names in a home path that stand for nobody in particular.
HOME_PLACEHOLDERS = frozenset({"someone", "you", "runner", "dev", "u"})
#: Upstream attribution addresses, measured in the vendored components' licence texts (Marp's
#: licence holder; vhtml's author, bundled in Marp's viewer). Allowed only in :data:`VENDORED_PATHS`.
#: Joined at run time, so this file holds no address of its own.
UPSTREAM_ADDRESSES = frozenset({"marp-team" + "@" + "marp.app", "jason" + "@" + "developit.ca"})
#: The notices and the vendored files: the sites' ``_static/`` folders and the presentation HTML,
#: which inlines Marp's runtime. Each matches a whole open path.
VENDORED_PATHS = (
    re.compile(r"THIRD-PARTY-NOTICES\.md"),
    re.compile(r"demos/requirements-exchange/sites/[^/]+/_static/.+"),
    re.compile(r"demos/requirements-exchange-presentation[^/]*\.html"),
)
#: The user-facing files, which name no closed path at all.
USER_FACING = ("README.md", "docs/guide/")

_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
PRIVATE_IPV4 = re.compile(
    r"(?<![\d.])(?:10\.{o}\.{o}\.{o}|172\.(?:1[6-9]|2\d|3[01])\.{o}\.{o}|192\.168\.{o}\.{o})(?!\.?\d)".format(o=_OCTET)
)
HOME_PATH = re.compile(r"(?:/Users/|/home/|\b[A-Za-z]:\\+Users\\+)([^\s/\\<>\"'`|)(\]\[*]+)")
EMAIL = re.compile(r"(?<![\w.+-])([\w.+-]+)@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})\b")
FENCE = re.compile(r"^ {0,3}(```|~~~).*?^ {0,3}\1[^\n]*$", re.MULTILINE | re.DOTALL)
CODE_SPAN = re.compile(r"(`+)(?:(?!\1).)+?\1", re.DOTALL)
#: A destination in angle brackets may hold spaces (CommonMark), so it is read to its ``>``.
INLINE_LINK = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?:<([^<>\n]*)>|([^)\s<>]+))(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
LINK_DEFINITION = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*(?:<([^<>\n]*)>|([^\s<>]+))(?:\s|$)", re.MULTILINE)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def licence_text_problems(notices: str) -> list[str]:
    """One line per licence text of *notices* missing or not the one :data:`LICENCE_SHA256` holds."""
    texts = notices.split("\n## Licence texts\n", 1)[-1]
    found = {match.group(1): match.group(2) for match in LICENCE_SECTION.finditer(texts)}
    problems = []
    for heading, digest in LICENCE_SHA256.items():
        if heading not in found:
            problems.append(f"no licence text under '### {heading}'")
        elif hashlib.sha256(found[heading].encode("utf-8")).hexdigest() != digest:
            problems.append(f"the licence text under '### {heading}' is not the one distributed")
    problems += [f"a licence text no digest holds: '### {heading}'" for heading in found if heading not in LICENCE_SHA256]
    return problems


def is_vendored(path: str) -> bool:
    """Whether *path* is the notices file or one of the vendored files."""
    return any(pattern.fullmatch(path) for pattern in VENDORED_PATHS)


def allowed_address(local: str, domain: str, path: str) -> bool:
    """Whether the address *local*@*domain* may stand in the open file *path*."""
    domain = domain.lower()
    if local.lower() == "noreply" or domain == "users.noreply.github.com":
        return True
    if domain.split(".")[0] == "example" or domain == "invalid" or domain.endswith(".invalid"):
        return True
    return f"{local}@{domain}" in UPSTREAM_ADDRESSES and is_vendored(path)


def blank(match: re.Match[str]) -> str:
    """The match replaced by spaces, newlines kept, so line numbers stay true."""
    return re.sub(r"[^\n]", " ", match.group(0))


def link_targets(text: str) -> list[tuple[int, str]]:
    """The targets of a Markdown text's inline links and link definitions, with their line numbers."""
    prose = CODE_SPAN.sub(blank, FENCE.sub(blank, text))
    found = []
    for pattern in (INLINE_LINK, LINK_DEFINITION):
        for match in pattern.finditer(prose):
            target = match.group(1) if match.group(1) is not None else match.group(2)
            found.append((prose.count("\n", 0, match.start()) + 1, target))
    return sorted(found)


def dead_link(path: str, target: str, opened: frozenset[str]) -> bool:
    """Whether the relative link *target* in the Markdown file *path* leads to no open path."""
    if SCHEME.match(target) or target.startswith(("#", "/")):
        return False
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return False
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
    if resolved == ".":
        return False
    if resolved.startswith("../"):
        return True
    return resolved not in opened and not any(name.startswith(resolved + "/") for name in opened)


def hygiene_problems(files: dict[str, str], opened: frozenset[str] | None = None) -> list[str]:
    """One line per finding in *files* (open path -> text): ``path:line: what: the text found``.

    A relative link must lead to one of *opened*: every open path, the images among them, which
    *files* (the texts) leaves out. Without it, the paths of *files* stand in.
    """
    opened = frozenset(files) if opened is None else opened
    problems = []
    for path, text in sorted(files.items()):
        user_facing = any(under(path, entry) for entry in USER_FACING)
        for number, line in enumerate(text.split("\n"), 1):
            where = f"{path}:{number}"
            for match in PRIVATE_IPV4.finditer(line):
                problems.append(f"{where}: private address: {match.group(0)}")
            for match in HOME_PATH.finditer(line):
                if match.group(1) not in HOME_PLACEHOLDERS:
                    problems.append(f"{where}: home path: {match.group(0)}")
            for match in EMAIL.finditer(line):
                if not allowed_address(match.group(1), match.group(2), path):
                    problems.append(f"{where}: e-mail address: {match.group(0)}")
            if user_facing:
                for closed in CLOSED:
                    if closed in line:
                        problems.append(f"{where}: closed path in a user-facing file: {closed}")
        if path.endswith(".md"):
            for number, target in link_targets(text):
                if dead_link(path, target, opened):
                    problems.append(f"{path}:{number}: link to no open path: {target}")
    return problems


def open_paths(root: Path) -> list[str]:
    """Every tracked file of *root* that public-paths.txt opens."""
    entries = parse_entries((root / "public-paths.txt").read_text(encoding="utf-8"))
    return [path for path in tracked_files(root) if any(under(path, entry) for entry in entries)]


def open_texts(root: Path) -> dict[str, str]:
    """Every open file of *root* that decodes as UTF-8, by path; the others (images) are skipped."""
    texts = {}
    for path in open_paths(root):
        try:
            texts[path] = (root / path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return texts


class TestPartitionHelper(unittest.TestCase):
    TRACKED = [
        ".gitea/workflows/verify.yml",
        "README.md",
        "tests/test_x.py",
        "docs/briefs/FB.md",
        "docs/guide/install.md",
        "docs/plans/p.md",
        "docs/evidence/run.md",
    ]
    GOOD = ["README.md", "tests/", "docs/briefs/", "docs/guide/"]

    def test_a_complete_list_is_accepted(self) -> None:
        self.assertEqual([], partition_problems(self.GOOD, self.TRACKED))

    def test_a_list_missing_tests_is_refused(self) -> None:
        entries = [entry for entry in self.GOOD if entry != "tests/"]
        self.assertEqual(
            ["tests/ is neither opened by public-paths.txt nor on the closed list"],
            partition_problems(entries, self.TRACKED),
        )

    def test_a_list_opening_a_closed_path_is_refused(self) -> None:
        for entry in ("docs/plans/", "docs/", ".gitea/workflows/", "docs/evidence/run.md"):
            with self.subTest(entry=entry):
                problems = partition_problems(self.GOOD + [entry], self.TRACKED)
                self.assertTrue(any("opens the closed path" in problem for problem in problems), problems)

    def test_an_entry_naming_nothing_tracked_is_refused(self) -> None:
        self.assertEqual(
            ["kit/ is listed but no tracked file is under it", "NOTICE is listed but no tracked file is it"],
            partition_problems(self.GOOD + ["kit/", "NOTICE"], self.TRACKED),
        )

    def test_a_new_docs_child_needs_a_decision(self) -> None:
        tracked = self.TRACKED + ["docs/drafts/d.md", "docs/loose.md"]
        self.assertEqual(
            [
                "docs/drafts/ is neither opened by public-paths.txt nor on the closed list",
                "docs/loose.md is neither opened by public-paths.txt nor on the closed list",
            ],
            partition_problems(self.GOOD, tracked),
        )

    def test_comments_and_blank_lines_are_not_entries(self) -> None:
        self.assertEqual(["tests/", "README.md"], parse_entries("# head\n\ntests/\n  README.md  # root\n"))


class TestHygieneHelper(unittest.TestCase):
    """Each pattern on in-memory text. The vectors are concatenated, so this file passes its own scan."""

    def test_a_clean_text_passes(self) -> None:
        text = (
            "Version 10.1.0 and 1.192.168.0.1.5 are no addresses; /Users/<name>, /home/runner/work and "
            "C:\\Users\\you\\project are placeholders; someone@example.com, noreply@" + "github.com, "
            "12345+someone@users.noreply.github.com and snapshot@build.invalid are allowed.\n"
        )
        self.assertEqual([], hygiene_problems({"README.md": text}))

    def test_a_private_address_is_refused(self) -> None:
        for address in ("192." + "168.0.1", "10." + "0.0.7", "172." + "16.4.2", "172." + "31.255.255"):
            with self.subTest(address=address):
                found = hygiene_problems({"tests/x.py": f"HOST = '{address}'\n"})
                self.assertEqual([f"tests/x.py:1: private address: {address}"], found)
        self.assertEqual([], hygiene_problems({"tests/x.py": "172." + "32.0.1 and 8.8.8.8\n"}))

    def test_a_home_path_is_refused_unless_a_placeholder(self) -> None:
        for path in ("/Us" + "ers/alice/x", "/ho" + "me/alice/x", "C:\\Us" + "ers\\alice\\x", "c:\\\\Us" + "ers\\\\alice"):
            with self.subTest(path=path):
                found = hygiene_problems({"kit/README.md": f"see {path}\n"})
                self.assertEqual(1, len(found), found)
                self.assertIn("home path", found[0])
        for path in ("/Us" + "ers/someone/x", "/ho" + "me/dev/x", "C:\\Us" + "ers\\u\\x", "/Us" + "ers/<you>/x"):
            with self.subTest(path=path):
                self.assertEqual([], hygiene_problems({"kit/README.md": f"see {path}\n"}))

    def test_an_email_address_is_refused(self) -> None:
        address = "alice" + "@" + "corp.test.org"
        self.assertEqual(
            [f"demos/a.md:2: e-mail address: {address}"],
            hygiene_problems({"demos/a.md": f"one\nwrite to {address}\n"}),
        )

    def test_an_upstream_address_is_allowed_only_in_the_vendored_files(self) -> None:
        address = "marp-team" + "@" + "marp.app"
        line = f"Copyright (c) 2018 Marp team ({address})\n"
        for path in (
            "THIRD-PARTY-NOTICES.md",
            "demos/requirements-exchange/sites/1.0/_static/jquery.js",
            "demos/requirements-exchange-presentation-public.html",
        ):
            with self.subTest(path=path):
                self.assertEqual([], hygiene_problems({path: line}))
        self.assertEqual(
            [f"README.md:1: e-mail address: {address}"], hygiene_problems({"README.md": line})
        )

    def test_a_link_to_no_open_path_is_refused(self) -> None:
        files = {
            "demos/README.md": (
                "[ok](test-tables.md) [anchor](#top) [web](https://example.com/x) [up](../README.md#licence)\n"
                "[gone](../docs/" + "plans/p.md) `[code](nowhere.md)`\n"
                "```\n[fenced](nowhere.md)\n```\n"
                "[ref]: missing.md\n"
            ),
            "demos/test-tables.md": "",
            "README.md": "[folder](demos) [image](demos/test-tables.md)\n[out](../../outside.md)\n",
        }
        self.assertEqual(
            [
                "README.md:2: link to no open path: ../../outside.md",
                "demos/README.md:2: link to no open path: ../docs/" + "plans/p.md",
                "demos/README.md:6: link to no open path: missing.md",
            ],
            hygiene_problems(files),
        )

    def test_a_bracketed_destination_with_spaces_is_followed(self) -> None:
        closed = "../docs/" + "plans/private record.md"
        files = {
            "demos/README.md": f"[record](<{closed}>)\n[here](<test tables.md> \"title\")\n[ref]: <{closed}>\n",
            "demos/test tables.md": "",
        }
        self.assertEqual(
            [
                f"demos/README.md:1: link to no open path: {closed}",
                f"demos/README.md:3: link to no open path: {closed}",
            ],
            hygiene_problems(files),
        )

    def test_a_link_to_an_open_image_is_followed_through_the_open_paths(self) -> None:
        files = {"docs/guide/a.md": "![diagram](img/flow.png)\n"}
        self.assertEqual(
            ["docs/guide/a.md:1: link to no open path: img/flow.png"], hygiene_problems(files)
        )
        self.assertEqual([], hygiene_problems(files, frozenset(files) | {"docs/guide/img/flow.png"}))

    def test_a_closed_path_is_refused_in_a_user_facing_file(self) -> None:
        for closed in CLOSED:
            line = f"the record `{closed}x.md`\n"
            with self.subTest(closed=closed):
                self.assertEqual(
                    [f"docs/guide/a.md:1: closed path in a user-facing file: {closed}"],
                    hygiene_problems({"docs/guide/a.md": line}),
                )
                self.assertEqual([], hygiene_problems({"README.md": "fine\n", "docs/briefs/FB.md": line}))

    def test_vendored_paths(self) -> None:
        self.assertTrue(is_vendored("demos/requirements-exchange/sites/1.1-confirmed/_static/css/x.css"))
        self.assertTrue(is_vendored("demos/requirements-exchange-presentation.html"))
        self.assertFalse(is_vendored("demos/requirements-exchange/sites/1.0/index.html"))
        self.assertFalse(is_vendored("README.md"))


class TestThisRepository(unittest.TestCase):
    def test_the_allow_list_partitions_the_tracked_files(self) -> None:
        entries = parse_entries(ALLOW_LIST.read_text(encoding="utf-8"))
        problems = partition_problems(entries, tracked_files(PROJECT_ROOT))
        self.assertEqual([], problems, "\n".join(problems))

    def test_the_allow_list_is_decision_2s(self) -> None:
        entries = parse_entries(ALLOW_LIST.read_text(encoding="utf-8"))
        self.assertEqual(
            [
                ".github/", ".kiro/", ".moon/", ".vscode/", "demos/", "docs/briefs/", "docs/guide/",
                "experiments/", "kit/", "model/", "scripts/", "tests/",
                ".gitattributes", ".gitignore", ".prototools", "LICENSE", "NOTICE", "README.md",
                "THIRD-PARTY-NOTICES.md", "moon.yml", "public-paths.txt", "swcraft.yaml",
            ],
            entries,
        )

    def test_license_is_the_apache_2_0_text(self) -> None:
        digest = hashlib.sha256((PROJECT_ROOT / "LICENSE").read_bytes()).hexdigest()
        self.assertEqual(APACHE_SHA256, digest)

    def test_notice_is_exactly_its_four_lines(self) -> None:
        text = (PROJECT_ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertEqual("\n".join(NOTICE_LINES) + "\n", text)

    def test_third_party_notices_name_each_vendored_component_with_its_text(self) -> None:
        text = (PROJECT_ROOT / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8")
        for name in VENDORED:
            with self.subTest(component=name):
                self.assertIn(f"\n| {name} ", text)
                self.assertIn(f"\n### {name} ", text)
        for licence in ("BSD-2-Clause", "BSD-3-Clause", "MIT"):
            self.assertIn(licence, text)
        self.assertEqual([], licence_text_problems(text))

    def test_an_emptied_or_altered_licence_text_is_refused(self) -> None:
        text = (PROJECT_ROOT / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8")
        start = text.index("```text\n", text.index("\n### Sphinx ")) + len("```text\n")
        end = text.index("\n```\n", start) + 1
        self.assertEqual(
            ["the licence text under '### Sphinx 9.0.4' is not the one distributed"],
            licence_text_problems(text[:start] + text[end:]),
        )
        altered = text.replace("two clause BSD licence", "MIT licence", 1)
        self.assertEqual(
            ["the licence text under '### Sphinx 9.0.4' is not the one distributed"], licence_text_problems(altered)
        )
        dropped = text.replace("### Sphinx 9.0.4\n", "### Sphinx\n", 1)
        self.assertEqual(
            ["no licence text under '### Sphinx 9.0.4'", "a licence text no digest holds: '### Sphinx'"],
            licence_text_problems(dropped),
        )

    def test_third_party_notices_name_every_static_file_of_the_sites(self) -> None:
        """Each file directly in a site's ``_static/`` is named, and each folder there as ``<name>/``."""
        text = (PROJECT_ROOT / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8")
        statics = sorted(SITES.glob("*/_static"))
        self.assertEqual(4, len(statics))
        for static in statics:
            for path in sorted(static.iterdir()):
                if path.name.startswith("."):
                    continue
                name = f"`{path.name}/`" if path.is_dir() else f"`{path.name}`"
                with self.subTest(path=path.relative_to(PROJECT_ROOT).as_posix()):
                    self.assertIn(name, text)

    def test_the_open_files_pass_the_hygiene_scan(self) -> None:
        texts = open_texts(PROJECT_ROOT)
        self.assertIn("README.md", texts)
        self.assertIn("tests/test_open_copy.py", texts)
        problems = hygiene_problems(texts, frozenset(open_paths(PROJECT_ROOT)))
        self.assertEqual([], problems, "\n".join(problems))

    def test_each_upstream_address_stands_in_the_notices(self) -> None:
        text = (PROJECT_ROOT / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8")
        for address in sorted(UPSTREAM_ADDRESSES):
            with self.subTest(address=address):
                self.assertIn(address, text)


if __name__ == "__main__":
    unittest.main()
