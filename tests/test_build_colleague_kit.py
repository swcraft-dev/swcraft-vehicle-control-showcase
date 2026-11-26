"""Stdlib tests for the colleague-kit builder."""

from __future__ import annotations

import difflib
import hashlib
import io
import json
import posixpath
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "build_colleague_kit.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate

KIT = gate.load_script("build_colleague_kit")

#: What must never reach a colleague: the moon build graph, git, the generated
#: outputs, the evidence and the licensed schema -- and the files earlier
#: releases retired (0.7.0's bootstrap, the Python preflight and its two
#: launchers, 0.22.0's trace decisions file, Codex's hook the showcase dropped
#: on 0.23.0), should one ever come back.
NEVER_IN_KIT = (
    ".venv/bin/python",
    "bootstrap.py",
    "requirements-swcraft.txt",
    "clean_outputs.py",
    "setup-showcase",
    "setup-showcase.ps1",
    "scripts/setup_showcase.py",
    "moon.yml",
    ".moon/workspace.yml",
    ".prototools",
    ".git/HEAD",
    ".env",
    "schemas/AUTOSAR_4-3-0.xsd",
    "dist/model.arxml",
    "views/index.html",
    ".vscode/mcp.json",
    ".vscode/mcp.json.example",
    ".codex/hooks.json",
    "docs/evidence/run.md",
    "tests/test_x.py",
    "tests/test_rejected_changes.py",
    "demos/notes.txt",
    "scripts/generate_requirements_deliveries.py",
    "scripts/generate_requirements_prepared.py",
    "scripts/generate_test_annotations.py",
    "scripts/pinned_swcraft.py",
    "scripts/repository_rules.py",
    "tests/test_test_tables.py",
    "demos/test-tables/annotations/notes.txt",
    "demos/requirements-exchange/sites/1.0/.DS_Store",
    "demos/requirements-exchange/sites/2.0/index.html",
    "tests/test_requirements_deliveries.py",
    "demos/requirements-exchange/team/swcraft/needs.json",
    "demos/requirements-exchange-presentation.md",
    "demos/requirements-exchange-presentation.html",
    "demos/requirements-exchange-presentation-public.md",
    "demos/build_public.py",
    "experiments/rebalance.yaml",
    "trace-decisions.yaml",
    "demos/.DS_Store",
    "model/.DS_Store",
)

MANIFEST = """\
# Project manifest. A comment about clean_outputs.py that the kit must drop.
name: synthetic
schema_version: "1.0"
arxml_version: "4.3.0"
model_root: model
dist_root: dist
views_root: views
outputs:
  arxml: dist/model.arxml
  needs: dist/needs.json
"""


