"""The requirements exchange presentation: its public copy is current and holds no speaker note.

``demos/requirements-exchange-presentation.md`` is the source deck, speaker notes as HTML comments;
``demos/build_public.py`` renders the presenter's HTML and the public Markdown and HTML from it. The
kit ships the public HTML only. These tests need no ``marp``: they rebuild the public Markdown with
the builder's own functions and compare it with the committed file, read both committed HTML
files as text -- every prose line of the public Markdown (headings, list items, table cells and
paragraphs, their inline marks dropped) must be in the public HTML's text, so the shipped HTML is
the rendering of the current Markdown -- and hold the builder's audience marks on a fixture deck.

What this does not reach: the HTML's layout and the code blocks' contents (Marp's highlighting
splits them into spans), and whether ``marp`` was the version that rendered the committed copies.
"""

from __future__ import annotations

import contextlib
import html
import io
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import swcraft_on_path as gate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMOS = PROJECT_ROOT / "demos"
SOURCE = DEMOS / "requirements-exchange-presentation.md"
PUBLIC_MD = DEMOS / "requirements-exchange-presentation-public.md"
PUBLIC_HTML = DEMOS / "requirements-exchange-presentation-public.html"
MAIN_HTML = DEMOS / "requirements-exchange-presentation.html"
AUTHOR = "Konstantin Tarandevich"

BUILD = gate.load_script("build_public", DEMOS)

#: A note's markers, as the source writes them; none may reach the public copy.
NOTE_MARKERS = ("Talk track", "Purpose:", "Audience:", "Transition:", "[Sources")
#: Neither copy names a phase number, a local path or an e-mail address.
FORBIDDEN = (
    re.compile(r"\bPhase[\s#]*\d", re.IGNORECASE),
    re.compile(r"/Users/|/home/|[A-Za-z]:\\\\|~/"),
    re.compile(r"[\w.+-]+@[A-Za-z][\w-]*\.[A-Za-z]{2,}"),
)
#: Nor a dotted requirement id, checked in the Markdown: Marp's HTML carries SVG path data
#: (``M7.775``) that reads like one.
DOTTED_ID = re.compile(r"\b[A-Z][A-Z0-9_-]*\d(?:\.\d+)+\b")


#: HTML elements that end a run of text; any other tag is inline and joins its neighbours.
BLOCK_TAG_RE = re.compile(r"</?(?:li|p|h[1-6]|td|th|tr|br|section|pre|div|ul|ol|table|thead|tbody|blockquote)\b[^>]*>")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def html_text(page: str) -> str:
    """A rendered deck's text: no script or style, block tags a space, inline tags dropped, entities read."""
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S)
    page = re.sub(r"<[^>]+>", "", BLOCK_TAG_RE.sub(" ", page))
    return " ".join(html.unescape(page).split())


def prose_lines(markdown: str) -> list[str]:
    """Each heading, list item, table cell and paragraph line of a deck, its inline marks dropped.

    The front matter, style blocks, inline SVG drawings, comments and fenced code are left out.
    """
    body = markdown.split("\n---\n", 1)[1]
    body = re.sub(r"^```.*?^```", "", body, flags=re.M | re.S)
    body = re.sub(r"<style\b.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<svg\b.*?</svg>", "", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    lines = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line == "---" or re.fullmatch(r"\|?[\s:|-]+\|?", line):
            continue
        for cell in line.strip("|").split("|") if line.startswith("|") else [line]:
            cell = re.sub(r"^(#+|[-*]|\d+\.)\s+", "", cell.strip())
            cell = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell)
            cell = re.sub(r"\*\*|__|`|(?<!\w)_|_(?!\w)|(?<!\*)\*(?!\*)", "", cell)
            cell = " ".join(cell.split())
            if cell:
                lines.append(cell)
    return lines


