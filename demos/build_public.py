"""Rebuild both renderings of the requirements exchange presentation from the one source deck.

The deck ``requirements-exchange-presentation.md`` carries speaker notes as HTML comments; they are
for the presenter and never for the audience. A slide may be marked for one audience only,
``<!-- audience: presenter -->`` or ``<!-- audience: public -->``, in the form of SWCraft's own
project presentation; this deck marks none today. This script produces:

- ``requirements-exchange-presentation.html`` — the presenter's deck: every slide except the
  public-only ones, notes kept (Marp shows them in presenter view);
- ``requirements-exchange-presentation-public.md`` / ``.html`` — the public deck: every slide except
  the presenter-only ones, every comment stripped except Marp directives
  (``<!-- _class: compact -->`` and the like: a one-line comment naming a directive Marp
  knows, :data:`MARP_DIRECTIVES`; ``<!-- Transition: ... -->`` is a note and is removed).

Run it after every edit to the deck:

    python demos/build_public.py

Stdlib only; needs ``marp`` on PATH (``brew install marp-cli``).

Every function reads the deck through one line scanner, :func:`scan`, whose docstring says which
CommonMark rules it follows and which it does not reach. The leak check is structural and runs
before anything is written: :func:`main` refuses, by name, a deck whose scan ends inside an HTML
comment or a fenced code block (:func:`unterminated`), and a public Markdown copy that holds any
comment outside a code block but a Marp directive, whatever its text (:func:`stray_comments`). The
rendered public HTML is then read once more as plain text for :data:`NOTE_MARKERS`, a second net:
a public slide that *shows* a marker in a code block (``<!-- audience: presenter -->`` as an
example) is refused there and both public copies are removed -- a refusal, never a leak.

What the structural check does not reach: whatever :func:`scan` does not model (its docstring) --
a comment inside a ``>`` quote or an indented code block is still read as a comment and refused,
never passed; a comment Marp would read inside a ``<pre>`` or ``<script>`` block is not seen as one.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "requirements-exchange-presentation.md"
PUBLIC_MD = HERE / "requirements-exchange-presentation-public.md"
PUBLIC_HTML = HERE / "requirements-exchange-presentation-public.html"
MAIN_HTML = HERE / "requirements-exchange-presentation.html"
MAIN_MD = HERE / "requirements-exchange-presentation-main.md"  # transient input for marp

#: Marp's directives by name, global and local (a local one may carry the ``_`` of a spot directive),
#: case as Marp reads them. Only a one-line comment ``<name>: <value>`` naming one of them is kept:
#: any other ``key: value`` comment -- ``<!-- Transition: ... -->`` -- is a speaker note.
MARP_DIRECTIVES = frozenset(
    {
        # global
        "theme", "style", "headingDivider", "size", "math", "marp", "lang",
        "title", "author", "description", "image", "keywords", "url",
        # local
        "paginate", "header", "footer", "class", "transition",
        "backgroundColor", "backgroundImage", "backgroundPosition", "backgroundRepeat",
        "backgroundSize", "color",
    }
)  # fmt: skip
_DIRECTIVE = re.compile(r"^_?([a-zA-Z][a-zA-Z0-9]*)\s*:\s*\S[^\n]*$")
#: A speaker note's markers, as the deck writes them; none may reach either public copy.
NOTE_MARKERS = ("Talk track", "Purpose:", "Audience:", "audience:", "Transition:", "[Sources")
_SEPARATOR = "---"

#: A line that is an audience marker: one directive comment and nothing else on the line.
_AUDIENCE = re.compile(r"[ \t]*<!--[ \t]*audience:[ \t]*(\w+)[ \t]*-->[ \t]*")
#: A fenced code block's opening line (CommonMark: at most three spaces, then three or more backticks
#: or tildes, then an info string -- one that holds no backtick after a backtick fence).
_FENCE_OPEN = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
#: A line that may close a fence: at most three spaces, a run of one fence character, then only
#: spaces or tabs; :func:`_closes` adds that the character and length suit the open fence.
_FENCE_CLOSE = re.compile(r" {0,3}(`{3,}|~{3,})[ \t]*")
#: A thematic break (CommonMark): at most three spaces, then three or more of one of ``-``, ``*``,
#: ``_``, with spaces or tabs between and after. Marp starts a slide at every one.
_BREAK = re.compile(r" {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})")


@dataclass(frozen=True)
class Line:
    """One line of a deck as :func:`scan` reads it."""

    text: str
    #: The line opens, continues or closes a fenced code block.
    in_fence: bool
    #: The line starts inside an HTML comment opened on an earlier line.
    in_comment: bool

    @property
    def outside(self) -> bool:
        """Whether the line starts as Markdown: neither in a code block nor in a comment."""
        return not (self.in_fence or self.in_comment)


def scan(text: str) -> list[Line]:
    """*text*'s lines (split at ``\\n``), each with whether it is in a fenced code block or a comment.

    The one Markdown reader of this script: every function below asks it, so a slide break, an
    audience marker and a note are found by the same rules. They follow CommonMark where they
    matter here:

    - a fenced code block opens at a line of three or more backticks or tildes indented at most three
      spaces (a backtick fence's info string holds no backtick), and closes at a line of the same
      character, at least as long, indented at most three spaces, with only spaces or tabs after
      it; a fence never closed runs to the end of the deck. Inside it nothing is a comment, a break
      or a marker;
    - outside a fence, an HTML comment runs from ``<!--`` to the next ``-->``, over as many lines as
      it takes; a line that starts inside one is no break, no marker and opens no fence.

    What this does not reach: container blocks -- a fence inside a list item indented four or more
    spaces, or inside a ``>`` quote, is not seen as one (its ``---`` line is caught as a break
    or by :func:`other_rules` instead, never silently passed); an indented (four-space) code block is
    not a code block here, so a ``***`` in one is reported by :func:`other_rules` as a break, which
    refuses a valid deck rather than leaking one; ``<!--`` inside an inline code span is read as a
    comment's start; the HTML block rules beyond comments (``<pre>``, ``<script>``) and the
    degenerate comments ``<!-->`` and ``<!--->`` are not modelled; a setext underline (``----``
    under a paragraph line) is read as a break, again a refusal rather than a leak.
    """
    return _scan(text)[0]


def _scan(text: str) -> tuple[list[Line], str, bool]:
    """:func:`scan`'s lines, the fence still open at the end (``""`` if none) and whether a comment is."""
    lines: list[Line] = []
    fence = ""
    in_comment = False
    for raw in text.split("\n"):
        if fence:
            lines.append(Line(raw, in_fence=True, in_comment=False))
            if _closes(raw, fence):
                fence = ""
        elif in_comment:
            lines.append(Line(raw, in_fence=False, in_comment=True))
            closing = raw.find("-->")
            in_comment = closing < 0 or _comment_open_after(raw, closing + 3)
        else:
            opening = _FENCE_OPEN.fullmatch(raw)
            if opening and not (opening.group(1)[0] == "`" and "`" in opening.group(2)):
                fence = opening.group(1)
                lines.append(Line(raw, in_fence=True, in_comment=False))
            else:
                lines.append(Line(raw, in_fence=False, in_comment=False))
                in_comment = _comment_open_after(raw, 0)
    return lines, fence, in_comment


def unterminated(text: str) -> str | None:
    """What *text* leaves open at its end, as :func:`scan` reads it: a comment, a fence, or ``None``.

    Either swallows the rest of the deck -- a comment never closed is a note :func:`strip_notes`
    cannot remove, a fence never closed hides every comment after it -- so :func:`main` refuses it.
    """
    _, fence, in_comment = _scan(text)
    if in_comment:
        return "an HTML comment ('<!--' without '-->')"
    if fence:
        return f"a fenced code block ({fence!r} never closed)"
    return None


def stray_comments(text: str) -> list[str]:
    """Every HTML comment outside a fenced code block of *text* that is not a Marp directive.

    Read as :func:`scan` reads it; a ``<!--`` never closed counts as one, its text to the end. The
    public copy must hold none: :func:`main` refuses it whatever the comment says.
    """
    found: list[str] = []
    for in_fence, run in groupby(scan(text), key=lambda line: line.in_fence):
        if in_fence:
            continue
        block = "\n".join(line.text for line in run)
        for match in re.finditer(r"<!--(.*?)(?:-->|\Z)", block, flags=re.S):
            if not (match.group(0).endswith("-->") and is_directive(match.group(1))):
                found.append(match.group(0))
    return found


def _closes(line: str, fence: str) -> bool:
    """Whether *line* closes the fenced code block *fence* (its opening run of backticks or tildes)."""
    match = _FENCE_CLOSE.fullmatch(line)
    if not match:
        return False
    run = match.group(1)
    return run[0] == fence[0] and len(run) >= len(fence)


def _comment_open_after(line: str, start: int) -> bool:
    """Whether an HTML comment is still open at the end of *line*, read from *start* outside one."""
    position = start
    while True:
        opening = line.find("<!--", position)
        if opening < 0:
            return False
        closing = line.find("-->", opening + 4)
        if closing < 0:
            return True
        position = closing + 3


def split_slides(text: str) -> list[str]:
    """*text*'s slides, the front matter first: split at each ``---`` line :func:`scan` reads as Markdown.

    A ``---`` line inside a fenced code block (a YAML document marker in an example) or inside an
    HTML comment (a note) is the slide's content, not a boundary, so a presenter-only slide holding
    one is dropped whole. Joining the parts with ``"\\n---\\n"`` gives *text* back unchanged.

    What this does not reach: Marp's other breaks (``***``, ``___``, ``- - -``, an indented or
    longer dash line) also start a slide and are not split at here -- the deck writes every boundary
    as ``---``, and :func:`main` refuses a deck that holds one of the others (:func:`other_rules`).
    """
    slides: list[list[str]] = [[]]
    for index, line in enumerate(scan(text)):
        if index > 0 and line.outside and line.text == _SEPARATOR:
            slides.append([])
            continue
        slides[-1].append(line.text)
    return ["\n".join(slide) for slide in slides]


def join_slides(slides: list[str]) -> str:
    """The inverse of :func:`split_slides`."""
    return f"\n{_SEPARATOR}\n".join(slides)


def other_rules(text: str) -> list[str]:
    """The Markdown lines Marp would read as a slide break other than a plain ``---`` line.

    Lines in a fenced code block or a comment are content (:func:`scan`), so a ``***`` in a speaker
    note or an example is not one.
    """
    return [
        line.text
        for line in scan(text)
        if line.outside and line.text != _SEPARATOR and _BREAK.fullmatch(line.text)
    ]


def drop_audience(text: str, audience: str) -> tuple[str, int]:
    """Remove every slide marked ``<!-- audience: <audience> -->``; the front matter is slide 0.

    A marker counts only as a line of its own outside a code block and a comment (:func:`scan`);
    such a line is removed from every slide kept. A marker shown in a code block is the slide's
    content and stays.
    """
    slides = split_slides(text)
    kept = [slides[0]]
    dropped = 0
    for slide in slides[1:]:
        lines = scan(slide)
        markers = {
            index: match.group(1)
            for index, line in enumerate(lines)
            if line.outside and (match := _AUDIENCE.fullmatch(line.text))
        }
        if audience in markers.values():
            dropped += 1
            continue
        kept.append("\n".join(line.text for index, line in enumerate(lines) if index not in markers))
    return join_slides(kept), dropped


def is_directive(body: str) -> bool:
    """Whether a comment's *body* is one Marp directive: one line, a name :data:`MARP_DIRECTIVES` holds."""
    if "\n" in body.strip():
        return False
    match = _DIRECTIVE.match(body.strip())
    return bool(match) and match.group(1) in MARP_DIRECTIVES


def strip_notes(text: str) -> tuple[str, int]:
    """*text* with every HTML comment removed but the Marp directives; the number removed.

    Comments are read as :func:`scan` reads them: a ``<!-- -->`` inside a fenced code block is the
    block's content and stays, and the runs of blank lines a removed note leaves are closed up only
    outside code blocks. A comment never closed is left in place: :func:`main` refuses the deck
    before writing (:func:`unterminated`, :func:`stray_comments`).
    """
    removed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal removed
        body = match.group(1)
        if is_directive(body):
            return match.group(0)
        removed += 1
        return ""

    # Consecutive lines of one kind, each run as text: a comment never spans a fence, because a
    # line inside a comment opens none.
    parts: list[str] = []
    for in_fence, run in groupby(scan(text), key=lambda line: line.in_fence):
        block = "\n".join(line.text for line in run)
        if in_fence:
            # An empty line of a code block is held by a placeholder so the close-up below skips it.
            parts.append("\n".join(line or _HELD for line in block.split("\n")))
        else:
            parts.append(re.sub(r"<!--(.*?)-->", replace, block, flags=re.S))
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(parts))
    return out.replace(_HELD, ""), removed


