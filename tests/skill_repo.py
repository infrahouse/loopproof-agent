"""
What the checks read and hold the repository to: its files, the manifests, the skill's frontmatter, Markdown's links
and headings, and what no file may hold.

Each ``check_*`` function raises :class:`CheckError`, naming what is wrong, and returns nothing when all is well. Each
``*_in`` function returns what it finds, for a test to compare with nothing. The tests run both on the repository and
on samples that must fail.
"""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN = ROOT / "plugins" / "loopproof"
PLUGIN_MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"
SKILL_DIR = PLUGIN / "skills" / "connector"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"
README = ROOT / "README.md"
FIXTURES = ROOT / "tests" / "fixtures"

GITHUB_BLOB = "https://github.com/infrahouse/loopproof-agent/blob/main/"
GITHUB_TREE = "https://github.com/infrahouse/loopproof-agent/tree/main/"
GITHUB_RAW = "https://raw.githubusercontent.com/infrahouse/loopproof-agent/main/"

LINE_LIMIT = 120
"""The coding standard's limit, for every file but those a tool writes."""

GENERATED = ("ci/package-lock.json",)
"""Files a tool writes, which the line limit leaves alone."""

MANAGED = (
    ".claude/CODING_STANDARD.md",
    ".claude/instructions.md",
    ".github/workflows/vuln-scanner-pr.yml",
    "renovate.json",
)
"""Files infrahouse/github-control writes and overwrites, which this repository can't change: no check reads them."""

DOCUMENTATION_ACCOUNT_IDS = frozenset({"111122223333", "444455556666", "777788889999", "123456789012"})
"""The only account ids any file may hold: AWS's documentation examples."""

SKILL_NAME_MAX = 64
SKILL_DESCRIPTION_MAX = 1024
SKILL_BODY_MAX_LINES = 500
SKILL_FIELDS = frozenset({"name", "description", "license", "compatibility", "metadata", "allowed-tools"})
"""The Agent Skills specification's frontmatter fields: a skill with only these loads in any agent that follows it."""
RESERVED_WORDS = ("anthropic", "claude")
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
"""A plugin's, a marketplace's or a skill's name: lowercase letters and digits, single hyphens between them."""


class CheckError(Exception):
    """A file breaks a rule of the repository's."""


@dataclass(frozen=True)
class Link:
    """A link in a Markdown file, and the line it is on."""

    line: int
    target: str


# --- The repository's files ---


def repository_files() -> List[Path]:
    """
    Every file git tracks or would track: the working tree but what ``.gitignore`` leaves out.

    :return: the files' paths, sorted
    """
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(ROOT / name for name in listed.split("\0") if name and (ROOT / name).is_file())


def text_files() -> List[Path]:
    """
    The repository's files that are text, as UTF-8, but those github-control manages.

    :return: their paths, sorted
    """
    texts = []
    for path in repository_files():
        if relative(path) in MANAGED:
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        texts.append(path)
    return texts


def markdown_files() -> List[Path]:
    """
    The repository's Markdown files, the fixtures' included.

    :return: their paths, sorted
    """
    return [path for path in text_files() if path.suffix == ".md"]


def relative(path: Path) -> str:
    """
    A path as the repository names it.

    :param path: a path, inside the repository or not
    :return: the path from the repository's root, with forward slashes, or as it is outside the repository
    """
    if path.resolve().is_relative_to(ROOT):
        return path.resolve().relative_to(ROOT).as_posix()
    return str(path)


# --- The manifests ---


def load_json(path: Path) -> Dict[str, Any]:
    """
    A JSON object from a file.

    :param path: the file
    :return: the object
    :raises CheckError: if the file isn't a JSON object
    """
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CheckError(f"{relative(path)} isn't JSON: {error}") from error
    if not isinstance(value, dict):
        raise CheckError(f"{relative(path)} isn't a JSON object")
    return value


def check_name(name: Any, what: str) -> None:
    """
    A marketplace's, a plugin's or a skill's name.

    :param name: the name
    :param what: what it names, for the message
    :raises CheckError: if it isn't kebab-case, or holds a reserved word
    """
    if not isinstance(name, str) or not NAME_PATTERN.match(name):
        raise CheckError(f"{what} must be lowercase letters and digits with single hyphens between them: {name!r}")
    for word in RESERVED_WORDS:
        if word in name:
            raise CheckError(f"{what} must not hold the reserved word {word!r}: {name!r}")