class TestPublicCopy(unittest.TestCase):
    def test_public_markdown_is_the_source_without_notes(self) -> None:
        text, _ = BUILD.drop_audience(read(SOURCE), "presenter")
        text, removed = BUILD.strip_notes(text)
        self.assertGreater(removed, 0)
        self.assertEqual(text, read(PUBLIC_MD), "run: python demos/build_public.py")

    def test_public_copies_hold_no_speaker_note(self) -> None:
        for path in (PUBLIC_MD, PUBLIC_HTML):
            text = read(path)
            for marker in NOTE_MARKERS:
                self.assertNotIn(marker, text, f"{path.name}: {marker!r}")
        for body in re.findall(r"<!--(.*?)-->", read(PUBLIC_MD), flags=re.S):
            self.assertTrue(BUILD.is_directive(body), f"only Marp directives stay: {body.strip()!r}")

    def test_the_public_html_renders_the_public_markdown(self) -> None:
        """The HTML the kit ships says what the current public Markdown says, line by line."""
        lines = prose_lines(read(PUBLIC_MD))
        self.assertGreater(len(lines), 40)
        text = html_text(read(PUBLIC_HTML))
        for line in lines:
            with self.subTest(line=line):
                self.assertIn(line, text)

    def test_presenter_copy_keeps_the_notes(self) -> None:
        self.assertIn("Talk track", read(MAIN_HTML))

    def test_both_html_copies_carry_every_slide_title(self) -> None:
        prose = re.sub(r"^```.*?^```", "", read(SOURCE), flags=re.M | re.S)
        titles = re.findall(r"^# (.+)$", prose, flags=re.M)
        self.assertEqual(10, len(titles))
        for path in (MAIN_HTML, PUBLIC_HTML):
            text = read(path)
            for title in titles:
                self.assertIn(title.split(":")[0].split(" —")[0], text, f"{path.name}: {title}")


class TestAudienceMarks(unittest.TestCase):
    """``drop_audience`` on a fixture deck: a marked slide leaves the other audience's copy."""

    DECK = (
        "---\nmarp: true\n---\n\n# Title\n"
        "\n---\n<!-- audience: presenter -->\n# For the presenter\n"
        "\n---\n<!-- audience: public -->\n# For the public\n"
        "\n---\n# For both\n"
    )

    def test_the_public_copy_drops_the_presenters_slide_and_the_mark(self) -> None:
        text, dropped = BUILD.drop_audience(self.DECK, "presenter")
        self.assertEqual(1, dropped)
        self.assertNotIn("For the presenter", text)
        self.assertIn("# For the public", text)
        self.assertIn("# For both", text)
        self.assertNotIn("audience:", text)
        self.assertTrue(text.startswith("---\nmarp: true\n---\n"))

    def test_the_presenters_copy_drops_the_public_slide(self) -> None:
        text, dropped = BUILD.drop_audience(self.DECK, "public")
        self.assertEqual(1, dropped)
        self.assertNotIn("For the public", text)
        self.assertIn("# For the presenter", text)
        self.assertNotIn("audience:", text)

    def test_a_deck_without_marks_is_unchanged(self) -> None:
        deck = "---\nmarp: true\n---\n\n# Title\n\n---\n# Only\n"
        self.assertEqual((deck, 0), BUILD.drop_audience(deck, "presenter"))

    def test_a_dash_line_in_a_code_block_does_not_split_a_presenters_slide(self) -> None:
        for fence in ("```", "~~~", "````"):
            with self.subTest(fence=fence):
                deck = (
                    "---\nmarp: true\n---\n\n# Title\n"
                    f"\n---\n<!-- audience: presenter -->\n# For the presenter\n\n{fence}yaml\n"
                    f"name: first\n---\nname: second\n{fence}\n\nPresenter only after the block\n"
                    "\n---\n# For both\n"
                )
                text, dropped = BUILD.drop_audience(deck, "presenter")
                self.assertEqual(1, dropped)
                for leaked in ("For the presenter", "name: second", "Presenter only after"):
                    self.assertNotIn(leaked, text)
                self.assertEqual("---\nmarp: true\n---\n\n# Title\n\n---\n# For both\n", text)

    def test_a_dash_line_in_a_note_does_not_split_a_presenters_slide(self) -> None:
        deck = (
            "---\nmarp: true\n---\n\n# Title\n"
            "\n---\n<!-- audience: presenter -->\n# For the presenter\n\n<!--\nfirst part\n---\n"
            "second part\n-->\n\nPresenter only after the note\n"
            "\n---\n# For both\n"
        )
        text, dropped = BUILD.drop_audience(deck, "presenter")
        self.assertEqual((1, "---\nmarp: true\n---\n\n# Title\n\n---\n# For both\n"), (dropped, text))

    def test_the_slides_join_back_to_the_deck(self) -> None:
        for deck in (read(SOURCE), self.DECK, "---\nmarp: true\n---\n\n```\n---\n```\n\n---\n# B\n"):
            with self.subTest(deck=deck[:20]):
                self.assertEqual(deck, BUILD.join_slides(BUILD.split_slides(deck)))
        self.assertEqual(5, len(BUILD.split_slides(self.DECK + "\n```\n---\n```\n")))

    def test_another_horizontal_rule_is_reported_and_one_in_a_code_block_is_not(self) -> None:
        self.assertEqual([], BUILD.other_rules(read(SOURCE)))
        self.assertEqual(
            ["***", "___", "- - -"],
            BUILD.other_rules("# A\n\n***\n\n# B\n\n___\n\n- - -\n\n```\n***\n```\n"),
        )


