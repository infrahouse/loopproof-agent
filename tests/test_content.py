"""
What no file may hold: a connector release, the onboarding page's Terraform, a command that reads a value, an account
id but AWS's documentation examples, and a line over the coding standard's 120 characters.
"""

from pathlib import Path
from typing import List

import pytest

from skill_repo import (
    FIXTURES,
    GENERATED,
    SKILL_DIR,
    account_ids_in,
    copied_terraform_in,
    long_lines_in,
    markdown_files,
    relative,
    releases_in,
    text_files,
    unsafe_commands_in,
)


def _written() -> List[Path]:
    """Every text file but a tool's, and the tests' own code, whose samples hold what they must catch."""
    return [
        path
        for path in text_files()
        if relative(path) not in GENERATED and not (path.suffix == ".py" and relative(path).startswith("tests/"))
    ]


def _documents() -> List[Path]:
    """What an agent or a person reads: the Markdown files, the skill's folder and the fixtures."""
    paths = set(markdown_files())
    paths.update(path for path in text_files() if path.is_relative_to(SKILL_DIR) or path.is_relative_to(FIXTURES))
    return sorted(paths)


@pytest.mark.parametrize("path", _documents(), ids=relative)
def test_no_connector_release_is_named(path: Path) -> None:
    """Renovate moves the connector's release in LoopProof, not here: nothing names one, or calls one the current."""
    assert not releases_in(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", _written(), ids=relative)
def test_no_part_is_copied(path: Path) -> None:
    """The two parts come from the onboarding page: no file holds their Terraform, the fixtures included."""
    assert not copied_terraform_in(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", markdown_files(), ids=relative)
def test_no_command_reads_a_value(path: Path) -> None:
    """No code block gives an agent a command that reads a value, prints state or a plan as JSON, or targets."""
    assert not unsafe_commands_in(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", text_files(), ids=relative)
def test_account_ids_are_awss_examples(path: Path) -> None:
    """Every account id is one of AWS's documentation examples: no tenant's, no InfraHouse's."""
    assert not account_ids_in(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", [p for p in text_files() if relative(p) not in GENERATED], ids=relative)
def test_no_line_is_over_120_characters(path: Path) -> None:
    """The coding standard's limit, but for a Markdown link's definition, whose URL can't be split."""
    assert not long_lines_in(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", text_files(), ids=relative)
def test_every_file_ends_with_a_newline(path: Path) -> None:
    """The coding standard: every file ends with a newline."""
    text = path.read_text(encoding="utf-8")
    assert not text or text.endswith("\n")


@pytest.mark.parametrize(
    "text",
    [
        'version = "1.5.0"',
        "Upgrade to v2.0.1 first.",
        "This needs the current connector release.",
        "Use the latest version of the module.",
    ],
)
def test_a_release_is_caught(text: str) -> None:
    """A three-part version, or a release called the current or latest one, is caught."""
    assert releases_in(text)


@pytest.mark.parametrize("text", ["curl 7.76 or later", "Terraform 1.11", "10.20.1.0/24", "the release the root runs"])
def test_what_isnt_a_release_passes(text: str) -> None:
    """Two-part versions, as the page names Terraform's and curl's, and IP addresses aren't releases."""
    assert not releases_in(text)


@pytest.mark.parametrize(
    "text",
    [
        'module "loopproof_connector" {',
        'source  = "registry.infrahouse.com/infrahouse/loopproof-connector/aws"',
        'resource "aws_ssm_parameter" "loopproof_external_ids" {',
        '  value_wo         = "unset"',
    ],
)
def test_a_copied_part_is_caught(text: str) -> None:
    """The parts' module block, its source, Part 1's resources and their placeholder are each caught."""
    assert copied_terraform_in(text)


@pytest.mark.parametrize(
    "command",
    [
        "aws ssm get-parameter --name /loopproof/production/external-ids",
        "aws ssm get-parameters --names a b",
        "aws ssm get-parameters-by-path --path /loopproof/production",
        "aws ssm get-parameter-history --name /loopproof/production/registration-token",
        "aws ssm get-parameter --name x --with-decryption",
        "terraform show -json plan.out",
        "terraform state pull",
        "terraform state show module.loopproof_connector.aws_iam_role.connector",
        "terraform output -json",
        "terraform apply -target=aws_ssm_parameter.x",
        "terraform destroy",
        "TF_VAR_external_id=x terraform apply",
        "TF_LOG=DEBUG terraform plan",
        "aws iam get-role --role-name loopproof-production-connector",
        "aws iam list-roles",
        "aws iam get-account-authorization-details --filter Role",
        "terraform plan -out=plan.out",
    ],
)
def test_an_unsafe_command_is_caught(command: str) -> None:
    """Each command an agent must never run is caught in a code block."""
    assert unsafe_commands_in(f"Text.\n\n```bash\n{command}\n```\n")


@pytest.mark.parametrize(
    "command",
    [
        "aws ssm describe-parameters --region us-west-2",
        "aws iam list-role-tags --role-name loopproof-production-connector",
        "terraform output loopproof_connector_role_arn",
        "terraform plan",
    ],
)
def test_a_safe_command_passes(command: str) -> None:
    """The commands the skill gives, which print no value, aren't caught."""
    assert not unsafe_commands_in(f"```bash\n{command}\n```\n")


def test_unsafe_words_in_prose_pass() -> None:
    """The rules name what never to run in prose; only code blocks are commands."""
    assert not unsafe_commands_in("Run no `aws ssm get-parameter`, and no `terraform state pull`.\n")


def test_another_account_id_is_caught() -> None:
    """Twelve digits that aren't a documentation example are caught; longer runs of digits aren't account ids."""
    other = "2" * 12
    assert account_ids_in(f"arn:aws:iam::{other}:role/x") == [other]
    assert not account_ids_in("1" * 13)
    assert not account_ids_in("arn:aws:iam::111122223333:role/x")


def test_a_long_line_is_caught() -> None:
    """A line of 121 characters is over; a link's definition with a long URL isn't."""
    assert long_lines_in("x" * 121) == [1]
    assert not long_lines_in("x" * 120)
    assert not long_lines_in("[skill]: https://github.com/" + "a/" * 60)
    assert long_lines_in("See [skill]: https://github.com/" + "a/" * 60 + " for more")
