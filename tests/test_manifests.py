"""
The marketplace's and the plugin's manifests: their required fields, and the marketplace's entry for the plugin.
"""

import copy
from pathlib import Path
from typing import Any, Callable, Dict

import pytest

from skill_repo import MARKETPLACE, PLUGIN_MANIFEST, ROOT, CheckError, check_marketplace, check_plugin, load_json


def _marketplace() -> Dict[str, Any]:
    return load_json(MARKETPLACE)


def test_the_marketplace_is_valid() -> None:
    """The marketplace has a name, an owner and the plugin, whose source is the plugin in this repository."""
    check_marketplace(_marketplace(), ROOT)


def test_the_names_are_ih_172s() -> None:
    """The marketplace is loopproof-agent, and its one plugin loopproof, as the README's commands name them."""
    marketplace = _marketplace()
    assert marketplace["name"] == "loopproof-agent"
    assert [entry["name"] for entry in marketplace["plugins"]] == ["loopproof"]
    assert marketplace["owner"]["name"] == "InfraHouse"


def test_the_entry_names_the_plugin_as_its_manifest_does() -> None:
    """The marketplace's entry and plugin.json give the plugin the same name."""
    entry = _marketplace()["plugins"][0]
    assert load_json(ROOT / entry["source"] / ".claude-plugin" / "plugin.json")["name"] == entry["name"]


def test_the_plugin_is_valid() -> None:
    """plugin.json has its name, and its other fields are of the types the reference gives."""
    check_plugin(load_json(PLUGIN_MANIFEST))


def test_neither_manifest_carries_a_version() -> None:
    """Users track main's commits: a version in either file would hold them at it until someone bumps it."""
    assert "version" not in load_json(PLUGIN_MANIFEST)
    assert all("version" not in entry for entry in _marketplace()["plugins"])


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda m: m.pop("name"), "marketplace's name"),
        (lambda m: m.update(name="LoopProof Agent"), "marketplace's name"),
        (lambda m: m.update(name="claude-loopproof"), "reserved word"),
        (lambda m: m.pop("owner"), "owner"),
        (lambda m: m["owner"].pop("name"), "owner"),
        (lambda m: m.update(plugins=[]), "list of plugins"),
        (lambda m: m["plugins"].append(copy.deepcopy(m["plugins"][0])), "twice"),
        (lambda m: m["plugins"][0].update(name="loopproof-connector"), "differs"),
        (lambda m: m["plugins"][0].update(source="plugins/loopproof"), "path in the repository"),
        (lambda m: m["plugins"][0].update(source="./plugins/../plugins/loopproof"), "path in the repository"),
        (lambda m: m["plugins"][0].update(source="./plugins/nothing"), "no .claude-plugin/plugin.json"),
    ],
    ids=[
        "no name",
        "a name with spaces",
        "a reserved word",
        "no owner",
        "an owner without a name",
        "no plugins",
        "a plugin twice",
        "another name than plugin.json's",
        "a source not from ./",
        "a source through ..",
        "a source with no plugin",
    ],
)
def test_a_wrong_marketplace_fails(change: Callable[[Dict[str, Any]], Any], message: str) -> None:
    """Each required field missing or wrong fails the check, naming what is wrong."""
    marketplace = _marketplace()
    change(marketplace)
    with pytest.raises(CheckError, match=message):
        check_marketplace(marketplace, ROOT)


def test_a_version_in_both_manifests_fails(tmp_path: Path) -> None:
    """Claude Code's documentation warns against a version in both files: they can disagree."""
    plugin = tmp_path / "plugins" / "loopproof" / ".claude-plugin"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text('{"name": "loopproof", "version": "1"}', encoding="utf-8")
    marketplace = _marketplace()
    marketplace["plugins"][0]["version"] = "1"
    with pytest.raises(CheckError, match="version in both"):
        check_marketplace(marketplace, tmp_path)


@pytest.mark.parametrize(
    "plugin, message",
    [
        ({}, "plugin's name"),
        ({"name": "Loop Proof"}, "plugin's name"),
        ({"name": "loopproof", "description": 1}, "description"),
        ({"name": "loopproof", "author": "InfraHouse"}, "author"),
    ],
    ids=["no name", "a name with a space", "a description that isn't text", "an author that isn't an object"],
)
def test_a_wrong_plugin_fails(plugin: Dict[str, Any], message: str) -> None:
    """A plugin.json without its name, or with a field of the wrong type, fails."""
    with pytest.raises(CheckError, match=message):
        check_plugin(plugin)


def test_a_manifest_that_isnt_json_fails(tmp_path: Path) -> None:
    """A manifest that doesn't parse is a failure, not an empty manifest."""
    path = tmp_path / "plugin.json"
    path.write_text("{name: loopproof}", encoding="utf-8")
    with pytest.raises(CheckError, match="isn't JSON"):
        load_json(path)