def make_project(root: Path) -> None:
    """A synthetic showcase checkout: the kit's inputs plus everything it must skip."""
    files = {
        "swcraft.yaml": MANIFEST,
        ".vscode/settings.json": '{"xml.validation.filters": []}\n',
        ".gitattributes": "* text=auto eol=lf\n",
        "model/hardware/CPU.yaml": "name: CPU\nkind: processor\n",
        "model/swc/application/A.yaml": "name: A\n",
        "model/connectors/.gitkeep": "",
        ".github/agents/swcraft-architect.agent.md": "---\nname: SWCraft Architect\n---\n",
        ".github/hooks/swcraft.json": "{}\n",
        ".kiro/settings/mcp.json": "{}\n",
        ".kiro/steering/swcraft.md": "# steering\n",
        ".kiro/hooks/swcraft-guard.json": "{}\n",
        ".github/copilot-instructions.md": "# repository instructions: moon run :build\n",
        "kit/overlay/.github/copilot-instructions.md": "# kit instructions\n",
        "kit/overlay/.gitignore": "dist/\n",
        "docs/guide/install-on-a-workstation.md": "# Install\n",
        "demos/README.md": "# Rejected changes\n",
        "demos/chat-with-the-model.md": "# Chat with the model\n",
        "demos/rejected-changes.json": "[]\n",
        "demos/requirements-exchange.md": "# The requirements exchange\n",
        "demos/requirements-exchange-presentation-public.html": "<section>public</section>\n",
        "demos/requirements-exchange/team.needs-mapping.yaml": "types: {}\n",
        "demos/requirements-exchange/answer-key.json": "{}\n",
        "demos/requirements-exchange/prepared-links.json": "{}\n",
        "demos/requirements-exchange/sites/1.0.needs.json": "{}\n",
        "demos/requirements-exchange/sites/1.1-unconfirmed.needs.json": "{}\n",
        "demos/requirements-exchange/sites/1.1-confirmed.needs.json": "{}\n",
        "demos/requirements-exchange/sites/1.0-original/index.html": "<p>1.0 original</p>\n",
        "demos/requirements-exchange/sites/1.0/index.html": "<p>1.0</p>\n",
        "demos/requirements-exchange/sites/1.0/_static/basic.css": "p {}\n",
        "demos/requirements-exchange/sites/1.1-unconfirmed/index.html": "<p>1.1</p>\n",
        "demos/requirements-exchange/sites/1.1-confirmed/index.html": "<p>1.1</p>\n",
        "demos/requirements-exchange/deliveries/1.0/needs.json": "{}\n",
        "demos/requirements-exchange/deliveries/1.1/needs.json": "{}\n",
        "demos/requirements-exchange/team/conf.py": "project = 'x'\n",
        "demos/requirements-exchange/team/requirements.txt": "sphinx-needs==9.2.0\n",
        "demos/requirements-exchange/team/delivery-1.0/index.rst": "Delivery 1.0\n",
        "demos/requirements-exchange/team/delivery-1.1/index.rst": "Delivery 1.1\n",
        "demos/test-tables.md": "# Test tables\n",
        "demos/test-tables/annotations/components.csv": '"row_id"\n',
        "demos/test-tables/annotations/component-placement.csv": '"row_id"\n',
        "demos/test-tables/annotations/runnable-scheduling.csv": '"row_id"\n',
        "experiments/trace.yaml": "name: trace\n",
        "LICENSE": "Apache License\n",
        "NOTICE": "SWCraft Vehicle Control Showcase\n",
        "THIRD-PARTY-NOTICES.md": "# Third-party notices\n",
    }
    for relative in NEVER_IN_KIT:
        files[relative] = "must not ship\n"
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def build(root: Path, version: str = "0.22.0", **kwargs: object) -> dict[str, bytes]:
    return KIT.build_members(
        root,
        root / "kit" / "overlay",
        root / "docs" / "guide" / "install-on-a-workstation.md",
        version,
        **kwargs,
    )


