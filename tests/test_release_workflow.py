"""The open copy's release workflow ``.github/workflows/release.yml``, pinned.

It asserts what the guarantee *a release is the kit built from a tag, attached with its sums, and
nothing else is reached* rests on: the triggers (a tag push and a dispatch with the ``draft``
input), the runner ``ubuntu-24.04``, the GitHub-only guard and the tag-ref refusal on every job,
read-only permissions with ``contents: write`` in ``publish`` alone, one concurrency group per ref
that never cancels, every action pinned by a full commit SHA under ``actions/``, no secret, no
cache, no pull-request trigger, the SWCraft version read from ``swcraft.yaml`` and handed to
``publish`` as the ``kit`` job's output, and the release lifecycle: exactly one kit zip, a
``gh release view`` whose failures other than *release not found* fail the step, the create (a
draft only under the dispatch's ``draft`` input), the refusal of a ``draft: true`` dispatch on a
published release, the re-upload with ``--clobber`` and the guarded ``--draft=false`` edit, in
that order, each create and upload naming both assets.

Each check is a function over the workflow's text returning its problems, so the negative cases
run on in-memory variants of the real file. The workflow is read as text with the scans of
``workflow_text.py``.

``.github/`` is open, so this file never skips.
"""

from __future__ import annotations

import re
import sys
import unittest
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workflow_text import code_lines, find_run, head_of, job_blocks, step_blocks, step_name, steps, without_comments  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "release.yml"

JOBS = ("kit", "publish")
GUARD = "    if: github.server_url == 'https://github.com'"
RUNNER = "    runs-on: ubuntu-24.04"
REFUSAL_STEP = "refuse a ref that is not a tag"
PIN_STEP = "read the pin"
BUILD_STEP = "build the colleague kit"
RELEASE_STEP = "create or update the release"
SUITE = "python -m unittest discover -s tests -v"
#: The four actions a release may use, each by a full commit SHA with its exact release tag.
PINNED_USES = re.compile(
    r"^\s*(?:- )?uses: actions/(?:checkout|setup-python|upload-artifact|download-artifact)"
    r"@[0-9a-f]{40} # v\d+\.\d+\.\d+$"
)
DRAFT_ENV = "DRAFT: ${{ github.event_name == 'workflow_dispatch' && inputs.draft }}"
CONCURRENCY = "\nconcurrency:\n  group: release-${{ github.ref }}\n  cancel-in-progress: false\n"
ASSETS = ('"${zips[@]}"', "SHA256SUMS")
VERSION_LITERAL = "a version literal is a second pin to keep in step"

# The release step's script, in the order it must run, as contiguous runs of its code lines.
#: Exactly one kit zip, or nothing is released.
ONE_ZIP = ["shopt -s nullglob", "zips=(*.zip)", 'if [ "${#zips[@]}" -ne 1 ]; then']
#: The release looked up: only *release not found* means there is none; any other failure stops.
VIEW = [
    'if is_draft=$(gh release view "$TAG" --json isDraft --jq .isDraft 2>"$err"); then',
    "exists=true",
    'elif grep -q "release not found" "$err"; then',
    "exists=false",
    "else",
    'cat "$err" >&2',
    "exit 1",
    "fi",
]
#: No release yet: create it, a draft only under the dispatch's draft input.
CREATE = [
    'if [ "$exists" = false ]; then',
    "create_args=()",
    'if [ "$DRAFT" = true ]; then create_args+=(--draft); fi',
]
#: The create consumes the draft arguments built above; without them a draft dispatch publishes.
CREATE_ARGS = '"${create_args[@]}"'
#: A draft: true dispatch on a published release: refused before anything is uploaded.
REFUSAL_CONDITION = '[ "$DRAFT" = true ] && [ "$is_draft" != true ]'
REFUSAL = f"elif {REFUSAL_CONDITION}; then"
#: The existing release re-uploaded and, unless the dispatch asked for a draft, made final.
REUPLOAD = 'gh release upload "$TAG" "${zips[@]}" SHA256SUMS --clobber'
FINAL_EDIT = ['if [ "$DRAFT" != true ]; then', 'gh release edit "$TAG" --draft=false', "fi"]


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


