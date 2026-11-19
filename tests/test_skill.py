"""
The skill: its frontmatter within the documented limits, its body's length, and its reference files, each loaded
from SKILL.md.
"""

from typing import Any, Dict

import pytest

from skill_repo import (
    REFERENCES,
    SKILL,
    SKILL_DESCRIPTION_MAX,
    SKILL_DIR,
    SKILL_NAME_MAX,
    CheckError,
    check_body,
    check_frontmatter,
    links_in,
    local_target,
    split_frontmatter,
)

VALID = {"name": "connector", "description": "Installs LoopProof's connector."}


def test_the_frontmatter_is_within_the_limits() -> None:
    """name and description within the Agent Skills specification's and Claude Code's limits, and no other field."""
    meta, _ = split_frontmatter(SKILL.read_text(encoding="utf-8"))
    check_frontmatter(meta, SKILL_DIR.name)


def test_the_skill_is_connector() -> None:
    """The skill is named connector, so Claude Code runs it as /loopproof:connector."""
    meta, _ = split_frontmatter(SKILL.read_text(encoding="utf-8"))
    assert meta["name"] == "connector"


def test_the_description_says_when_to_load_it() -> None:
    """The description names what makes an agent load the skill: the install, onboarding and the work after go-live."""
    meta, _ = split_frontmatter(SKILL.read_text(encoding="utf-8"))
    description = meta["description"].lower()
    for words in ("loopproof's connector", "onboarding", "go-live", "upgrade", "accept rule", "rotation"):
        assert words in description, words


def test_the_body_is_within_its_length() -> None:
    """SKILL.md's body stays under the 500 lines the specification recommends."""
    _, body = split_frontmatter(SKILL.read_text(encoding="utf-8"))
    check_body(body)


def test_the_rules_come_before_the_steps() -> None:
    """The body's first section is the rules, before the install's steps."""
    _, body = split_frontmatter(SKILL.read_text(encoding="utf-8"))
    sections = [line for line in body.splitlines() if line.startswith("## ")]
    assert sections[0] == "## The rules"
    assert sections.index("## The rules") < sections.index("## The install")


def test_skill_md_loads_every_reference_file() -> None:
    """Every file in references/ is linked from SKILL.md, one level deep: an agent loads it when a step needs it."""
    linked = set()
    for link in links_in(SKILL.read_text(encoding="utf-8")):
        found = local_target(SKILL, link.target)
        if found is not None:
            linked.add(found[0].resolve())
    references = {path.resolve() for path in REFERENCES.glob("*.md")}
    assert references, "no reference files"
    assert references <= linked, sorted(path.name for path in references - linked)


def test_no_reference_file_is_nested() -> None:
    """The reference files sit in one directory beside SKILL.md, with nothing below it."""
    assert all(path.is_file() and path.suffix == ".md" for path in REFERENCES.iterdir())


@pytest.mark.parametrize(
    "change, message",
    [
        ({"name": None}, "1 to 64"),
        ({"name": "x" * (SKILL_NAME_MAX + 1)}, "1 to 64"),
        ({"name": "Connector"}, "lowercase"),
        ({"name": "connector--two"}, "lowercase"),
        ({"name": "-connector"}, "lowercase"),
        ({"name": "claude-connector"}, "reserved word"),
        ({"name": "install"}, "directory"),
        ({"description": ""}, "1 to 1024"),
        ({"description": "x" * (SKILL_DESCRIPTION_MAX + 1)}, "1 to 1024"),
        ({"description": "Installs <b>the</b> connector."}, "XML tag"),
        ({"argument-hint": "[account]"}, "specification doesn't"),
    ],
    ids=[
        "no name",
        "a name too long",
        "a capital",
        "two hyphens in a row",
        "a hyphen first",
        "a reserved word",
        "another name than its directory's",
        "an empty description",
        "a description too long",
        "an XML tag",
        "a field only Claude Code reads",
    ],
)
def test_a_wrong_frontmatter_fails(change: Dict[str, Any], message: str) -> None:
    """Each limit broken fails the check, naming it."""
    meta = {**VALID, **change}
    with pytest.raises(CheckError, match=message):
        check_frontmatter({key: value for key, value in meta.items() if value is not None}, "connector")


@pytest.mark.parametrize(
    "text, message",
    [
        ("# Connector\n", "frontmatter block"),
        ("---\nname: [connector\n---\nbody\n", "isn't YAML"),
        ("---\n- connector\n---\nbody\n", "mapping"),
    ],
    ids=["no frontmatter", "frontmatter that isn't YAML", "frontmatter that isn't a mapping"],
)
def test_a_wrong_skill_file_fails(text: str, message: str) -> None:
    """A SKILL.md without frontmatter, or whose frontmatter isn't a YAML mapping, fails."""
    with pytest.raises(CheckError, match=message):
        split_frontmatter(text)


def test_a_body_too_long_fails() -> None:
    """A body of 501 lines is over the specification's 500."""
    with pytest.raises(CheckError, match="over 500"):
        check_body("line\n" * 501)


def test_an_empty_body_fails() -> None:
    """A skill with frontmatter alone tells an agent nothing."""
    with pytest.raises(CheckError, match="empty"):
        check_body("\n\n")
