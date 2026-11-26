"""What the kit builder and the two generators agree on: the pin's parser and the names no output holds.

A leaf: stdlib only, and it imports none of the repository's scripts. The kit builder
(``scripts/build_colleague_kit.py``, which the CI runner runs with no SWCraft and which
re-exports :func:`parse_toolchain_version` for the verify workflow), the shared pin check
(``scripts/pinned_swcraft.py``) and the two generators import it, so none of them depends on
another's job. Maintainer tooling, not a kit member.
"""

from __future__ import annotations

import re

#: One exact release, ``X.Y.Z``: what a pin and ``--swcraft-version`` must be.
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
TOOLCHAIN_RE = re.compile(r'^toolchain_version:\s*"?([^"\s#]+)"?\s*(?:#.*)?$')

#: Operating-system litter: never shipped from a site folder, and neither generator compares
#: nor writes these names.
IGNORED_NAMES = (".DS_Store", "Thumbs.db")
#: Sphinx's bookkeeping no reader opens: the incremental build's record and Sphinx-Needs'
#: validation report, which holds the build's timing. The requirements exchange's generator
#: leaves these files out of a site, and the kit refuses them in a site folder (``.buildinfo``
#: is a dotfile as well, which the kit refuses anyway; the generator needs it named).
SITE_REFUSED_NAMES = (".buildinfo", "schema_violations.json")


class ManifestError(RuntimeError):
    """``swcraft.yaml`` does not pin one exact release; the message is printed as it is."""


def parse_toolchain_version(text: str) -> str:
    """Return the one exact SWCraft release a ``swcraft.yaml`` text pins.

    The verify workflow asks this (through the kit builder) for ``--swcraft-version``, so
    the release a kit is pinned to is read from the manifest and written nowhere else.
    """
    versions = [match.group(1) for line in text.splitlines() if (match := TOOLCHAIN_RE.match(line))]
    if not versions:
        raise ManifestError("swcraft.yaml declares no toolchain_version")
    if len(versions) > 1:
        raise ManifestError("swcraft.yaml declares toolchain_version more than once")
    version = versions[0]
    if not VERSION_RE.match(version):
        raise ManifestError(
            f"toolchain_version must be one exact release such as 0.7.0, not {version!r}: "
            "the project pins a version, never a range"
        )
    return version