# --- the checks: each returns its problems, empty when the text holds -------------------------


def check_triggers(text: str) -> list[str]:
    problems = []
    for wanted in (
        'on:\n  push:\n    tags: ["v*"]\n  workflow_dispatch:\n    inputs:\n      draft:\n',
        "        type: boolean\n        default: true\n",
    ):
        if wanted not in head_of(text):
            problems.append(f"trigger missing: {wanted.strip()!r}")
    for absent in ("pull_request", "schedule:", "branches:"):
        if absent in without_comments(text):
            problems.append(f"unexpected trigger {absent!r}")
    return problems


def check_jobs(text: str) -> list[str]:
    jobs = job_blocks(text)
    problems = [] if tuple(jobs) == JOBS else [f"the jobs are {list(jobs)}, not {list(JOBS)}"]
    for name, block in jobs.items():
        lines = block.splitlines()
        if GUARD not in lines:
            problems.append(f"job {name!r} lacks the guard {GUARD.strip()!r}")
        if RUNNER not in lines:
            problems.append(f"job {name!r} does not run on ubuntu-24.04")
        if not any(line.startswith("    timeout-minutes: ") for line in lines):
            problems.append(f"job {name!r} has no timeout")
    if "    needs: kit" not in jobs.get("publish", "").splitlines():
        problems.append("publish does not need kit")
    return problems


def check_tag_refusal(text: str) -> list[str]:
    problems = []
    for name, block in job_blocks(text).items():
        found = step_blocks(block)
        first = found[0] if found else ""
        lines = code_lines(first)
        if not found or step_name(first) != REFUSAL_STEP:
            problems.append(f"job {name!r} does not start by refusing a ref that is not a tag")
            continue
        for wanted in ("REF_TYPE: ${{ github.ref_type }}", 'if [ "$REF_TYPE" != tag ]; then', "exit 1"):
            if wanted not in lines:
                problems.append(f"job {name!r}'s refusal lacks {wanted!r}")
        if not any(line.startswith("echo ") and "$REF" in line and "tag" in line for line in lines):
            problems.append(f"job {name!r}'s refusal does not name the ref")
    return problems


def check_permissions(text: str) -> list[str]:
    problems = []
    if "\npermissions:\n  contents: read\n" not in head_of(text) + "\n":
        problems.append("the top-level permissions are not 'contents: read'")
    if re.search(r"^\s*[a-z-]+: write\s*$", head_of(text), re.MULTILINE):
        problems.append("a write permission at the top level")
    for name, block in job_blocks(text).items():
        writes = re.findall(r"^\s*([a-z-]+): write\s*$", block, re.MULTILINE)
        allowed = ["contents"] if name == "publish" else []
        if writes != allowed:
            problems.append(f"job {name!r} has write permissions {writes}, not {allowed}")
    if "    permissions:\n      contents: write" not in job_blocks(text).get("publish", ""):
        problems.append("publish is not granted 'contents: write'")
    return problems


def check_actions_pinned(text: str) -> list[str]:
    uses = [line for line in text.splitlines() if re.match(r"^\s*(?:- )?uses:", line)]
    problems = [f"not pinned to an actions/ commit with its tag: {line.strip()!r}" for line in uses if not PINNED_USES.match(line)]
    if len(uses) != 4:
        problems.append(f"{len(uses)} actions, not the four (checkout, setup-python, upload- and download-artifact)")
    return problems


def check_nothing_secret(text: str) -> list[str]:
    problems = []
    if "secrets." in text:
        problems.append("a secrets. reference")
    if re.search(r"\bcache\b", without_comments(text), re.IGNORECASE):
        problems.append("a cache")
    return problems