def check_marketplace(marketplace: Dict[str, Any], root: Path) -> None:
    """
    The marketplace's manifest, as Claude Code's marketplace reference requires it.

    :param marketplace: ``.claude-plugin/marketplace.json``'s object
    :param root: the marketplace's root, from which a plugin's relative source resolves
    :raises CheckError: if a required field is missing or wrong, or a plugin's source isn't a plugin in the repository
    """
    check_name(marketplace.get("name"), "the marketplace's name")
    owner = marketplace.get("owner")
    if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner["name"]:
        raise CheckError("the marketplace needs an owner with a name")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        raise CheckError("the marketplace needs a list of plugins")
    names = [entry.get("name") if isinstance(entry, dict) else None for entry in plugins]
    if len(set(names)) != len(names):
        raise CheckError(f"the marketplace lists a plugin twice: {names}")
    for entry in plugins:
        if not isinstance(entry, dict):
            raise CheckError("each of the marketplace's plugins must be an object")
        check_name(entry.get("name"), "a plugin's name")
        source = entry.get("source")
        if not isinstance(source, str) or not source.startswith("./") or ".." in source.split("/"):
            raise CheckError(f"plugin {entry['name']!r}: its source must be a path in the repository, from ./")
        manifest = root / source / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            raise CheckError(f"plugin {entry['name']!r}: {source} has no .claude-plugin/plugin.json")
        plugin = load_json(manifest)
        if plugin.get("name") != entry["name"]:
            raise CheckError(
                f"plugin {entry['name']!r}: the marketplace's name for it differs from its plugin.json's,"
                f" {plugin.get('name')!r}"
            )
        if "version" in entry and "version" in plugin:
            raise CheckError(f"plugin {entry['name']!r}: a version in both the marketplace and plugin.json")


def check_plugin(plugin: Dict[str, Any]) -> None:
    """
    A plugin's manifest, as Claude Code's plugins reference requires it.

    :param plugin: ``plugin.json``'s object
    :raises CheckError: if its name is missing or wrong, or a field has the wrong type
    """
    check_name(plugin.get("name"), "the plugin's name")
    for field in ("description", "homepage", "repository", "license"):
        if field in plugin and not isinstance(plugin[field], str):
            raise CheckError(f"the plugin's {field} must be a string")
    author = plugin.get("author")
    if author is not None and (not isinstance(author, dict) or not isinstance(author.get("name"), str)):
        raise CheckError("the plugin's author must be an object with a name")


# --- The skill's frontmatter ---


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """
    A ``SKILL.md``'s frontmatter and body.

    :param text: the file's text
    :return: the frontmatter, as YAML reads it, and the body after it
    :raises CheckError: if the file doesn't start with a frontmatter block of YAML
    """
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    if not match:
        raise CheckError("SKILL.md must start with a frontmatter block between two lines of ---")
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise CheckError(f"SKILL.md's frontmatter isn't YAML: {error}") from error
    if not isinstance(meta, dict):
        raise CheckError("SKILL.md's frontmatter must be a mapping")
    return meta, match.group(2)


def check_frontmatter(meta: Dict[str, Any], directory: str) -> None:
    """
    A skill's frontmatter, within the limits of the Agent Skills specification and Claude Code's documentation.

    :param meta: the frontmatter
    :param directory: the name of the skill's directory, which its name must equal
    :raises CheckError: naming the first field that breaks a limit
    """
    unknown = sorted(set(meta) - SKILL_FIELDS)
    if unknown:
        raise CheckError(f"SKILL.md's frontmatter has fields the specification doesn't: {unknown}")
    name = meta.get("name")
    if not isinstance(name, str) or not 1 <= len(name) <= SKILL_NAME_MAX:
        raise CheckError(f"the skill's name must be 1 to {SKILL_NAME_MAX} characters: {name!r}")
    check_name(name, "the skill's name")
    if name != directory:
        raise CheckError(f"the skill's name, {name!r}, must equal its directory's, {directory!r}")
    description = meta.get("description")
    if not isinstance(description, str) or not 1 <= len(description) <= SKILL_DESCRIPTION_MAX:
        length = len(description) if isinstance(description, str) else None
        raise CheckError(f"the skill's description must be 1 to {SKILL_DESCRIPTION_MAX} characters, not {length}")
    if re.search(r"<[^>]*>", description):
        raise CheckError("the skill's description must hold no XML tag")


def check_body(body: str) -> None:
    """
    A skill's body, after its frontmatter.

    :param body: the body
    :raises CheckError: if it is empty or longer than the specification recommends
    """
    lines = body.splitlines()
    if not body.strip():
        raise CheckError("SKILL.md's body is empty")
    if len(lines) > SKILL_BODY_MAX_LINES:
        raise CheckError(f"SKILL.md's body is {len(lines)} lines, over {SKILL_BODY_MAX_LINES}")


