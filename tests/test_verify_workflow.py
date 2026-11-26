"""The work repository's gate ``.gitea/workflows/verify.yml``, pinned.

It asserts what the guarantee *a green run means the suite and the kit build pass, in the checkout
and in the public tree, and nothing left the runner* rests on: the triggers, the single job
``linux`` (the name SWCraft's publish step looks for, with the file name), the suite before the
build, the pinned SWCraft version read from ``swcraft.yaml`` rather than written here, ``--tagged``
only on a tag ref, the public-tree step reading ``public-paths.txt`` and running the suite there in
a repository whose one commit carries an explicit identity, and the absence of anything that
publishes: no secret, no ``sftp``/``ssh``, no address, no upload or release step.

Each check is a function over the workflow's text returning its problems, so the negative cases
run on in-memory variants of the real file.

The workflow is read as **text**, not parsed as YAML: this repository's suite is stdlib-only
(``python -m unittest discover -s tests``) and installs nothing, so there is no PyYAML to read it
as data. The scans are ``workflow_text.py``'s, shared with ``test_release_workflow.py``; what they
do not reach is what a YAML parser would catch: a duplicated key, a mis-indented block that still
parses. The run that proves the file is valid YAML is Gitea's own.

``.gitea/`` is closed: the open copy does not carry the workflow, so in the public tree this whole
file skips, naming that reason, rather than moving to a closed test folder.
"""

from __future__ import annotations

import re
import sys
import unittest
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workflow_text import code_lines, step_blocks, step_name, without_comments  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT_ROOT / ".gitea" / "workflows" / "verify.yml"
ABSENT = ".gitea/ is closed and absent from the public tree: there is no workflow to read"

TESTS_STEP = "tests"
PIN_STEP = "read the pin"
BUILD_STEP = "build the colleague kit"
PUBLIC_TREE_STEP = "the public tree, tests and the kit build"
SUITE = "python -m unittest discover -s tests -v"
BUILD = 'python scripts/build_colleague_kit.py "${kit_args[@]}"'
#: The tag condition, as the build steps' environment carries it, and the one line that may
#: add ``--tagged`` -- under it.
TAG_ENV = "IS_TAG: ${{ startsWith(github.ref, 'refs/tags/') }}"
TAGGED_LINE = 'if [ "$IS_TAG" = true ]; then kit_args+=(--tagged); fi'
VERSION_ENV = "SWCRAFT_VERSION: ${{ steps.pin.outputs.version }}"
IDENTITY = 'git -c user.name="public tree" -c user.email=snapshot@invalid commit'
VERSION_LITERAL = "a version literal is a second pin to keep in step"
#: The public tree's script, in the order it must run: the open paths taken from HEAD, made a
#: one-commit repository, and the suite and the kit build run there.
PUBLIC_TREE_ORDER = (
    'git archive --format=tar HEAD -- "${entries[@]}" | tar -x -C "$tree"',
    'cd "$tree"',
    "git init -q",
    "git add -A",
    IDENTITY,
    SUITE,
    BUILD,
    "cat dist/colleague-kit/SHA256SUMS",
)


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def step_names(text: str) -> list[str]:
    """The steps of the one job, in file order, by ``name:`` or, for an action, by ``uses:``."""
    return [step_name(block) for block in step_blocks(text)]


def steps(text: str) -> dict[str, str]:
    return dict(zip(step_names(text), step_blocks(text)))


# --- the checks: each returns its problems, empty when the text holds -------------------------


def check_triggers(text: str) -> list[str]:
    problems = []
    for wanted in ("on:\n  push:\n    branches: [main]\n    tags: [\"v*\"]\n", "  workflow_dispatch:\n"):
        if wanted not in text:
            problems.append(f"trigger missing: {wanted.strip()!r}")
    for absent in ("pull_request", "schedule:"):
        if absent in text:
            problems.append(f"unexpected trigger {absent!r}")
    return problems


