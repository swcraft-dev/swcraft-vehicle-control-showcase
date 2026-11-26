"""Reading a workflow file as text: the scans ``test_verify_workflow.py`` and ``test_release_workflow.py`` share.

The suite is stdlib-only, so a workflow is not parsed as YAML: these are indentation scans over
the ``jobs:`` map and a job's ``steps:`` list. What they do not reach (a duplicated key, a
mis-indented block that still parses) is what the CI host's own parser catches on the first run.
"""

from __future__ import annotations

import re

#: A step of a job's ``steps:`` list starts at this indentation.
STEP_PREFIX = "      - "


def head_of(text: str) -> str:
    """Everything before ``jobs:``: the triggers, the permissions, the concurrency group."""
    return text.partition("\njobs:\n")[0]


def job_blocks(text: str) -> dict[str, str]:
    """Each job under ``jobs:``, by name, as its own block of text."""
    blocks: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.partition("\njobs:\n")[2].splitlines():
        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if match:
            current = blocks.setdefault(match.group(1), [])
        elif current is not None:
            current.append(line)
    return {name: "\n".join(lines) for name, lines in blocks.items()}


def step_blocks(job: str) -> list[str]:
    """Every entry of a ``steps:`` list in *job*, as its own block of text."""
    blocks: list[str] = []
    current: list[str] | None = None
    for line in job.splitlines():
        if line.startswith(STEP_PREFIX):
            if current is not None:
                blocks.append("\n".join(current))
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append("\n".join(current))
    return blocks


def step_name(block: str) -> str:
    """A step's ``name:``, or, for an action, its ``uses:`` without the ``@`` ref."""
    head = block.splitlines()[0][len(STEP_PREFIX) :]
    key, _, value = head.partition(": ")
    if key == "uses":
        return value.split("@")[0].strip()
    return value.strip() if key == "name" else head.strip()


def steps(job: str) -> dict[str, str]:
    """The steps of *job* by name, in file order."""
    return {step_name(block): block for block in step_blocks(job)}


def code_lines(block: str) -> list[str]:
    """The block's lines without YAML/shell comments, stripped."""
    return [line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]


def without_comments(text: str) -> str:
    return "\n".join(code_lines(text))


def find_run(lines: list[str], run: list[str]) -> int:
    """Where the contiguous *run* of lines starts in *lines*, or -1 when it is not there."""
    for start in range(len(lines) - len(run) + 1):
        if lines[start : start + len(run)] == run:
            return start
    return -1