# --- Markdown ---


def _prose_lines(text: str) -> Iterable[Tuple[int, str]]:
    """
    A Markdown file's lines outside fenced code blocks, with their numbers, code spans blanked.

    :param text: the file's text
    :return: each line's number, from 1, and its text
    """
    fence: Optional[str] = None
    for number, line in enumerate(text.splitlines(), start=1):
        opening = re.match(r"^\s*(```+|~~~+)", line)
        if fence is None and opening:
            fence = opening.group(1)
            continue
        if fence is not None:
            if line.strip().startswith(fence):
                fence = None
            continue
        yield number, re.sub(r"`[^`]*`", "``", line)


def code_blocks(text: str) -> List[Tuple[int, str]]:
    """
    A Markdown file's fenced code blocks.

    :param text: the file's text
    :return: each block's first line number and its lines, joined
    """
    blocks = []
    current: Optional[List[str]] = None
    start = 0
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        opening = re.match(r"^\s*(```+|~~~+)", line)
        if current is None and opening:
            current, start, fence = [], number + 1, opening.group(1)
        elif current is not None and line.strip().startswith(fence):
            blocks.append((start, "\n".join(current)))
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def links_in(text: str) -> List[Link]:
    """
    The links of a Markdown file, inline and reference definitions, outside code.

    :param text: the file's text
    :return: each link, with its line
    """
    links = []
    for number, line in _prose_lines(text):
        definition = re.match(r"^\s{0,3}\[[^\]]+\]:\s+(\S+)", line)
        if definition:
            links.append(Link(number, definition.group(1)))
            continue
        for match in re.finditer(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            links.append(Link(number, match.group(1)))
    return links


def section_links(text: str, heading: str) -> List[str]:
    """
    The targets of the links in one section of a Markdown file, inline or by a reference defined anywhere in it.

    :param text: the file's text
    :param heading: the section's heading line, such as ``### If you are an AI agent``
    :return: the targets, in order
    :raises CheckError: if the file has no such section, or a reference in it is defined nowhere
    """
    lines = text.splitlines()
    if heading not in lines:
        raise CheckError(f"no section {heading!r}")
    level = len(heading) - len(heading.lstrip("#"))
    start = lines.index(heading) + 1
    end = next(
        (i for i in range(start, len(lines)) if re.match(rf"^#{{1,{level}}}\s", lines[i])),
        len(lines),
    )
    definitions = {}
    for _, line in _prose_lines(text):
        definition = re.match(r"^\s{0,3}\[([^\]]+)\]:\s+(\S+)", line)
        if definition:
            definitions[definition.group(1).lower()] = definition.group(2)
    targets = []
    for _, line in _prose_lines("\n".join(lines[start:end])):
        for match in re.finditer(r"\]\(([^)\s]+)\)|\]\[([^\]]+)\]", line):
            if match.group(1):
                targets.append(match.group(1))
            elif match.group(2).lower() in definitions:
                targets.append(definitions[match.group(2).lower()])
            else:
                raise CheckError(f"the reference [{match.group(2)}] is defined nowhere")
    return targets


def github_anchor(heading: str) -> str:
    """
    The anchor GitHub gives a heading.

    :param heading: the heading's text, without its #s
    :return: lowercase, its punctuation but hyphens and underscores dropped, its spaces hyphens
    """
    text = heading.strip().lower().replace("`", "")
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors_in(text: str) -> List[str]:
    """
    The anchors of a Markdown file's headings, a repeated one with GitHub's ``-1``, ``-2`` after it.

    :param text: the file's text
    :return: the anchors, in order
    """
    anchors: List[str] = []
    for _, line in _prose_lines(text):
        heading = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if not heading:
            continue
        anchor = github_anchor(heading.group(1))
        repeats = sum(1 for earlier in anchors if re.fullmatch(re.escape(anchor) + r"(-\d+)?", earlier))
        anchors.append(anchor if repeats == 0 else f"{anchor}-{repeats}")
    return anchors


def local_target(source: Path, target: str) -> Optional[Tuple[Path, str]]:
    """
    Where a link leads in the repository, if it does.

    :param source: the file that holds the link
    :param target: the link's target
    :return: the file or directory and the anchor, which may be empty; None for a link out of the repository
    """
    for prefix in (GITHUB_BLOB, GITHUB_TREE, GITHUB_RAW):
        if target.startswith(prefix):
            path, _, anchor = target[len(prefix) :].partition("#")
            return ROOT / path, anchor
    if re.match(r"^[a-z][a-z0-9+.-]*:", target):
        return None
    path, _, anchor = target.partition("#")
    return (source.parent / path if path else source), anchor


def check_link(source: Path, link: Link) -> None:
    """
    A link that leads into the repository: its file exists, and so does its heading.

    :param source: the file that holds the link
    :param link: the link
    :raises CheckError: naming the file, the line and the target
    """
    found = local_target(source, link.target)
    if found is None:
        return
    path, anchor = found
    where = f"{relative(source)}:{link.line}: {link.target}"
    if not path.resolve().is_relative_to(ROOT) or not path.exists():
        raise CheckError(f"{where} leads to no file in the repository")
    if anchor:
        if not path.is_file() or path.suffix != ".md":
            raise CheckError(f"{where} has an anchor, but leads to no Markdown file")
        if anchor not in anchors_in(path.read_text(encoding="utf-8")):
            raise CheckError(f"{where} names no heading of {relative(path)}")


# --- What no file may hold ---

RELEASE = re.compile(r"(?<![\w.])v?\d+\.\d+\.\d+(?![\w.])")
"""A three-part version, as a release names it. An IP address has four parts, and doesn't match."""

CURRENT_RELEASE = re.compile(r"\b(current|latest|newest|recent)\s+(connector\s+|module\s+)?(release|version)\b", re.I)

COPIED_TERRAFORM = (
    re.compile(r"module\s+\"loopproof_connector\"\s*\{"),
    re.compile(r"source\s*=\s*\"[^\"]*loopproof-connector"),
    re.compile(r"resource\s+\"aws_ssm_parameter\"\s+\"loopproof_"),
    re.compile(r"\bvalue_wo\s*="),
)
"""The onboarding page's two parts, as their Terraform would be copied."""

UNSAFE_COMMANDS = (
    re.compile(r"\bget-parameters?(?![\w-])"),
    re.compile(r"\bget-parameters-by-path\b"),
    re.compile(r"\bget-parameter-history\b"),
    re.compile(r"--with-decryption\b"),
    re.compile(r"\bterraform\s+show\b[^\n]*-json"),
    re.compile(r"\bterraform\s+state\s+(pull|show)\b"),
    re.compile(r"\bterraform\s+output\b[^\n]*-json"),
    re.compile(r"\bterraform\s+destroy\b"),
    re.compile(r"(?<![\w-])-target\b"),
    re.compile(r"\bTF_VAR_"),
    re.compile(r"\bTF_LOG"),
    re.compile(r"\.tfstate"),
    re.compile(r"\bcrash\.log\b"),
    re.compile(r"\baws\s+iam\s+(get-role|list-roles|get-account-authorization-details)(?![\w-])"),
    re.compile(r"\bterraform\s+plan\b[^\n]*-out\b"),
)
"""What a command the skill gives an agent must never be: each reads or prints a value, or acts beyond the install."""


def releases_in(text: str) -> List[str]:
    """
    Releases a text names: a three-part version, or a release called the current one.

    :param text: the text
    :return: each mention
    """
    return [match.group(0) for match in RELEASE.finditer(text)] + [
        match.group(0) for match in CURRENT_RELEASE.finditer(text)
    ]


def copied_terraform_in(text: str) -> List[str]:
    """
    Terraform of the onboarding page's parts that a text holds.

    :param text: the text
    :return: each match
    """
    return [match.group(0) for pattern in COPIED_TERRAFORM for match in pattern.finditer(text)]


def unsafe_commands_in(text: str) -> List[Tuple[int, str]]:
    """
    Commands in a Markdown file's code blocks that no agent may run.

    :param text: the file's text
    :return: each block's first line and what matched
    """
    found = []
    for start, block in code_blocks(text):
        for pattern in UNSAFE_COMMANDS:
            found.extend((start, match.group(0)) for match in pattern.finditer(block))
    return found


def account_ids_in(text: str) -> List[str]:
    """
    Account ids a text holds that aren't AWS's documentation examples: any run of exactly twelve digits.

    :param text: the text
    :return: each one
    """
    return [found for found in re.findall(r"(?<!\d)\d{12}(?!\d)", text) if found not in DOCUMENTATION_ACCOUNT_IDS]


def long_lines_in(text: str) -> List[int]:
    """
    Lines over the limit, but a Markdown link's definition whose URL alone makes it long, which the coding standard
    allows since a URL can't be split.

    :param text: the text
    :return: the long lines' numbers, from 1
    """
    long = []
    for number, line in enumerate(text.splitlines(), start=1):
        if len(line) <= LINE_LIMIT:
            continue
        if re.fullmatch(r"\[[^\]]+\]: https?://\S+", line):
            continue
        long.append(number)
    return long
