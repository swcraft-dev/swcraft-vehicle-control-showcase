# The requirements team's Sphinx-Needs project (synthetic): its software requirements, in its own
# vocabulary, and the SWCraft architecture it loads from swcraft/needs.json. One conf for every
# delivery, given with -c and the delivery's version with -D:
#   sphinx-build -W -c demos/requirements-exchange/team -D version=1.0 -b needs \
#       demos/requirements-exchange/team/delivery-1.0 <out>
from pathlib import Path

project = "Vehicle control software requirements (synthetic)"
# Wide enough for a needs table of long ids beside the sidebar (the theme caps the page at 940px
# and the text at 800px).
html_theme_options = {"page_width": "1500px", "body_max_width": "none"}
extensions = ["sphinx_needs"]

# --- SWCraft's architecture: the need types, fields and link types its needs.json uses ---
needs_types = [
    # ... the project's own types (a project on the defaults lists req, spec, impl, test, need) ...
    {"directive": "arch_req", "title": "Architecture requirement", "prefix": "AR_"},
    {"directive": "arch_spec", "title": "Architecture specification", "prefix": "AS_"},
    {"directive": "arch_element", "title": "Architecture element", "prefix": "AE_"},
]
needs_fields = {
    "asil": {"description": "The safety integrity level allocated to the requirement.", "nullable": True},
    "swcraft_path": {
        "description": "The file in the SWCraft model that declares the need.", "nullable": True,
        "parse_dynamic_functions": False,
    },
}
needs_links = {
    "satisfies": {
        "outgoing": "satisfies", "incoming": "satisfied by",
        "parse_conditions": False, "parse_dynamic_functions": False,
    },
    "satisfies_unconfirmed": {
        "outgoing": "satisfies (unconfirmed)", "incoming": "satisfied by (unconfirmed)",
        "allow_dead_links": True, "parse_conditions": False, "parse_dynamic_functions": False,
    },
    "derived_from": {
        "outgoing": "derived from", "incoming": "derives",
        "parse_conditions": False, "parse_dynamic_functions": False,
    },
    "derived_from_unconfirmed": {
        "outgoing": "derived from (unconfirmed)", "incoming": "derives (unconfirmed)",
        "allow_dead_links": True, "parse_conditions": False, "parse_dynamic_functions": False,
    },
}
# A SWCraft need links into the showcase project open in the reader's VS Code, through the SWCraft
# extension: one address for every reader, whatever folder the project sits in, and no network.
needs_external_needs = [
    {
        "base_url": "",
        "target_url": "vscode://swcraft-local.swcraft-vscode/model?path={{need.swcraft_path | urlencode}}",
        "json_path": "swcraft/needs.json",
        "css_class": "swcraft",
    },
]
# --- end of SWCraft's declarations ---

# The team's own vocabulary, beside SWCraft's: its types, its fields and its parent link.
needs_types[0:0] = [
    {"directive": "swreq", "title": "Software requirement", "prefix": "SWR-", "color": "#BFD8D2", "style": "node"},
    {"directive": "sgoal", "title": "Safety goal", "prefix": "SG-", "color": "#FEDCD2", "style": "node"},
    {"directive": "test", "title": "Test case", "prefix": "TC-", "color": "#DCB239", "style": "node"},
]
needs_fields["safety"] = {"description": "The ASIL allocated to the requirement.", "nullable": True}
needs_fields["rev"] = {"description": "The requirement's revision in the team's tool.", "nullable": True}
needs_fields["document"] = {"description": "The specification the requirement belongs to.", "nullable": True}
# A safety goal's parent is the hazard analysis's, not the team's: a dead link the build allows.
needs_links["parent"] = {"description": "The requirement this one derives from.", "allow_dead_links": True}
# The team's ids hold `-` (SWR-BRK-001).
needs_id_regex = r"^[A-Z][A-Z0-9_-]{4,}$"
# No timestamps, so a rebuild of the same sources writes the same file.
needs_reproducible_json = True
# A delivery is the team's own build, made before any architecture was handed over, and
# Sphinx-Needs fails on a missing json_path: load SWCraft's file only once it is there, and
# only then show the page's section of the architecture (`.. only:: swcraft`).
if not (Path(__file__).parent / "swcraft" / "needs.json").is_file(): needs_external_needs = []
if (Path(__file__).parent / "swcraft" / "needs.json").is_file(): tags.add("swcraft")
