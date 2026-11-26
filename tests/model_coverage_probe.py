"""Report which kinds and fields of SWCraft's model contract this model carries.

Run under the interpreter of the SWCraft installation being tested -- never under
the interpreter that runs the tests -- because it imports ``swcraft_tools``, which
only that installation is known to have, and parses every element file with that
installation's own ``swcraft_tools.yaml_load.load_yaml_document`` (libyaml), the
reader SWCraft itself uses:

    <python> -I tests/model_coverage_probe.py <model_root>
        The coverage report, as one JSON object on stdout:
        ``contractVersion``, ``contractSource`` (``"installed"``, or ``"file"``
        under ``--contract-file``), ``swcraftVersion``, ``swcraftToolsPath``,
        ``rules`` (the contract's rule ids), ``unknown`` (every key of a model
        mapping that is not a field of the kind it was read as, as
        ``file: kind.key``), and ``kinds`` / ``fields``: every kind id and field
        id of the contract, each with the model files that carry it (an empty
        list when none does). Paths are POSIX and relative to the model root;
        ids are the contract's without their ``kind:`` / ``field:`` / ``rule:``
        prefix.

    <python> -I tests/model_coverage_probe.py <model_root> --contract-file PATH
        The same report against the contract JSON at PATH, read without the
        meta-schema check. For tests only: the production gate never passes it.

    <python> -I tests/model_coverage_probe.py --dump-contract
        The installed contract as JSON, so a test can derive a variant of it.

    <python> -I tests/model_coverage_probe.py --rules <model_root>
        ``{"records": [...]}``: the sorted set of rule ids SWCraft's cross-layer
        validator reports for the model -- the stable identity of a finding,
        never its message.

    <python> -I tests/model_coverage_probe.py --links <model_root>
        ``{"links": [...], "decisions": [...]}``: every ``satisfies`` list of the
        model, one entry per site -- ``{"site": {kind, owner, name}, "members":
        [...]}``, addressed as the trace link search addresses a target (``owner``
        the component of a port or a runnable, ``null`` otherwise), sorted -- and
        the records of ``trace-decisions.yaml`` beside the model root's parent
        (``[]`` without one), both read with SWCraft's own YAML reader.

What "carries" means: the element file holds the key. For the one placement
field (``swc.swc.group``) it means the element sits in a group directory; for a
member kind, that one member of that kind exists. A map or a list of strings is
a whole value and is not walked into.

What this does not reach: it reads only the files the contract's storage
declarations name (``*.yaml`` in each layer's directory, one level deeper for a
grouped layer), so a file elsewhere is neither counted nor reported; it checks
that a key is present, never that its value is valid -- that is
``swcraft check-model``'s job; and a list member or nested value that is not a
mapping is skipped rather than reported.

It is not a ``test*.py`` file, and it imports ``swcraft_tools`` only
inside the functions that need them, so the coverage gate imports it on any
Python to exercise :class:`Walk` on a hand-written contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


def bare(contract_id: str) -> str:
    """``kind:swc.port`` -> ``swc.port``."""
    return contract_id.split(":", 1)[1]


class Walk:
    """One walk of a model root against one contract."""

    def __init__(self, contract: dict[str, Any], model_root: Path) -> None:
        self.contract = contract
        self.model_root = model_root
        self.kinds: dict[str, list[str]] = {}
        self.fields: dict[str, list[str]] = {}
        self.unknown: list[str] = []
        # (layer name, kind name) -> the kind declaration
        self.kind_decls: dict[tuple[str, str], dict[str, Any]] = {}
        for layer in contract["layers"]:
            for kind in layer["kinds"]:
                self.kind_decls[(layer["name"], kind["kind"])] = kind
                self.kinds[bare(kind["id"])] = []
                for field in kind["fields"]:
                    self.fields[bare(field["id"])] = []

    @staticmethod
    def _mark(table: dict[str, list[str]], contract_id: str, rel: str) -> None:
        carriers = table[bare(contract_id)]
        if rel not in carriers:
            carriers.append(rel)

    def _files(self, layer: dict[str, Any]) -> list[Path]:
        storage = layer["storage"]
        directory = self.model_root / storage["directory"]
        if not directory.is_dir():
            return []
        suffix = storage.get("fileSuffix", ".yaml")
        pattern = f"*/*{suffix}" if storage.get("nesting") == "group" else f"*{suffix}"
        return sorted(
            (path for path in directory.glob(pattern) if path.is_file()),
            key=lambda path: path.as_posix(),
        )

    def _top_level_kind(self, layer: dict[str, Any], document: dict[str, Any]) -> dict[str, Any] | None:
        candidates = [kind for kind in layer["kinds"] if not kind["memberOnly"]]
        if len(candidates) == 1:
            return candidates[0]
        value = document.get("kind")
        for kind in candidates:
            for field in kind["fields"]:
                if field["name"] == "kind" and value in field.get("enum", ()):
                    return kind
        return None

    def _member_kind(self, layer_name: str, collection: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
        members = [self.kind_decls[(layer_name, name)] for name in collection.get("memberKinds", ())]
        if len(members) == 1:
            return members[0]
        discriminator = collection.get("discriminatorField")
        if discriminator is None:
            return None
        value = item.get(discriminator)
        for kind in members:
            for field in kind["fields"]:
                if field["name"] == discriminator and value in field.get("enum", ()):
                    return kind
        return None

    def _walk_mapping(self, layer_name: str, kind: dict[str, Any], mapping: dict[str, Any], rel: str) -> None:
        self._mark(self.kinds, kind["id"], rel)
        by_name = {field["name"]: field for field in kind["fields"]}
        for key, value in mapping.items():
            field = by_name.get(key)
            if field is None:
                self.unknown.append(f"{rel}: {bare(kind['id'])}.{key}")
                continue
            self._mark(self.fields, field["id"], rel)
            collection = field.get("collection")
            if collection is not None and collection.get("memberKinds") and isinstance(value, list):
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    member = self._member_kind(layer_name, collection, item)
                    if member is None:
                        self.unknown.append(f"{rel}: {bare(field['id'])}[?]")
                        continue
                    self._walk_mapping(layer_name, member, item, rel)
            elif "elementKind" in field and isinstance(value, dict):
                self._walk_mapping(layer_name, self.kind_decls[(layer_name, field["elementKind"])], value, rel)

    def run(self, load: Callable[[str], Any] | None = None) -> None:
        """Walk every element file; *load* parses one file's text.

        When ``None``, the installation's own ``load_yaml_document`` -- SWCraft's one
        YAML reader. The tests drive the walk on a Python without SWCraft by writing
        JSON -- which is YAML -- and passing ``json.loads``.
        """
        if load is None:
            from swcraft_tools.yaml_load import load_yaml_document

            load = load_yaml_document
        for layer in self.contract["layers"]:
            placement = layer.get("placement")
            for path in self._files(layer):
                rel = path.relative_to(self.model_root).as_posix()
                document = load(path.read_text(encoding="utf-8"))
                if not isinstance(document, dict):
                    self.unknown.append(f"{rel}: not a mapping")
                    continue
                kind = self._top_level_kind(layer, document)
                if kind is None:
                    self.unknown.append(f"{rel}: {layer['name']}.kind={document.get('kind')!r}")
                    continue
                self._walk_mapping(layer["name"], kind, document, rel)
                if placement is not None and layer["storage"].get("nesting") == "group":
                    for field in kind["fields"]:
                        if field.get("placement"):
                            self._mark(self.fields, field["id"], rel)


def coverage(contract: dict[str, Any], source: str, model_root: Path) -> dict[str, Any]:
    import swcraft_tools
    from swcraft_tools._version import __version__

    walk = Walk(contract, model_root)
    walk.run()
    return {
        "contractVersion": contract["contractVersion"],
        "contractSource": source,
        "swcraftVersion": __version__,
        "swcraftToolsPath": Path(swcraft_tools.__file__).as_posix(),
        "rules": sorted(bare(rule["id"]) for rule in contract["rules"]),
        "unknown": walk.unknown,
        "kinds": walk.kinds,
        "fields": walk.fields,
    }


def rules(model_root: Path) -> dict[str, Any]:
    from swcraft_tools.validator import check_cross_layer_consistency

    result = check_cross_layer_consistency(str(model_root))
    return {"records": sorted({record.rule for record in result.records})}


#: The site kind of a top-level element, by its layer directory; a hardware element
#: names its own (``kind: core`` and so on).
SITE_KINDS = {"swc": "swc", "interfaces": "interface", "compositions": "composition", "tasks": "task"}


def links(model_root: Path) -> dict[str, Any]:
    from swcraft_tools.yaml_load import load_yaml_document

    sites: list[dict[str, Any]] = []

    def add(kind: str, owner: str | None, name: str, element: dict[str, Any]) -> None:
        members = element.get("satisfies")
        if members:
            sites.append({"site": {"kind": kind, "owner": owner, "name": name}, "members": list(members)})

    for path in sorted(model_root.rglob("*.yaml"), key=lambda path: path.as_posix()):
        layer = path.relative_to(model_root).parts[0]
        document = load_yaml_document(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            continue
        if layer == "hardware":
            add(document["kind"], None, document["name"], document)
        elif layer in SITE_KINDS:
            add(SITE_KINDS[layer], None, document["name"], document)
        if layer == "swc":
            for member_kind, collection in (("port", "ports"), ("runnable", "runnables")):
                for member in document.get(collection) or ():
                    add(member_kind, document["name"], member["name"], member)
    sites.sort(key=lambda entry: json.dumps(entry["site"], sort_keys=True))
    decisions_file = model_root.parent / "trace-decisions.yaml"
    decisions: list[Any] = []
    if decisions_file.is_file():
        decisions = (load_yaml_document(decisions_file.read_text(encoding="utf-8")) or {}).get("decisions") or []
    return {"links": sites, "decisions": decisions}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("model_root", nargs="?", type=Path)
    parser.add_argument("--contract-file", type=Path)
    parser.add_argument("--dump-contract", action="store_true")
    parser.add_argument("--rules", dest="rules_root", type=Path)
    parser.add_argument("--links", dest="links_root", type=Path)
    args = parser.parse_args(argv)

    if args.dump_contract:
        from swcraft_tools.contract import load_contract

        result: dict[str, Any] = load_contract()
    elif args.rules_root is not None:
        result = rules(args.rules_root)
    elif args.links_root is not None:
        result = links(args.links_root)
    elif args.model_root is not None:
        if args.contract_file is not None:
            contract = json.loads(args.contract_file.read_text(encoding="utf-8"))
            source = "file"
        else:
            from swcraft_tools.contract import load_contract

            contract = load_contract()
            source = "installed"
        result = coverage(contract, source, args.model_root)
    else:
        parser.error("name a model root, --rules <model_root>, --links <model_root> or --dump-contract")
    # ASCII only, so the reader's decoding cannot matter.
    sys.stdout.write(json.dumps(result, sort_keys=True, ensure_ascii=True))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
