# The colleague kit

`scripts/build_colleague_kit.py` packages this showcase as **one zip** a colleague can
unpack next to an installed SWCraft toolchain: the manifest pinned to one SWCraft
release, the model, the editor settings, the Copilot agent profile and the
model-guard hook from this repository's own `.github/`, Kiro's MCP server settings, steering file
and model-guard hook from its `.kiro/`, the trace link search's
configuration (`experiments/trace.yaml`), the demonstrations in the order the install page takes them
(`demos/README.md` lists them so):

1. the diagrams in a VS Code tab, a section of `demos/README.md` (the kit carries no diagrams: the
   colleague generates them);
2. the chat with the model in Copilot and Kiro (`demos/chat-with-the-model.md`);
3. the rejected changes, a section of `demos/README.md` with `demos/rejected-changes.json`: the edits
   the build refuses, each with its rule;
4. the test tables (`demos/test-tables.md`, with the test team's annotations folder
   `demos/test-tables/annotations/`, which the editor settings name);
5. the requirements exchange (`demos/requirements-exchange.md`, with its files under
   `demos/requirements-exchange/`: the architect's mapping, the answer key, the prepared links, the
   requirements team's two deliveries, its Sphinx project and its four ready-made sites — three beside
   the needs file each was built from, and delivery 1.0 as the team built it before the handover — and the public copy of its presentation,
   `demos/requirements-exchange-presentation-public.html` — the sites and the prepared links are most
   of the zip, nearly two thirds of its bytes, the cost of a demonstration that needs no Sphinx);

and the install page
(`docs/guide/install-on-a-workstation.md`) as its `README.md`. It also carries `LICENSE`, `NOTICE` and
`THIRD-PARTY-NOTICES.md`: the showcase's licence, and the licences of the third-party code its sites and
presentation carry (Sphinx and its theme and extensions, the Snowball stemmers, Pygments' style, jQuery,
Marp). Nothing in the zip needs git, moon, Node or a network, except building the requirements
team's Sphinx site yourself (optional: the kit carries it ready-made), which needs Python 3.11 or
later and `pip` access to PyPI for the team's tool.

The repository and the kit are at the same SWCraft release, so the kit carries the
repository's files verbatim wherever it can. `overlay/` holds only what the kit ships
**instead of** a repository copy:

| File | Why the kit has its own |
|---|---|
| `.github/copilot-instructions.md` | Identical to the root copy except the *Building* section: the kit ships no `moon.yml`, so it names `swcraft validate` as the gate rather than `moon run :build`. |
| `.gitignore` | Based on the pinned release's project template `.gitignore`, plus `schemas/` (the licensed XSD) and the requirements team's copy of the architecture. |

What the kit deliberately leaves out is asserted by name in
`tests/test_build_colleague_kit.py`: the moon build graph and its pins, the setup
launchers, the tests, the scripts that generate the requirements team's sources, the prepared files and the test team's
annotations, the team's copy of the
architecture (`demos/requirements-exchange/team/swcraft/`), the generated outputs, the evidence and the licensed schema.