#: Stands for an empty line of a code block while :func:`strip_notes` closes up blank lines.
_HELD = "\0"


def render(md: Path, html: Path) -> None:
    subprocess.run(["marp", "--html", "--no-stdin", str(md), "-o", str(html)], check=True)


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    rules = other_rules(source)
    if rules:
        print(
            f"error: {SOURCE.name} writes a slide boundary as {rules[0]!r}; write it as '---'",
            file=sys.stderr,
        )
        return 1
    left_open = unterminated(source)
    if left_open:
        print(f"error: {SOURCE.name} ends inside {left_open}; nothing written", file=sys.stderr)
        return 1

    # Both copies are built and checked in memory before either is written.
    main_text, public_only = drop_audience(source, "public")
    text, presenter_only = drop_audience(source, "presenter")
    text, removed = strip_notes(text)
    left_open = unterminated(text)
    if left_open:
        print(f"error: {PUBLIC_MD.name} would end inside {left_open}; nothing written", file=sys.stderr)
        return 1
    stray = stray_comments(text)
    if stray:
        print(
            f"error: {PUBLIC_MD.name} would keep a comment that is no Marp directive: "
            f"{stray[0][:60]!r}; nothing written",
            file=sys.stderr,
        )
        return 1

    MAIN_MD.write_text(main_text, encoding="utf-8", newline="\n")
    try:
        render(MAIN_MD, MAIN_HTML)
    finally:
        MAIN_MD.unlink()

    PUBLIC_MD.write_text(text, encoding="utf-8", newline="\n")
    render(PUBLIC_MD, PUBLIC_HTML)
    html = PUBLIC_HTML.read_text(encoding="utf-8")
    for marker in NOTE_MARKERS:
        if marker in html:
            PUBLIC_MD.unlink()
            PUBLIC_HTML.unlink()
            print(
                f"error: a note marker survived in {PUBLIC_HTML.name}: {marker!r}; "
                "both public copies removed",
                file=sys.stderr,
            )
            return 1
    print(
        f"{MAIN_HTML.name}: {public_only} public-only slide(s) dropped; "
        f"{PUBLIC_MD.name} and {PUBLIC_HTML.name}: {presenter_only} presenter-only slide(s) "
        f"and {removed} note blocks removed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