def check_version_from_manifest(text: str) -> list[str]:
    jobs = job_blocks(text)
    kit = jobs.get("kit", "")
    found = steps(kit)
    problems = []
    if "    outputs:\n      swcraft_version: ${{ steps.pin.outputs.version }}" not in kit:
        problems.append("kit does not hand the pin on as its output swcraft_version")
    pin = found.get(PIN_STEP, "")
    for wanted in (
        "id: pin",
        "from build_colleague_kit import parse_toolchain_version",
        'parse_toolchain_version(Path("swcraft.yaml")',
        'echo "version=$version" >> "$GITHUB_OUTPUT"',
    ):
        if wanted not in pin:
            problems.append(f"the pin step lacks {wanted!r}")
    build = code_lines(found.get(BUILD_STEP, ""))
    if "SWCRAFT_VERSION: ${{ steps.pin.outputs.version }}" not in build or not any(
        line.startswith("python scripts/build_colleague_kit.py") and '--swcraft-version "$SWCRAFT_VERSION"' in line and "--tagged" in line
        for line in build
    ):
        problems.append("the kit is not built --tagged with the version read from the manifest")
    if "SWCRAFT_VERSION: ${{ needs.kit.outputs.swcraft_version }}" not in steps(jobs.get("publish", "")).get(RELEASE_STEP, ""):
        problems.append("publish does not read the version from kit's output")
    scanned = "\n".join(line for line in text.splitlines() if not re.match(r"^\s*(?:- )?uses:", line))
    literals = re.findall(r"\b\d+\.\d+\.\d+\b", scanned)
    if literals:
        problems.append(f"{VERSION_LITERAL}: {literals}")
    return problems


def check_suite_before_build(text: str) -> list[str]:
    names = list(steps(job_blocks(text).get("kit", "")))
    if "tests" not in names or BUILD_STEP not in names or names.index("tests") > names.index(BUILD_STEP):
        return [f"the suite does not run before the kit build: {names}"]
    if SUITE not in steps(job_blocks(text)["kit"])["tests"]:
        return ["the tests step does not run the suite"]
    return []


def check_artifact_handover(text: str) -> list[str]:
    jobs = job_blocks(text)
    problems = []
    upload = steps(jobs.get("kit", "")).get("actions/upload-artifact", "")
    for wanted in ("name: colleague-kit", "dist/colleague-kit/*.zip", "dist/colleague-kit/SHA256SUMS", "retention-days: 1"):
        if wanted not in code_lines(upload):
            problems.append(f"the artifact upload lacks {wanted!r}")
    download = steps(jobs.get("publish", "")).get("actions/download-artifact", "")
    if "name: colleague-kit" not in code_lines(download):
        problems.append("publish does not download the kit's artifact")
    return problems


def check_concurrency(text: str) -> list[str]:
    if CONCURRENCY not in head_of(text):
        return [f"the runs of one ref are not queued, never cancelled: {CONCURRENCY.strip()!r} missing"]
    return []