def check_single_job(text: str) -> list[str]:
    jobs = re.findall(r"^  ([A-Za-z0-9_-]+):\s*$", text.partition("\njobs:\n")[2], re.MULTILINE)
    problems = [] if jobs == ["linux"] else [f"the jobs are {jobs}, not the one job 'linux'"]
    if "    runs-on: linux\n" not in text:
        problems.append("the job does not run on the self-hosted 'linux' runner")
    if "timeout-minutes:" not in text:
        problems.append("the job has no timeout")
    return problems


def check_order(text: str) -> list[str]:
    names = step_names(text)
    order = [TESTS_STEP, PIN_STEP, BUILD_STEP, PUBLIC_TREE_STEP]
    if [name for name in names if name in order] != order:
        return [f"the steps must run in the order {order}, found {names}"]
    found = steps(text)
    problems = []
    if SUITE not in found[TESTS_STEP]:
        problems.append("the tests step does not run the suite")
    tree = code_lines(found[PUBLIC_TREE_STEP])
    if SUITE not in tree or BUILD not in tree or tree.index(SUITE) > tree.index(BUILD):
        problems.append("the public tree does not run the suite before the kit build")
    return problems


def check_version_from_manifest(text: str) -> list[str]:
    found = steps(text)
    problems = []
    pin = found.get(PIN_STEP, "")
    for wanted in (
        "id: pin",
        "from build_colleague_kit import parse_toolchain_version",
        'parse_toolchain_version(Path("swcraft.yaml")',
        'echo "version=$version" >> "$GITHUB_OUTPUT"',
    ):
        if wanted not in pin:
            problems.append(f"the pin step lacks {wanted!r}")
    for name in (BUILD_STEP, PUBLIC_TREE_STEP):
        block = found.get(name, "")
        if VERSION_ENV not in block or 'kit_args=(--swcraft-version "$SWCRAFT_VERSION")' not in block:
            problems.append(f"{name!r} does not build with the version read from the manifest")
    literals = re.findall(r"\b\d+\.\d+\.\d+\b", text)
    if literals:
        problems.append(f"{VERSION_LITERAL}: {literals}")
    return problems


def check_tagged_only_on_tags(text: str) -> list[str]:
    problems = []
    for name, block in steps(text).items():
        tagged = [line for line in code_lines(block) if "--tagged" in line]
        if not tagged:
            continue
        if any(line != TAGGED_LINE for line in tagged):
            problems.append(f"{name!r} passes --tagged outside the tag condition: {tagged}")
        if TAG_ENV not in block:
            problems.append(f"{name!r} passes --tagged without the tag condition in its environment")
    for name in (BUILD_STEP, PUBLIC_TREE_STEP):
        if TAGGED_LINE not in code_lines(steps(text).get(name, "")):
            problems.append(f"{name!r} never builds the tagged kit on a tag")
    return problems


def check_public_tree(text: str) -> list[str]:
    block = steps(text).get(PUBLIC_TREE_STEP)
    if block is None:
        return ["there is no public-tree step"]
    lines = code_lines(block)
    problems = []
    for wanted in (
        "sed -e 's/#.*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' public-paths.txt | grep -v '^$')",
        'git archive --format=tar HEAD -- "${entries[@]}" | tar -x -C "$tree"',
        'cd "$tree"',
        "git init -q",
        "git add -A",
        "cat dist/colleague-kit/SHA256SUMS",
    ):
        if not any(wanted in line for line in lines):
            problems.append(f"the public-tree step lacks {wanted!r}")
    script = lines[lines.index("run: |") + 1 :] if "run: |" in lines else []
    if script[:1] != ["set -euo pipefail"]:
        problems.append("the public-tree script does not start with set -euo pipefail")
    found = [next((number for number, line in enumerate(script) if line.startswith(wanted)), -1) for wanted in PUBLIC_TREE_ORDER]
    if -1 in found or found != sorted(found):
        problems.append(f"the public-tree script does not run {list(PUBLIC_TREE_ORDER)} in this order: {found}")
    return problems