class TestScanner(unittest.TestCase):
    """The one line scanner every function reads the deck through, table by table."""

    HEAD = "---\nmarp: true\n---\n\n# Title\n"
    TAIL = "\n---\n# For both\n"
    PUBLIC = HEAD + TAIL

    def presenter_slide(self, body: str) -> str:
        return (
            f"{self.HEAD}\n---\n<!-- audience: presenter -->\n# For the presenter\n\n{body}\n\n"
            f"Presenter only after\n{self.TAIL}"
        )

    def test_fence_indentation(self) -> None:
        # (opening line, closing line, whether the closing line closes the block)
        for opening, closing, closes in (
            ("```", "```", True),
            ("   ```", "```", True),
            ("```", "   ```", True),
            ("  ~~~", " ~~~~", True),
            ("```", "```  ", True),
            ("```", "    ```", False),
            ("```", "~~~", False),
            ("````", "```", False),
            ("```", "``` x", False),
        ):
            with self.subTest(opening=opening, closing=closing):
                lines = BUILD.scan(f"{opening}\n{closing}\nafter")
                self.assertEqual([True, True, not closes], [line.in_fence for line in lines])

    def test_a_four_space_line_opens_no_fence(self) -> None:
        lines = BUILD.scan("    ```\n---\n    ```")
        self.assertEqual([False, False, False], [line.in_fence for line in lines])
        self.assertEqual(2, len(BUILD.split_slides("# A\n    ```\n---\n    ```")))

    def test_breaks_in_a_fence_or_a_note_neither_split_nor_leak(self) -> None:
        for rule in ("---", "***", "___", "- - -", " ---", "-----"):
            for body in (
                f"```\nname: first\n{rule}\nname: second\n```",
                f"   ```yaml\nname: first\n{rule}\n    ```\nname: second\n   ```",
                f"~~~\nname: first\n{rule}\nname: second\n~~~",
                f"<!--\nname: first\n{rule}\nname: second\n-->",
            ):
                with self.subTest(rule=rule, body=body):
                    deck = self.presenter_slide(body)
                    self.assertEqual([], BUILD.other_rules(deck))
                    self.assertEqual((self.PUBLIC, 1), BUILD.drop_audience(deck, "presenter"))

    def test_other_breaks_outside_are_reported(self) -> None:
        for rule in ("***", "___", "- - -", " ---", "---  ", "-----", "* * *", "   ___"):
            with self.subTest(rule=rule):
                self.assertEqual([rule], BUILD.other_rules(f"# A\n\n{rule}\n\n# B\n"))
        for line in ("    ***", "--", "--- x", "---"):
            with self.subTest(line=line):
                self.assertEqual([], BUILD.other_rules(f"# A\n\n{line}\n\n# B\n"))

    def test_an_audience_marker_counts_only_as_a_line_of_its_own_outside_fences_and_notes(self) -> None:
        for body, dropped in (
            ("<!-- audience: presenter -->", 1),
            ("  <!--audience:presenter-->  ", 1),
            ("```markdown\n<!-- audience: presenter -->\n```", 0),
            ("   ~~~\n<!-- audience: presenter -->\n~~~", 0),
            ("<!--\n<!-- audience: presenter -->", 0),
            ("Mark it with <!-- audience: presenter --> on a line", 0),
        ):
            with self.subTest(body=body):
                deck = f"{self.HEAD}\n---\n# A public slide\n\n{body}\n{self.TAIL}"
                text, count = BUILD.drop_audience(deck, "presenter")
                self.assertEqual(dropped, count)
                if not dropped:
                    self.assertEqual(deck, text)

    def test_a_marker_in_a_fence_is_kept_by_the_public_copy(self) -> None:
        deck = f"{self.HEAD}\n---\n# Marking a slide\n\n```markdown\n<!-- audience: presenter -->\n```\n{self.TAIL}"
        self.assertEqual((deck, 0), BUILD.drop_audience(deck, "presenter"))
        self.assertEqual((deck, 0), BUILD.strip_notes(deck))

    def test_a_speaker_note_holding_another_break_is_accepted_and_removed(self) -> None:
        for rule in ("***", "___", "- - -"):
            with self.subTest(rule=rule):
                deck = f"{self.HEAD}\n---\n# A slide\n\n<!--\nTalk track: first\n{rule}\nthen\n-->\n{self.TAIL}"
                self.assertEqual([], BUILD.other_rules(deck))
                self.assertEqual((f"{self.HEAD}\n---\n# A slide\n{self.TAIL}", 1), BUILD.strip_notes(deck))

    def test_strip_notes_leaves_code_blocks_whole(self) -> None:
        text = "# A\n\n```\n<!-- an example -->\n\n\n\nend\n```\n\n<!-- note -->\n\n\nafter\n"
        self.assertEqual(
            ("# A\n\n```\n<!-- an example -->\n\n\n\nend\n```\n\nafter\n", 1), BUILD.strip_notes(text)
        )

    def test_the_real_deck_is_unchanged(self) -> None:
        source = read(SOURCE)
        self.assertEqual([], BUILD.other_rules(source))
        self.assertEqual((source, 0), BUILD.drop_audience(source, "public"))
        self.assertEqual((source, 0), BUILD.drop_audience(source, "presenter"))
        self.assertEqual(read(PUBLIC_MD), BUILD.strip_notes(source)[0])