def check_release_lifecycle(text: str) -> list[str]:
    block = steps(job_blocks(text).get("publish", "")).get(RELEASE_STEP)
    if block is None:
        return ["publish has no release step"]
    lines = code_lines(block)
    problems = []
    for wanted in ("GH_TOKEN: ${{ github.token }}", "GH_REPO: ${{ github.repository }}", DRAFT_ENV):
        if wanted not in lines:
            problems.append(f"the release step lacks {wanted!r}")
    creates = [line for line in lines if line.startswith("gh release create ")]
    uploads = [line for line in lines if line.startswith("gh release upload ")]
    for line in creates + uploads:
        missing = [asset for asset in ASSETS if asset not in line.split()]
        if missing:
            problems.append(f"{line!r} does not name {missing}")
    if len(creates) != 1:
        problems.append(f"{len(creates)} gh release create lines, not the one")

    # Each part, found where it must stand: -1 is "not there".
    one_zip = find_run(lines, ONE_ZIP)
    if one_zip < 0 or lines[one_zip + 4 : one_zip + 6] != ["exit 1", "fi"] or not lines[one_zip + 3].startswith("echo "):
        problems.append("the step does not refuse an artifact without exactly one kit zip (nullglob, count, exit 1)")
    view = find_run(lines, VIEW)
    if view < 0:
        problems.append("a failing gh release view is not told apart from 'release not found'")
    create = find_run(lines, CREATE)
    if create < 0 or not lines[create + len(CREATE)].startswith("gh release create "):
        problems.append("the create is not the no-release branch with --draft under the dispatch's draft input")
    elif CREATE_ARGS not in lines[create + len(CREATE)].split():
        problems.append(f"the create does not pass {CREATE_ARGS}: a draft dispatch would publish a final release")
    if [line for line in lines if "--draft" in line and line != CREATE[2] and line != FINAL_EDIT[1]]:
        problems.append("--draft is passed outside the dispatch's draft input")
    refusal = next((number for number, line in enumerate(lines) if REFUSAL_CONDITION in line), -1)
    if refusal < 0:
        problems.append("a draft: true dispatch on a published release is not refused")
    else:
        echo, *after = lines[refusal + 1 : refusal + 5]
        if not (echo.startswith("echo ") and "$TAG" in echo and "published" in echo and echo.endswith(">&2")):
            problems.append("the refusal of a published release does not name the tag on stderr")
        if lines[refusal] != REFUSAL or after != ["exit 1", "else", REUPLOAD]:
            problems.append("the refusal does not exit 1 before the re-upload branch")
    if REUPLOAD not in lines:
        problems.append("the existing release is not re-uploaded with --clobber")
    final = find_run(lines, FINAL_EDIT)
    if final < 0:
        problems.append("the existing release is not made final with gh release edit <tag> --draft=false under 'not a draft'")
    order = [one_zip, view, create, refusal, lines.index(REUPLOAD) if REUPLOAD in lines else -1, final]
    if -1 not in order and order != sorted(order):
        problems.append(f"the release step's parts are out of order (one zip, view, create, refusal, upload, final): {order}")
    return problems


CHECKS: tuple[Callable[[str], list[str]], ...] = (
    check_triggers,
    check_jobs,
    check_tag_refusal,
    check_permissions,
    check_concurrency,
    check_actions_pinned,
    check_nothing_secret,
    check_version_from_manifest,
    check_suite_before_build,
    check_artifact_handover,
    check_release_lifecycle,
)


class TestTheWorkflowHolds(unittest.TestCase):
    def test_every_check_passes_on_the_real_file(self) -> None:
        text = workflow_text()
        for check in CHECKS:
            with self.subTest(check.__name__):
                self.assertEqual([], check(text))