class TestMembers(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_project(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_kit_carries_exactly_the_allowlist(self) -> None:
        members = build(self.root)
        self.assertEqual(b"# kit instructions\n", members[".github/copilot-instructions.md"])
        self.assertEqual(
            {
                "swcraft.yaml",
                ".vscode/settings.json",
                ".gitattributes",
                "model/hardware/CPU.yaml",
                "model/swc/application/A.yaml",
                "model/connectors/.gitkeep",
                ".github/copilot-instructions.md",
                ".github/agents/swcraft-architect.agent.md",
                ".github/hooks/swcraft.json",
                ".kiro/settings/mcp.json",
                ".kiro/steering/swcraft.md",
                ".kiro/hooks/swcraft-guard.json",
                ".gitignore",
                "README.md",
                "demos/README.md",
                "demos/chat-with-the-model.md",
                "demos/rejected-changes.json",
                "demos/requirements-exchange.md",
                "demos/requirements-exchange-presentation-public.html",
                "demos/requirements-exchange/team.needs-mapping.yaml",
                "demos/requirements-exchange/answer-key.json",
                "demos/requirements-exchange/prepared-links.json",
                "demos/requirements-exchange/sites/1.0.needs.json",
                "demos/requirements-exchange/sites/1.1-unconfirmed.needs.json",
                "demos/requirements-exchange/sites/1.1-confirmed.needs.json",
                "demos/requirements-exchange/sites/1.0-original/index.html",
                "demos/requirements-exchange/sites/1.0/index.html",
                "demos/requirements-exchange/sites/1.0/_static/basic.css",
                "demos/requirements-exchange/sites/1.1-unconfirmed/index.html",
                "demos/requirements-exchange/sites/1.1-confirmed/index.html",
                "demos/requirements-exchange/deliveries/1.0/needs.json",
                "demos/requirements-exchange/deliveries/1.1/needs.json",
                "demos/requirements-exchange/team/conf.py",
                "demos/requirements-exchange/team/requirements.txt",
                "demos/requirements-exchange/team/delivery-1.0/index.rst",
                "demos/requirements-exchange/team/delivery-1.1/index.rst",
                "demos/test-tables.md",
                "demos/test-tables/annotations/components.csv",
                "demos/test-tables/annotations/component-placement.csv",
                "demos/test-tables/annotations/runnable-scheduling.csv",
                "experiments/trace.yaml",
                "LICENSE",
                "NOTICE",
                "THIRD-PARTY-NOTICES.md",
                "kit-manifest.json",
            },
            set(members),
        )
        for relative in NEVER_IN_KIT:
            self.assertNotIn(relative, members)

    def test_kit_carries_the_demo_files_verbatim(self) -> None:
        members = build(self.root)
        self.assertEqual(b"# Rejected changes\n", members["demos/README.md"])
        self.assertEqual(b"[]\n", members["demos/rejected-changes.json"])
        self.assertEqual(b"# The requirements exchange\n", members["demos/requirements-exchange.md"])
        self.assertEqual(
            b"<section>public</section>\n", members["demos/requirements-exchange-presentation-public.html"]
        )

    def test_manifest_is_pinned_once_and_loses_the_build_graph_comment(self) -> None:
        text = build(self.root)["swcraft.yaml"].decode("utf-8")
        self.assertEqual(1, text.count("toolchain_version:"))
        self.assertIn('schema_version: "1.0"\ntoolchain_version: "0.22.0"\n', text)
        self.assertNotIn("clean_outputs.py", text)
        self.assertTrue(text.startswith("# Project manifest of the Vehicle Control Showcase"))
        self.assertIn("name: synthetic\n", text)
        self.assertIn("  needs: dist/needs.json\n", text)

    def test_an_existing_pin_is_replaced_not_duplicated(self) -> None:
        pinned = KIT.pin_manifest(MANIFEST.replace('schema_version: "1.0"\n', 'schema_version: "1.0"\ntoolchain_version: "0.7.0"\n'), "0.22.0")
        self.assertEqual(1, pinned.count("toolchain_version:"))
        self.assertIn('toolchain_version: "0.22.0"', pinned)
        self.assertNotIn("0.7.0", pinned)

    def test_readme_is_the_install_page(self) -> None:
        self.assertEqual(b"# Install\n", build(self.root)["README.md"])

    def test_kit_manifest_records_version_note_and_members(self) -> None:
        members = build(self.root)
        manifest = json.loads(members["kit-manifest.json"])
        self.assertEqual("0.22.0", manifest["swcraft_version"])
        self.assertEqual("swcraft-0.22.0-windows-x64.zip", manifest["swcraft_archive"])
        self.assertIn("tag was still pending", manifest["note"])
        self.assertEqual(sorted(members), sorted(manifest["members"]))
        self.assertEqual(KIT.model_digest(members), manifest["model_sha256"])
        tagged = json.loads(build(self.root, tagged=True)["kit-manifest.json"])
        self.assertNotIn("pending", tagged["note"])

    def test_model_digest_covers_only_the_model(self) -> None:
        members = build(self.root)
        before = KIT.model_digest(members)
        members["README.md"] = b"changed"
        self.assertEqual(before, KIT.model_digest(members))
        members["model/swc/application/A.yaml"] = b"name: B\n"
        self.assertNotEqual(before, KIT.model_digest(members))


class TestRefusals(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_project(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_version_must_be_one_exact_release(self) -> None:
        for bad in ("0.8", ">=0.8.0", "0.8.0rc1", "latest"):
            with self.assertRaisesRegex(KIT.KitError, "exact release"):
                build(self.root, bad)

    def test_missing_manifest_model_overlay_or_page_is_refused_by_name(self) -> None:
        (self.root / "swcraft.yaml").unlink()
        with self.assertRaisesRegex(KIT.KitError, "swcraft.yaml is missing"):
            build(self.root)
        (self.root / "swcraft.yaml").write_text(MANIFEST, encoding="utf-8", newline="\n")
        for path in (self.root / "model").rglob("*.yaml"):
            path.unlink()
        with self.assertRaisesRegex(KIT.KitError, "no element file"):
            build(self.root)

    def test_a_missing_legal_file_is_refused_by_name(self) -> None:
        for relative in KIT.LEGAL_FILES:
            with self.subTest(relative=relative):
                path = self.root / relative
                text = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaisesRegex(KIT.KitError, f"^{relative} is missing"):
                        build(self.root)
                finally:
                    path.write_bytes(text)

    def test_a_missing_demo_file_is_refused_by_name(self) -> None:
        for relative in KIT.DEMO_FILES:
            with self.subTest(relative=relative):
                path = self.root / relative
                text = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaisesRegex(KIT.KitError, f"{relative} is missing"):
                        build(self.root)
                finally:
                    path.write_bytes(text)

    def test_a_missing_or_empty_site_folder_is_refused_by_name(self) -> None:
        site = self.root / "demos" / "requirements-exchange" / "sites" / "1.1-confirmed" / "index.html"
        site.unlink()
        with self.assertRaisesRegex(KIT.KitError, "sites/1.1-confirmed/ is missing or empty"):
            build(self.root)
        for name in KIT.IGNORED_NAMES:
            (site.parent / name).write_text("litter\n", encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(KIT.KitError, "sites/1.1-confirmed/ is missing or empty"):
            build(self.root)
        for name in KIT.IGNORED_NAMES:
            (site.parent / name).unlink()
        site.parent.rmdir()
        with self.assertRaisesRegex(KIT.KitError, "sites/1.1-confirmed/ is missing or empty"):
            build(self.root)

    def test_a_site_file_no_reader_opens_is_refused_by_name(self) -> None:
        """Sphinx's bookkeeping, a dotfile or a dot folder under a site folder: refused, the path named."""
        site = self.root / "demos" / "requirements-exchange" / "sites" / "1.0"
        for relative in (*KIT.SITE_REFUSED_NAMES, ".hidden", ".doctrees/environment.pickle", "_static/.keep"):
            with self.subTest(relative=relative):
                path = site / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("left over\n", encoding="utf-8", newline="\n")
                try:
                    expected = re.escape(f"no part of a site: demos/requirements-exchange/sites/1.0/{relative};")
                    with self.assertRaisesRegex(KIT.KitError, expected):
                        build(self.root)
                finally:
                    path.unlink()

    def test_operating_system_litter_in_a_site_folder_is_skipped_not_refused(self) -> None:
        site = self.root / "demos" / "requirements-exchange" / "sites" / "1.0"
        for name in KIT.IGNORED_NAMES:
            (site / name).write_text("litter\n", encoding="utf-8", newline="\n")
        members = build(self.root)
        for name in KIT.IGNORED_NAMES:
            self.assertNotIn(f"demos/requirements-exchange/sites/1.0/{name}", members)

    def test_manifest_without_schema_version_is_refused(self) -> None:
        with self.assertRaisesRegex(KIT.KitError, "schema_version"):
            KIT.pin_manifest("name: x\n", "0.22.0")

    def test_overlay_may_not_shadow_a_project_file(self) -> None:
        shadow = self.root / "kit" / "overlay" / "swcraft.yaml"
        shadow.write_text("name: shadow\n", encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(KIT.KitError, "overlay would replace"):
            build(self.root)


class TestZip(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_project(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_two_builds_are_byte_identical_and_rooted_in_one_folder(self) -> None:
        first = KIT.zip_bytes(build(self.root))
        second = KIT.zip_bytes(build(self.root))
        self.assertEqual(first, second)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            names = archive.namelist()
            self.assertTrue(all(name.startswith("vehicle-control-showcase/") for name in names))
            self.assertEqual(sorted(names), names)
            self.assertTrue(all(info.date_time == KIT.ZIP_DATE_TIME for info in archive.infolist()))
            self.assertIn("vehicle-control-showcase/README.md", names)
            self.assertIn("vehicle-control-showcase/kit-manifest.json", names)

    def test_main_writes_the_zip_and_a_matching_sums_file(self) -> None:
        out = self.root / "out"
        code = KIT.main(["--project-root", str(self.root), "--output-dir", str(out)])
        self.assertEqual(0, code)
        target = out / KIT.kit_filename(KIT.DEFAULT_VERSION)
        self.assertTrue(target.is_file())
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        self.assertEqual(
            f"{digest}  {target.name}\n",
            (out / "SHA256SUMS").read_text(encoding="utf-8"),
        )

    def test_main_reads_the_install_page_from_docs_guide(self) -> None:
        # The fixture holds the page only at its one path, so ``main`` -- which, unlike
        # ``build()`` above, finds the page itself -- is held to that path.
        page = self.root / "docs" / "guide" / "install-on-a-workstation.md"
        page.write_text("# Install from the guide\n", encoding="utf-8", newline="\n")
        self.assertFalse((self.root / "docs" / "install-on-a-workstation.md").exists())
        out = self.root / "out"
        self.assertEqual(0, KIT.main(["--project-root", str(self.root), "--output-dir", str(out)]))
        with zipfile.ZipFile(out / KIT.kit_filename(KIT.DEFAULT_VERSION)) as archive:
            self.assertEqual(page.read_bytes(), archive.read("vehicle-control-showcase/README.md"))

    def test_main_reports_a_refusal_with_exit_2(self) -> None:
        (self.root / "swcraft.yaml").unlink()
        self.assertEqual(2, KIT.main(["--project-root", str(self.root), "--output-dir", str(self.root / "out")]))


class TestThisRepository(unittest.TestCase):
    """The real inputs: the overlay and the page the kit is built from."""

    def test_overlay_holds_the_kit_files_and_no_moon(self) -> None:
        overlay = KIT.collect_overlay(KIT.OVERLAY_DIR)
        self.assertEqual({".github/copilot-instructions.md", ".gitignore"}, set(overlay))
        instructions = overlay[".github/copilot-instructions.md"].decode("utf-8")
        self.assertNotIn("moon run", instructions)
        self.assertNotIn(".vscode/mcp.json", instructions)
        self.assertNotIn("bootstrap.py", instructions)
        self.assertIn("swcraft validate", instructions)
        self.assertIn("schemas/", overlay[".gitignore"].decode("utf-8"))
        # The kit carries the team's project, so it hides the team's copy of the architecture too.
        self.assertIn("demos/requirements-exchange/team/swcraft/", overlay[".gitignore"].decode("utf-8").splitlines())

    def test_kit_instructions_differ_from_the_repository_only_in_the_building_section(self) -> None:
        """One release, one wording: the overlay is the root copy minus the moon build."""
        root = (PROJECT_ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        kit = KIT.collect_overlay(KIT.OVERLAY_DIR)[".github/copilot-instructions.md"].decode("utf-8")
        self.assertIn("moon run :build", root)
        root_lines, kit_lines = root.splitlines(), kit.splitlines()
        changed = [line for line in difflib.ndiff(root_lines, kit_lines) if line[:1] in "+-"]
        self.assertTrue(changed, "the overlay copy has no reason to exist if it is identical")
        # The root's building paragraph (seven lines since 0.20.0, which names the build report a
        # failed check leaves) against the kit's seven: the one section, and no line elsewhere.
        self.assertLessEqual(len(changed), 14, "\n".join(changed))
        for retired in (".vscode/mcp.json", "bootstrap.py", ".venv", "resources/"):
            self.assertNotIn(retired, root)
            self.assertNotIn(retired, kit)

    def test_agent_profile_is_the_repository_root_copy(self) -> None:
        profile = (PROJECT_ROOT / ".github" / "agents" / "swcraft-architect.agent.md").read_text(encoding="utf-8")
        members = KIT.collect_project_files(PROJECT_ROOT)
        self.assertEqual(profile.encode("utf-8"), members[".github/agents/swcraft-architect.agent.md"])
        for retired in (".vscode/mcp.json", "bootstrap.py", ".venv"):
            self.assertNotIn(retired, profile)

    def test_model_guard_hook_is_the_repository_root_copy(self) -> None:
        hook = (PROJECT_ROOT / ".github" / "hooks" / "swcraft.json").read_bytes()
        members = KIT.collect_project_files(PROJECT_ROOT)
        self.assertEqual(hook, members[".github/hooks/swcraft.json"])
        self.assertIn(b'"command": "swcraft guard"', hook)

    def test_kiro_files_are_the_repository_root_copies(self) -> None:
        members = KIT.collect_project_files(PROJECT_ROOT)
        for relative in (".kiro/settings/mcp.json", ".kiro/steering/swcraft.md", ".kiro/hooks/swcraft-guard.json"):
            with self.subTest(relative=relative):
                self.assertEqual((PROJECT_ROOT / relative).read_bytes(), members[relative])
        self.assertIn(b'"command": "swcraft guard --host kiro"', members[".kiro/hooks/swcraft-guard.json"])

    def test_codex_hook_is_gone_from_the_repository_and_the_kit(self) -> None:
        """The showcase is set up for Copilot and Kiro; Codex's hook was deleted on 0.23.0."""
        self.assertFalse((PROJECT_ROOT / ".codex").exists())
        self.assertFalse(any(relative.startswith(".codex/") for relative in KIT.PROJECT_FILES))

    def test_the_kit_carries_the_three_legal_files_verbatim(self) -> None:
        """The kit ships the sites' and the presentation's third-party code, so it carries the licences with it."""
        members = KIT.collect_project_files(PROJECT_ROOT)
        for relative in KIT.LEGAL_FILES:
            with self.subTest(relative=relative):
                self.assertIn(relative, KIT.PROJECT_FILES)
                self.assertEqual((PROJECT_ROOT / relative).read_bytes(), members[relative])

    def test_demo_files_are_the_repository_copies(self) -> None:
        members = KIT.collect_project_files(PROJECT_ROOT)
        for relative in KIT.DEMO_FILES:
            with self.subTest(relative=relative):
                self.assertEqual((PROJECT_ROOT / relative).read_bytes(), members[relative])

    def test_every_link_of_the_kits_pages_resolves_inside_the_kit(self) -> None:
        """A Markdown link on a page the kit carries names a member or a folder of the kit.

        The install page is the kit's ``README.md`` and the demos link to each other, so a page added
        to the repository and left out of :data:`KIT.DEMO_FILES` dangles in the kit alone. An inline
        link (``](target)``) and a reference definition (``[label]: target``) are both read. Code
        spans and fenced blocks are not links; a link with a scheme (``https:``, ``vscode:``) or an
        in-page anchor leaves the kit and is not checked here. The sites' HTML is Sphinx's and not read.
        """
        members = build(PROJECT_ROOT, KIT.DEFAULT_VERSION)
        folders = {str(parent) for name in members for parent in PurePosixPath(name).parents if str(parent) != "."}
        fence = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
        code = re.compile(r"`[^`\n]*`")
        link = re.compile(r"\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
        definition = re.compile(r"^ {0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?", re.MULTILINE)
        pages = [name for name in members if name.endswith(".md")]
        self.assertIn("demos/chat-with-the-model.md", pages)
        for page in sorted(pages):
            text = code.sub("", fence.sub("", members[page].decode("utf-8")))
            for target in [*link.findall(text), *definition.findall(text)]:
                if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                path = target.split("#", 1)[0]
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(page), path)).rstrip("/")
                with self.subTest(page=page, target=target):
                    self.assertTrue(resolved in members or resolved in folders, f"{page} links {target}")

    def test_the_sites_ship_whole_and_nothing_else_of_their_folder(self) -> None:
        """Every file of the four ready-made sites, verbatim; under ``sites/`` only those and the needs files."""
        members = KIT.collect_project_files(PROJECT_ROOT)
        for relative in KIT.DEMO_TREES:
            files = [path for path in (PROJECT_ROOT / relative).rglob("*") if path.is_file() and path.name not in KIT.IGNORED_NAMES]
            with self.subTest(site=relative):
                self.assertIn(f"{relative}/index.html", members)
                for path in files:
                    name = path.relative_to(PROJECT_ROOT).as_posix()
                    self.assertEqual(path.read_bytes(), members[name], name)
        under_sites = {name for name in members if name.startswith("demos/requirements-exchange/sites/")}
        in_trees = {name for name in under_sites if name.startswith(tuple(f"{tree}/" for tree in KIT.DEMO_TREES))}
        self.assertEqual(under_sites - in_trees, {name for name in KIT.DEMO_FILES if name in under_sites})

    def test_gitattributes_is_the_repository_root_copy_and_forces_lf(self) -> None:
        """A kit turned into a repository must not fall back to Git for Windows' core.autocrlf."""
        attributes = (PROJECT_ROOT / ".gitattributes").read_bytes()
        members = KIT.collect_project_files(PROJECT_ROOT)
        self.assertEqual(attributes, members[".gitattributes"])
        self.assertIn("* text=auto eol=lf", attributes.decode("utf-8").splitlines())

    def test_default_version_is_the_repository_pin(self) -> None:
        manifest = (PROJECT_ROOT / "swcraft.yaml").read_text(encoding="utf-8")
        self.assertIn(f'\ntoolchain_version: "{KIT.DEFAULT_VERSION}"\n', manifest)

    def test_install_page_names_both_zips_at_the_default_version(self) -> None:
        page = KIT.INSTALL_PAGE.read_text(encoding="utf-8")
        version = KIT.DEFAULT_VERSION
        self.assertIn(f"swcraft-{version}-windows-x64.zip", page)
        self.assertIn(KIT.kit_filename(version), page)
        for token in (
            f"/swcraft/releases/tag/v{version}",
            "/swcraft-vehicle-control-showcase/releases",
            "SHA256SUMS-windows-x64",
        ):
            self.assertIn(token, page)
        for internal in ("Phase", "Gitea", "moon run", "bootstrap.py", "requirements-swcraft"):
            self.assertNotIn(internal, page)

    def test_source_never_requests_a_shell(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("shell=True", source)


if __name__ == "__main__":
    unittest.main()