class TestNotesAndDirectives(unittest.TestCase):
    """``strip_notes`` on fixture comments: only a one-line comment naming a Marp directive stays."""

    def test_marp_directives_stay(self) -> None:
        for comment in (
            "<!-- _class: compact -->",
            "<!-- class: lead -->",
            "<!-- paginate: false -->",
            "<!-- _backgroundColor: #fff -->",
            "<!--footer: Vehicle Control-->",
            "<!-- transition: fade -->",
        ):
            with self.subTest(comment=comment):
                text = f"# Slide\n\n{comment}\n"
                self.assertEqual((text, 0), BUILD.strip_notes(text))

    def test_a_one_line_key_value_note_is_removed(self) -> None:
        for comment in (
            "<!-- Transition: now the second enrichment -->",
            "<!-- Purpose: the close -->",
            "<!-- Note: ask the room -->",
            "<!-- _Class: compact -->",
            "<!-- todo: add a figure -->",
        ):
            with self.subTest(comment=comment):
                text, removed = BUILD.strip_notes(f"# Slide\n\n{comment}\n")
                self.assertEqual(("# Slide\n\n", 1), (text, removed))

    def test_a_multi_line_comment_is_removed_even_if_it_starts_like_a_directive(self) -> None:
        text, removed = BUILD.strip_notes("# Slide\n\n<!-- class: lead\nTalk track: say it -->\n")
        self.assertEqual(("# Slide\n\n", 1), (text, removed))

    def test_the_builders_markers_cover_the_tests(self) -> None:
        self.assertLessEqual(set(NOTE_MARKERS), set(BUILD.NOTE_MARKERS))


