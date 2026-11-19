# Placing the parts

Both parts go in one Terraform root: Part 2 refers to Part 1's two parameters by their Terraform addresses. That root
must apply resources in the account and the Region found in step 2, with a provider configured for both.

## Contents

- [Choosing the root](#choosing-the-root)
- [The provider](#the-provider)
- [What the root and the machine that applies it need](#what-the-root-and-the-machine-that-applies-it-need)
- [More than one environment](#more-than-one-environment)
- [Repositories that CI applies](#repositories-that-ci-applies)
- [Repositories applied by hand](#repositories-applied-by-hand)

## Choosing the root

Look for the root that already manages that account in that Region: its Security Hub or GuardDuty configuration,
its IAM roles, a directory named after it. Tell it by the provider's settings, not its name alone: an `assume_role`
whose role ARN names the account, `allowed_account_ids`, a profile, and `region`.

- **One root fits:** use it.
- **Several fit:** propose the one that holds the account's security configuration, and ask.
- **None fits:** ask the person whether to add a root, laid out like the repository's others, with the same backend
  and provider settings. Don't invent a state backend.

If the repository uses a wrapper around Terraform, such as Terragrunt or its own scripts, follow it. Read how a root
is planned and applied there before you add anything.

Keep the files' names, `loopproof-parameters.tf` and `loopproof-connector.tf`, unless the repository names files by
another convention.

## The provider

The module registers the Region of the provider it is applied with, and LoopProof reads the findings there. So the
provider must be in the account from step 2, and in its home Region.

- **The root's default provider is that account and Region:** the parts need no change.
- **The root reaches that account through an aliased provider,** such as `provider "aws" { alias = "audit" ... }`:
  add `provider = aws.audit` to each of Part 1's two `aws_ssm_parameter` resources, and
  `providers = { aws = aws.audit }` inside Part 2's module block. These are the only changes to the parts.
- **No provider reaches it:** add one, as the repository's other providers for its other accounts are written, and
  show the person.

Never point the module at another Region than the home Region, even if the root's default provider is elsewhere.

## What the root and the machine that applies it need

- **Terraform 1.11 or later.** Part 1's write-only placeholder needs it. If the root pins an older Terraform, tell the
  person: upgrading it is their change. The module's own required versions of Terraform and the AWS provider are in
  its `terraform.tf`; `terraform init` reports a conflict with the root's.
- **`terraform init`** after adding Part 2, for the module, and the root's lock file updated if the module needs
  another provider version. Commit the lock file if the repository does.
- **On the machine that applies:** curl 7.76 or later, on Linux or macOS, and HTTPS to LoopProof's API, the
  `registration_url` in Part 2. The registration is one `curl` call from that machine.
- **Permissions of whoever applies:** creating IAM roles and their policies, EventBridge rules and SSM parameters;
  `ssm:GetParameter` on `/loopproof/<environment>/*`, since the module reads both parameters on every plan and apply;
  and `kms:Decrypt` on the key, if the parameters use a customer-managed KMS key.

If the applier's role is managed in this repository and lacks one of these, propose the change, and say why.

## More than one environment

The connector is installed once per LoopProof tenant, in the one account and Region from step 2. A repository with a
root per environment, such as `staging/` and `production/`, each in its own accounts, gets it in the root that manages
Security Hub's account alone, not in each environment.

The parameter names and the module's `environment` are LoopProof's environment, which the page wrote, not the
repository's. Leave them as they are.

## Repositories that CI applies

- **Two pull requests.** The first holds Part 1 alone. The second holds Part 2, opened only once the first is
  applied and the person has stored both values: before that, the module's plan stops at the placeholder.
- **Each pull request says** what it creates, that it holds no value, and what comes next: after the first, the
  person stores the two values from the onboarding page; after the second, LoopProof checks the account. The second
  lists the excluded accounts, each with the reason the person agreed to.
- **Read the plan in CI's log,** as text. Never download a saved plan or a plan's JSON from CI: both hold the
  ExternalId.
- **The person merges.** CI's apply is the repository's; never run an apply of your own beside it.
- **CI's runner applies Part 2,** so it needs curl and HTTPS to LoopProof's API. If it can't reach LoopProof, see
  [when-it-fails.md](when-it-fails.md).

## Repositories applied by hand

- Run `terraform plan` in the root, if your credentials allow, and read it as [the-plan.md](the-plan.md) says.
  Otherwise ask the person to run it and show you the text.
- Apply only on the person's go-ahead, in the way they choose: they run `terraform apply` themselves, or you run it
  after they have read the plan and told you to.
- Commit the parts as the repository commits its changes, through a branch and a pull request if that is its practice.
