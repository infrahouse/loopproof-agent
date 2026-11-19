"""
Links between the README, SKILL.md, its reference files and the tests' README: each leads to a file of the
repository, and to a heading in it when it names one. The README's section for agents reaches every file of the skill.
"""

from pathlib import Path

import pytest

from skill_repo import (
    README,
    REFERENCES,
    SKILL,
    CheckError,
    Link,
    anchors_in,
    check_link,
    github_anchor,
    links_in,
    local_target,
    markdown_files,
    relative,
    section_links,
)


@pytest.mark.parametrize("path", markdown_files(), ids=relative)
def test_every_link_resolves(path: Path) -> None:
    """A link into the repository, relative or by its GitHub or raw URL, leads to a file, and to its heading."""
    for link in links_in(path.read_text(encoding="utf-8")):
        check_link(path, link)


def test_the_readme_sends_an_agent_to_every_file_of_the_skill() -> None:
    """From the README's section for agents alone, an agent reaches SKILL.md and each reference file on GitHub."""
    targets = section_links(README.read_text(encoding="utf-8"), "### If you are an AI agent")
    reached = set()
    for target in targets:
        if target.startswith("https://github.com/infrahouse/loopproof-agent/"):
            reached.add(local_target(README, target)[0].resolve())
    expected = {SKILL.resolve(), *(path.resolve() for path in REFERENCES.glob("*.md"))}
    assert expected <= reached, sorted(relative(path) for path in expected - reached)


def test_a_section_with_an_undefined_reference_fails() -> None:
    """A reference-style link with no definition is a broken link on GitHub."""
    with pytest.raises(CheckError, match="defined nowhere"):
        section_links("## A\n[SKILL.md][skill]\n", "## A")


@pytest.mark.parametrize(
    "heading, anchor",
    [
        ("The rules", "the-rules"),
        ("1. Get the two parts", "1-get-the-two-parts"),
        ("The machine can't reach LoopProof", "the-machine-cant-reach-loopproof"),
        ("What `rules` does", "what-rules-does"),
        ("Accept rules, tenant settings", "accept-rules-tenant-settings"),
    ],
)
def test_anchors_are_githubs(heading: str, anchor: str) -> None:
    """A heading's anchor is the one GitHub makes."""
    assert github_anchor(heading) == anchor


def test_a_repeated_heading_gets_a_number() -> None:
    """GitHub numbers a heading's anchor from its second time."""
    assert anchors_in("# A\n## A\n### A\n") == ["a", "a-1", "a-2"]


def test_headings_in_code_are_none() -> None:
    """A line starting with # in a code block is a comment, not a heading."""
    assert anchors_in("# Real\n```bash\n# not a heading\n```\n") == ["real"]


@pytest.mark.parametrize(
    "target, message",
    [
        ("references/nowhere.md", "no file"),
        ("references/the-plan.md#nowhere", "no heading"),
        ("../../../../../outside.md", "no file"),
        ("https://github.com/infrahouse/loopproof-agent/blob/main/plugins/nowhere.md", "no file"),
        ("https://raw.githubusercontent.com/infrahouse/loopproof-agent/main/LICENSE#top", "no Markdown file"),
        ("#nowhere", "no heading"),
    ],
    ids=["a missing file", "a missing heading", "out of the repository", "a GitHub URL", "an anchor in a file", "here"],
)
def test_a_broken_link_fails(target: str, message: str) -> None:
    """A link to a missing file, outside the repository, or to a missing heading fails, naming it."""
    with pytest.raises(CheckError, match=message):
        check_link(SKILL, Link(1, target))


def test_links_out_of_the_repository_are_left_alone() -> None:
    """Other sites' links aren't fetched: the checks run without the network."""
    check_link(SKILL, Link(1, "https://docs.aws.amazon.com/nowhere"))
    assert local_target(SKILL, "mailto:someone@example.com") is None


def test_links_in_code_are_none() -> None:
    """A link in a code span or a code block is text, not a link."""
    text = "`[a](nowhere.md)`\n```\n[b](nowhere.md)\n```\n[c](here.md)\n"
    assert [link.target for link in links_in(text)] == ["here.md"]