class TestStructuralLeakCheck(unittest.TestCase):
    """``main`` refuses, before writing anything, a deck that could leak a note whatever its text.

    ``marp`` is replaced by a stub that copies the Markdown, and every path points into a temporary
    directory, so the committed copies are never touched.
    """

    HEAD = "---\nmarp: true\n---\n\n# Title\n"

    def build(self, deck: str | None) -> tuple[int, Path, str]:
        """Run ``main`` on *deck* (the real source when ``None``); its code, output dir and stderr."""
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out)
        source = SOURCE if deck is None else out / "deck.md"
        if deck is not None:
            source.write_text(deck, encoding="utf-8", newline="\n")

        def render(md: Path, html_path: Path) -> None:
            html_path.write_text(md.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

        names = {
            "SOURCE": source,
            "PUBLIC_MD": out / "public.md",
            "PUBLIC_HTML": out / "public.html",
            "MAIN_HTML": out / "main.html",
            "MAIN_MD": out / "main.md",
        }
        err = io.StringIO()
        with contextlib.ExitStack() as stack:
            for name, value in names.items():
                stack.enter_context(mock.patch.object(BUILD, name, value))
            stack.enter_context(mock.patch.object(BUILD, "render", render))
            stack.enter_context(contextlib.redirect_stderr(err))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            code = BUILD.main()
        return code, out, err.getvalue()

    def assert_refused(self, deck: str, reason: str) -> None:
        code, out, err = self.build(deck)
        self.assertEqual(1, code)
        self.assertIn(reason, err)
        self.assertIn("nothing written", err)
        self.assertEqual(["deck.md"], sorted(path.name for path in out.iterdir()))

    def test_an_unterminated_comment_is_refused_and_nothing_written(self) -> None:
        deck = f"{self.HEAD}\n---\n# A slide\n\n<!-- private presenter note\nsay this\n"
        self.assertIsNotNone(BUILD.unterminated(deck))
        self.assert_refused(deck, "an HTML comment")

    def test_an_unclosed_fence_is_refused_and_nothing_written(self) -> None:
        deck = f"{self.HEAD}\n---\n# A slide\n\n```yaml\nname: first\n\n<!-- a note -->\n"
        self.assertIsNotNone(BUILD.unterminated(deck))
        self.assert_refused(deck, "a fenced code block")

    def test_any_comment_surviving_into_the_public_text_is_refused_whatever_its_text(self) -> None:
        # A comment that reaches the public text, carrying no note marker: the check reads the
        # structure, not the words. ``strip_notes`` removes every closed one today, so ``main`` is
        # driven below with it disabled -- the check is the net under it.
        for comment in ("<!-- private presenter note -->", "<!-- ask the room -->"):
            with self.subTest(comment=comment):
                text = f"# Slide\n\n```\nexample\n```\n\n{comment}\n\n<!-- _class: lead -->\n"
                self.assertEqual([comment], BUILD.stray_comments(text))
        self.assertEqual([], BUILD.stray_comments("```\n<!-- shown -->\n```\n<!-- class: lead -->\n"))
        with mock.patch.object(BUILD, "strip_notes", lambda text: (text, 0)):
            deck = f"{self.HEAD}\n---\n# A slide\n\n<!-- ask the room -->\n"
            self.assert_refused(deck, "no Marp directive")

    def test_a_marker_in_the_rendered_html_removes_both_public_copies(self) -> None:
        deck = f"{self.HEAD}\n---\n# A slide\n\n```markdown\nTalk track: shown as an example\n```\n"
        code, out, err = self.build(deck)
        self.assertEqual(1, code)
        self.assertIn("both public copies removed", err)
        self.assertEqual(["deck.md", "main.html"], sorted(path.name for path in out.iterdir()))

    def test_the_real_deck_still_builds_identically(self) -> None:
        self.assertIsNone(BUILD.unterminated(read(SOURCE)))
        code, out, err = self.build(None)
        self.assertEqual((0, ""), (code, err))
        self.assertEqual(read(PUBLIC_MD), read(out / "public.md"))
        self.assertEqual(
            ["main.html", "public.html", "public.md"], sorted(path.name for path in out.iterdir())
        )
        self.assertIn("Talk track", read(out / "main.html"))


class TestWording(unittest.TestCase):
    def test_no_phase_number_local_path_address_or_dotted_id(self) -> None:
        for path in (SOURCE, PUBLIC_MD, MAIN_HTML, PUBLIC_HTML):
            text = read(path)
            for pattern in FORBIDDEN:
                self.assertIsNone(pattern.search(text), f"{path.name}: {pattern.pattern}")
        for path in (SOURCE, PUBLIC_MD):
            self.assertIsNone(DOTTED_ID.search(read(path)), path.name)

    def test_the_only_name_is_the_author_on_the_title_slide(self) -> None:
        source = read(SOURCE)
        lines = [line for line in source.splitlines() if AUTHOR in line]
        self.assertEqual([f'author: "{AUTHOR}"', f"{AUTHOR} · November 2026"], lines)
        self.assertEqual(2, read(PUBLIC_MD).count(AUTHOR))


if __name__ == "__main__":
    unittest.main()