def check_public_tree_identity(text: str) -> list[str]:
    block = steps(text).get(PUBLIC_TREE_STEP, "")
    commits = [line for line in code_lines(block) if re.search(r"\bgit\b.*\bcommit\b", line)]
    if not commits or any(not line.startswith(IDENTITY) for line in commits):
        return [f"the public tree's commit carries no explicit identity: {commits}"]
    return []


def check_nothing_published(text: str) -> list[str]:
    problems = []
    if "secrets." in text:
        problems.append("a secrets. reference")
    for word in ("sftp", "ssh", "scp", "rsync", "curl", "wget", "nc", "git push", "gh", "tea", "GITEA_TOKEN", "api/v1"):
        if re.search(rf"\b{re.escape(word)}\b", without_comments(text), re.IGNORECASE):
            problems.append(f"{word!r} in a step")
    addresses = re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text)
    if addresses:
        problems.append(f"an IPv4 literal: {addresses}")
    for name in step_names(text):
        if re.search(r"upload|release|publish", name, re.IGNORECASE):
            problems.append(f"a step {name!r}")
    return problems


def check_interpreter(text: str) -> list[str]:
    problems = []
    uses = [line for line in text.splitlines() if line.strip().startswith("- uses:")]
    if uses != ["      - uses: actions/checkout@v4"]:
        problems.append(f"the only action is the checkout, found {uses}")
    if "python --version" not in steps(text).get("the interpreter the runner offers", ""):
        problems.append("the runner's python does not name itself in the log")
    for absent in ("python3.", "setup_showcase", "--check-runtime"):
        if absent in without_comments(text):
            problems.append(f"{absent!r} in a step")
    return problems


CHECKS: tuple[Callable[[str], list[str]], ...] = (
    check_triggers,
    check_single_job,
    check_order,
    check_version_from_manifest,
    check_tagged_only_on_tags,
    check_public_tree,
    check_public_tree_identity,
    check_nothing_published,
    check_interpreter,
)


@unittest.skipUnless(WORKFLOW.is_file(), ABSENT)
class TestTheWorkflowHolds(unittest.TestCase):
    def test_every_check_passes_on_the_real_file(self) -> None:
        text = workflow_text()
        for check in CHECKS:
            with self.subTest(check.__name__):
                self.assertEqual([], check(text))


