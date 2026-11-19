# Finding the account and the Region

The connector goes in one place: the AWS account where Security Hub collects the findings, in Security Hub's home
Region there. LoopProof reads the findings in the Region the connector is applied in, and the connector's rule forwards
what Security Hub's event feed holds there. In the right place, that feed includes the member accounts' findings and
the linked Regions'.

- **In an organization,** the account is Security Hub's delegated administrator. With AWS Control Tower, that is
  usually the Audit account.
- **Without an organization,** it is the single account.
- **The Region** is the home Region of the account's cross-Region aggregation, which AWS also calls the aggregation
  Region: where the findings of the linked Regions arrive.

Every command here only reads, and none prints a value of LoopProof's. If you have no credentials for an account,
ask the person to run the command and tell you what it answered.

## Contents

- [Start from the repository](#start-from-the-repository)
- [With an organization](#with-an-organization)
- [Without an organization](#without-an-organization)
- [The home Region](#the-home-region)
- [Confirming with the person](#confirming-with-the-person)
- [Proposing the excluded accounts](#proposing-the-excluded-accounts)

## Start from the repository

The repository often says it already. Search it for:

- Terraform that designates Security Hub's delegated administrator, such as an
  `aws_securityhub_organization_admin_account` resource, and the account id it names;
- Terraform that configures Security Hub, GuardDuty or cross-Region aggregation, and the provider and Region it uses;
- directories, provider aliases and profiles named after the account, such as `audit`, `security` or
  `security-tooling`.

What the repository says is a lead. Check it with AWS, below.

## With an organization

Find out where your credentials are, and whether there is an organization:

```bash
aws sts get-caller-identity
aws organizations describe-organization
```

`describe-organization` answers from any account in an organization, with the management account's id. An error
saying AWS Organizations isn't in use means there is none: see [Without an organization](#without-an-organization).

Then find Security Hub's delegated administrator. Security Hub makes it the delegated administrator in AWS Organizations
too, so either command finds it:

- From the management account:

  ```bash
  aws securityhub list-organization-admin-accounts --feature SecurityHubV2 --region <region>
  ```

  `AdminAccounts[].AccountId` with `Status` `ENABLED` is the account. Without `--feature SecurityHubV2`, the command
  answers for Security Hub CSPM, the older service, whose administrator may differ.
- From the management account, or an account that is a delegated administrator in AWS Organizations:

  ```bash
  aws organizations list-delegated-administrators --service-principal securityhub.amazonaws.com
  ```

The management account designates the administrator Region by Region. If the answers differ between Regions, or name
no account, tell the person: that is theirs to settle, before LoopProof is installed.

## Without an organization

The account is the one Security Hub runs in. Check that the new Security Hub is enabled there, in the Region you think
is home:

```bash
aws sts get-caller-identity
aws securityhub describe-security-hub-v2 --region <region>
```

An answer with `HubV2Arn` means it is enabled in that Region.

## The home Region

In the account found above, list its cross-Region aggregation, in the Region the repository's Security Hub
configuration uses, then read it:

```bash
aws securityhub list-aggregators-v2 --region <region>
aws securityhub get-aggregator-v2 --aggregator-v2-arn <arn> --region <region>
```

`get-aggregator-v2` answers `AggregationRegion`, the home Region, and `LinkedRegions`, the Regions whose findings
arrive there. The aggregator's ARN names its Region too. If the list is empty, ask the person which Region is home,
and list there again.

If the account has no aggregator, each Region keeps its own findings, and the connector forwards those of the Region it
is applied in alone. Tell the person which Regions run Security Hub, and ask which one to use. Setting up cross-Region
aggregation is theirs to decide, in Security Hub, not in this install.

## Confirming with the person

Say what you found, and how, in one message, and wait for a yes:

> LoopProof's connector goes in account `<account>` (`<name>`), the Security Hub delegated administrator, in
> `<region>`, the home Region, which links `<linked Regions>`. I found it with `<commands>`. Is that right?

If anything was a guess, such as an account the repository names but AWS didn't confirm, say so.

## Proposing the excluded accounts

The connector's `excluded_accounts` lists accounts whose findings stay out of LoopProof: its rule drops them, so they
never leave the account. The list is the tenant's decision. Propose one, with a reason for each account, and write
what the person decides; an empty list is a decision too. It changes later by pull request.

List the organization's accounts, from the management account or a delegated administrator in AWS Organizations:

```bash
aws organizations list-accounts \
  --query 'Accounts[].[Id,Name,State,JoinedTimestamp]' --output table
```

Read `State`, not `Status`, which AWS Organizations is retiring. Candidates, each only with a reason:

- an account that is `SUSPENDED`, `PENDING_CLOSURE` or `CLOSED`;
- an account outside the tenant's audit scope, such as a sandbox or an experiment, if the repository or the person
  says so;
- an account the repository says is decommissioned.

Don't propose an account from its name alone; ask. Never propose the account the connector goes in, nor the management
account, without the person saying so.