class TestTheChecksRefuseVariants(unittest.TestCase):
    """In-memory variants of the real file: each check must see what it guards against."""

    def setUp(self) -> None:
        self.text = workflow_text()

    def variant(self, old: str, new: str) -> str:
        self.assertEqual(1, self.text.count(old), f"{old!r} must occur once to build the variant")
        return self.text.replace(old, new)

    def uses_line(self, action: str) -> str:
        lines = [line for line in self.text.splitlines() if f"uses: actions/{action}@" in line]
        self.assertEqual(1, len(lines))
        return lines[0]

    def test_a_uses_by_tag_is_refused(self) -> None:
        line = self.uses_line("checkout")
        text = self.variant(line, "      - uses: actions/checkout@v" + "7")
        self.assertTrue(check_actions_pinned(text))

    def test_a_third_party_owner_is_refused(self) -> None:
        line = self.uses_line("setup-python")
        text = self.variant(line, line.replace("actions/setup-python", "someone/setup-python"))
        self.assertTrue(check_actions_pinned(text))

    def test_a_job_without_the_guard_is_refused(self) -> None:
        for job in JOBS:
            with self.subTest(job):
                old = f"  {job}:\n{GUARD}\n"
                self.assertTrue(check_jobs(self.variant(old, f"  {job}:\n")))

    def test_a_job_without_the_tag_ref_refusal_is_refused(self) -> None:
        for job in JOBS:
            with self.subTest(job):
                block = job_blocks(self.text)[job]
                refusal = step_blocks(block)[0] + "\n"
                self.assertEqual(REFUSAL_STEP, step_name(refusal))
                self.assertTrue(check_tag_refusal(self.text.replace(block, block.replace(refusal, "", 1))))

    def test_a_refusal_that_does_not_exit_is_refused(self) -> None:
        text = self.text.replace("            exit 1\n", "            true\n", 1)
        self.assertNotEqual(self.text, text)
        self.assertTrue(check_tag_refusal(text))

    def test_contents_write_at_the_top_level_is_refused(self) -> None:
        text = self.variant("permissions:\n  contents: read\n\nconcurrency:", "permissions:\n  contents: write\n\nconcurrency:")
        self.assertTrue(check_permissions(text))

    def test_contents_write_in_kit_is_refused(self) -> None:
        text = self.variant("    timeout-minutes: 30\n", "    timeout-minutes: 30\n    permissions:\n      contents: write\n")
        self.assertTrue(check_permissions(text))

    def test_a_secrets_reference_is_refused(self) -> None:
        text = self.variant("          GH_TOKEN: ${{ github.token }}\n", "          GH_TOKEN: ${{ secrets.RELEASE_TOKEN }}\n")
        self.assertTrue(check_nothing_secret(text))

    def test_a_cache_is_refused(self) -> None:
        text = self.variant('          python-version: "3.11"\n', '          python-version: "3.11"\n          cache: pip\n')
        self.assertTrue(check_nothing_secret(text))

    def test_a_pull_request_trigger_is_refused(self) -> None:
        text = self.variant("  workflow_dispatch:\n", "  pull_request:\n  workflow_dispatch:\n")
        self.assertTrue(check_triggers(text))

    def test_publish_without_gh_repo_is_refused(self) -> None:
        text = self.variant("          GH_REPO: ${{ github.repository }}\n", "")
        self.assertTrue(check_release_lifecycle(text))

    def test_no_concurrency_group_is_refused(self) -> None:
        self.assertTrue(check_concurrency(self.variant(CONCURRENCY, "\n")))

    def test_a_cancelling_concurrency_group_is_refused(self) -> None:
        text = self.variant("  cancel-in-progress: false\n", "  cancel-in-progress: true\n")
        self.assertTrue(check_concurrency(text))

    def test_more_than_one_zip_is_not_caught_without_nullglob_and_the_count(self) -> None:
        for old in ("          shopt -s nullglob\n", '          if [ "${#zips[@]}" -ne 1 ]; then\n'):
            with self.subTest(old=old.strip()):
                self.assertTrue(check_release_lifecycle(self.variant(old, "")))

    def test_a_create_naming_the_glob_is_refused(self) -> None:
        text = self.variant('gh release create "$TAG" "${zips[@]}"', 'gh release create "$TAG" *.zip')
        self.assertTrue(check_release_lifecycle(text))

    def test_a_view_failure_taken_for_no_release_is_refused(self) -> None:
        text = self.variant('            cat "$err" >&2\n            exit 1\n', "            exists=false\n")
        self.assertIn("a failing gh release view is not told apart from 'release not found'", check_release_lifecycle(text))

    def test_the_old_view_that_swallows_every_error_is_refused(self) -> None:
        old = "\n".join(f"          {line}" if i in (0, 2, 4, 7) else f"            {line}" for i, line in enumerate(VIEW))
        new = '          if gh release view "$TAG" > /dev/null 2>&1; then\n            exists=true\n          else\n            exists=false\n          fi'
        self.assertTrue(check_release_lifecycle(self.variant(old, new)))

    def test_the_draft_path_without_draft_is_refused(self) -> None:
        text = self.variant("then create_args+=(--draft); fi", "then true; fi")
        self.assertTrue(check_release_lifecycle(text))

    def test_a_create_that_drops_the_draft_arguments_is_refused(self) -> None:
        text = self.variant('"${create_args[@]}" --verify-tag', "--verify-tag")
        self.assertIn(
            'the create does not pass "${create_args[@]}": a draft dispatch would publish a final release',
            check_release_lifecycle(text),
        )

    def test_an_unguarded_draft_flag_is_refused(self) -> None:
        text = self.variant('"${create_args[@]}" --verify-tag', '"${create_args[@]}" --draft --verify-tag')
        self.assertIn("--draft is passed outside the dispatch's draft input", check_release_lifecycle(text))

    def test_a_draft_create_outside_the_draft_input_is_refused(self) -> None:
        text = self.variant(DRAFT_ENV, "DRAFT: true")
        self.assertTrue(check_release_lifecycle(text))

    def test_no_refusal_of_a_published_release_is_refused(self) -> None:
        old = f"          {REFUSAL}\n"
        start = self.text.index(old)
        end = self.text.index("          else\n", start)
        text = self.text[:start] + self.text[end:]
        self.assertIn("a draft: true dispatch on a published release is not refused", check_release_lifecycle(text))

    def test_a_published_release_refusal_that_does_not_exit_is_refused(self) -> None:
        old = "Dispatch with draft: false to re-upload into it.\" >&2\n            exit 1\n"
        text = self.variant(old, old.replace("exit 1", "true"))
        self.assertIn("the refusal does not exit 1 before the re-upload branch", check_release_lifecycle(text))

    def test_a_refusal_that_does_not_name_the_tag_is_refused(self) -> None:
        text = self.variant("The release $TAG is already published", "The release is already published")
        self.assertIn("the refusal of a published release does not name the tag on stderr", check_release_lifecycle(text))

    def test_a_refusal_after_the_upload_is_refused(self) -> None:
        refusal_start = self.text.index(f"          {REFUSAL}\n")
        else_at = self.text.index("          else\n", refusal_start)
        refusal = self.text[refusal_start:else_at]
        upload = f"            {REUPLOAD}\n"
        text = self.text[:refusal_start] + self.text[else_at:]
        moved = refusal.replace("          elif", "            if", 1).replace("\n          ", "\n            ")
        text = text.replace(upload, upload + moved + "            fi\n", 1)
        self.assertNotEqual(self.text, text)
        problems = check_release_lifecycle(text)
        self.assertIn("the refusal does not exit 1 before the re-upload branch", problems)
        self.assertTrue(any(problem.startswith("the release step's parts are out of order") for problem in problems), problems)

    def test_no_draft_false_edit_is_refused(self) -> None:
        text = self.variant('gh release edit "$TAG" --draft=false', "true")
        self.assertTrue(check_release_lifecycle(text))

    def test_an_unguarded_draft_false_edit_is_refused(self) -> None:
        old = '            if [ "$DRAFT" != true ]; then\n              gh release edit "$TAG" --draft=false\n            fi\n'
        text = self.variant(old, '            gh release edit "$TAG" --draft=false\n')
        self.assertTrue(check_release_lifecycle(text))

    def test_no_clobber_re_upload_is_refused(self) -> None:
        text = self.variant(" SHA256SUMS --clobber\n", " SHA256SUMS\n")
        self.assertTrue(check_release_lifecycle(text))

    def test_an_upload_missing_sha256sums_is_refused(self) -> None:
        text = self.variant(REUPLOAD, REUPLOAD.replace(" SHA256SUMS", ""))
        self.assertTrue(check_release_lifecycle(text))

    def test_an_artifact_missing_sha256sums_is_refused(self) -> None:
        text = self.variant("            dist/colleague-kit/SHA256SUMS\n", "")
        self.assertTrue(check_artifact_handover(text))

    def test_a_version_literal_is_refused(self) -> None:
        old = "          cat dist/colleague-kit/SHA256SUMS\n"
        text = self.variant(old, old + "          echo 0." + "1.2\n")
        problems = check_version_from_manifest(text)
        self.assertEqual([f"{VERSION_LITERAL}: ['0." + "1.2']"], problems)

    def test_publish_without_needs_kit_is_refused(self) -> None:
        self.assertTrue(check_jobs(self.variant("    needs: kit\n", "")))


if __name__ == "__main__":
    unittest.main()