@unittest.skipUnless(WORKFLOW.is_file(), ABSENT)
class TestTheChecksRefuseVariants(unittest.TestCase):
    """In-memory variants of the real file: each check must see what it guards against."""

    def setUp(self) -> None:
        self.text = workflow_text()

    def variant(self, old: str, new: str) -> str:
        self.assertEqual(1, self.text.count(old), f"{old!r} must occur once to build the variant")
        return self.text.replace(old, new)

    def test_an_sftp_line_is_refused(self) -> None:
        text = self.variant(
            "          cat dist/colleague-kit/SHA256SUMS\n\n",
            "          cat dist/colleague-kit/SHA256SUMS\n          echo put kit | sftp -b - writer@host\n\n",
        )
        self.assertTrue(check_nothing_published(text))

    def test_a_git_push_or_a_release_client_is_refused(self) -> None:
        for command in ("git push origin HEAD", "gh release create v1", "tea releases create", "wget -q https://example.com/x"):
            with self.subTest(command=command):
                old = "          cat dist/colleague-kit/SHA256SUMS\n\n"
                self.assertTrue(check_nothing_published(self.variant(old, f"          cat dist/colleague-kit/SHA256SUMS\n          {command}\n\n")))

    def test_a_public_tree_out_of_order_is_refused(self) -> None:
        text = self.variant('          cd "$tree"\n          git init -q\n', "          git init -q\n")
        text = text.replace("          cat dist/colleague-kit/SHA256SUMS\n", '          cat dist/colleague-kit/SHA256SUMS\n          cd "$tree"\n')
        problems = check_public_tree(text)
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(problems[0].startswith("the public-tree script does not run"), problems)

    def test_a_secrets_reference_is_refused(self) -> None:
        text = self.variant(
            "          SWCRAFT_VERSION: ${{ steps.pin.outputs.version }}\n          IS_TAG: ${{ startsWith(github.ref, 'refs/tags/') }}\n        run: |\n          set -euo pipefail\n          kit_args",
            "          SWCRAFT_VERSION: ${{ steps.pin.outputs.version }}\n          IS_TAG: ${{ startsWith(github.ref, 'refs/tags/') }}\n          KEY: ${{ secrets.KEY }}\n        run: |\n          set -euo pipefail\n          kit_args",
        )
        self.assertTrue(check_nothing_published(text))

    def test_an_ipv4_literal_is_refused(self) -> None:
        address = "10." + "0.0.1"
        text = self.variant("        run: python --version\n", f"        run: python --version && echo {address}\n")
        self.assertTrue(check_nothing_published(text))

    def test_an_upload_step_is_refused(self) -> None:
        text = self.text + "\n      - name: upload the kit\n        run: true\n"
        self.assertTrue(check_nothing_published(text))

    def test_tagged_outside_the_tag_condition_is_refused(self) -> None:
        old = 'python scripts/build_colleague_kit.py "${kit_args[@]}"\n          cat dist/colleague-kit/SHA256SUMS\n\n'
        text = self.variant(old, old.replace('"${kit_args[@]}"', '"${kit_args[@]}" --tagged'))
        self.assertTrue(check_tagged_only_on_tags(text))

    def test_tagged_without_the_tag_environment_is_refused(self) -> None:
        old = "          IS_TAG: ${{ startsWith(github.ref, 'refs/tags/') }}\n        run: |\n          set -euo pipefail\n          kit_args"
        text = self.variant(old, old.replace("startsWith(github.ref, 'refs/tags/')", "true"))
        self.assertTrue(check_tagged_only_on_tags(text))

    def test_a_version_literal_is_refused(self) -> None:
        text = self.variant("        run: python --version\n", "        run: python --version && echo 0." + "1.2\n")
        self.assertEqual([f"{VERSION_LITERAL}: ['0." + "1.2']"], check_version_from_manifest(text))

    def test_the_build_before_the_suite_is_refused(self) -> None:
        tests = "      - name: tests\n        run: python -m unittest discover -s tests -v\n\n"
        text = self.variant(tests, "") + "\n" + tests
        self.assertTrue(check_order(text))

    def test_a_public_tree_without_the_suite_is_refused(self) -> None:
        text = self.variant(
            "          python -m unittest discover -s tests -v\n          kit_args", "          kit_args"
        )
        self.assertTrue(check_order(text))

    def test_a_public_tree_not_reading_the_allow_list_is_refused(self) -> None:
        text = self.text.replace(" public-paths.txt | grep", " other.txt | grep")
        self.assertNotEqual(self.text, text)
        self.assertTrue(check_public_tree(text))

    def test_a_public_tree_script_that_does_not_stop_on_errors_is_refused(self) -> None:
        text = self.variant(
            "        run: |\n          set -euo pipefail\n          tree=", "        run: |\n          tree="
        )
        self.assertTrue(check_public_tree(text))

    def test_a_public_tree_commit_without_identity_is_refused(self) -> None:
        text = self.variant(IDENTITY, "git commit")
        self.assertTrue(check_public_tree_identity(text))

    def test_a_second_job_is_refused(self) -> None:
        self.assertTrue(check_single_job(self.text + "  windows:\n    runs-on: windows\n"))

    def test_a_pull_request_trigger_is_refused(self) -> None:
        text = self.variant("  workflow_dispatch:\n", "  workflow_dispatch:\n  pull_request:\n")
        self.assertTrue(check_triggers(text))

    def test_a_setup_python_action_is_refused(self) -> None:
        text = self.variant(
            "      - uses: actions/checkout@v4\n",
            "      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n",
        )
        self.assertTrue(check_interpreter(text))


if __name__ == "__main__":
    unittest.main()
