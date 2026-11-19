# After go-live

Once the connector is installed, its later work is of two kinds: changes to Part 2's module block, by pull request
as the repository changes its Terraform, and changes to Part 1's parameters, which only the person makes, with
LoopProof's commands. The [rules](../SKILL.md#the-rules) hold for both.

The connector module's public [README][module-readme] explains each input. Read it at the release the root runs.

## Contents

- [An accept rule](#an-accept-rule)
- [Tenant settings](#tenant-settings)
- [The excluded accounts](#the-excluded-accounts)
- [An ExternalId rotation](#an-externalid-rotation)
- [An upgrade of the module](#an-upgrade-of-the-module)
- [Registering the role again](#registering-the-role-again)

## An accept rule

A person accepts a risk on a work item's page in LoopProof. LoopProof drafts the rule and files its register entry,
an issue in the tenant's Linear, in the intake team's "LoopProof risk register" project. The entry holds the rule as
Terraform: one entry of the module's list. The rule needs the entry: LoopProof loads no rule without it.

1. Get the rule from its register entry: the person pastes it, or you read the issue, if you have access to the
   tenant's Linear.
2. Add it, as it is, to the module block's list for its kind: `threat_accept_rules` for a threat, GuardDuty's;
   `vulnerability_accept_rules` for a vulnerability, Inspector's. The entry says which.
3. Set its `decision_ref` to the entry's identifier, such as `SEC-42`.
4. Change nothing else of the rule: its scope, reason and review date are the person's decision, made in LoopProof.
5. Read the plan: one String parameter created under `/loopproof/<environment>/accept-rules/`, named by the rule's id.
   Read its published value: the module drops a field it doesn't know without an error.
6. Open the pull request, citing the entry. The person merges it.

LoopProof reads the rules within 15 minutes of the apply. Its Settings page shows each rule, in force or not, and why.

Removing a rule from the list, by pull request, takes it out of force. A change to a rule's content is a new version
of it, which needs its register entry too.

See [Accepting risks][accepting-risks] in the module's README for each field and what LoopProof refuses.

## Tenant settings

The tenant's SLA targets, thresholds, quiet window, ticket budget and review due date live in Part 2's
`tenant_settings`, as the tenant's security policy states them. A setting left out is LoopProof's default.

- Set only what the person's policy states, and ask where it is unclear. Never invent a number.
- The module checks every setting at plan, and refuses one it doesn't know.
- The plan changes the `/loopproof/<environment>/tenant-settings` parameter in place, and nothing else.
- LoopProof reads a change within 15 minutes, and applies it to work items that open after.
- A change to an SLA target can turn LoopProof's grace policy off. The module's README says when: tell the person
  before the pull request.

See [Your settings in LoopProof][settings] in the module's README for each setting, its default and its bounds.

## The excluded accounts

A change to `excluded_accounts` is the tenant's decision, as at the install: propose it with the reason for each
account, and write what the person decides. The plan changes the excluded-accounts parameter in place, and the
rule's pattern. See [find-the-account.md](find-the-account.md#proposing-the-excluded-accounts).

## An ExternalId rotation

An admin starts a rotation on LoopProof's Settings page, which shows the new ExternalId once, with the commands that
store it. Your Terraform doesn't change: each apply reads the parameter, and changes the role's trust policy in place.

1. **The person** runs the page's command that adds the new ExternalId beside the current one in the parameter.
2. **Apply,** the repository's way, on the person's go-ahead. The plan changes the connector role's trust policy in
   place, shown as `(sensitive value)`, and nothing else.
3. **The person** waits at least 10 minutes, then switches on Settings.
4. **The person** runs the page's command that keeps the new ExternalId alone in the parameter.
5. **Apply** again, as in step 2.
6. **The person** completes the rotation on Settings.

Both commands read the parameter inside the person's own shell, and print no value. Never run them, and never read
the parameter to check them: check its version, as the install's step 5 does, which rises with each.

In a repository that CI applies, a rotation has nothing to commit. Ask the person how the repository applies with no
change, such as running its apply workflow again. Don't make a change to start one.

See [Rotating the ExternalId][rotation] in the module's README.

## An upgrade of the module

Renovate, or the person, moves Part 2's module version by pull request. Never choose a release yourself.

1. Read the module's [upgrading notes][upgrading] and its changelog, for every release between the one the root runs
   and the new one.
2. Read the plan against them. An upgrade changes the connector role's `module_version` tag in place, and may add a
   policy or a parameter. It destroys or replaces nothing, and doesn't create the registration again, unless the notes
   say so.
3. If a release needs a new input or another change, the notes say what. Propose it on the same pull request, and say
   why.
4. If the plan does anything the notes don't say, stop, and show the person.

To check which release the role runs, read the role's tags, which hold no trust policy:

```bash
aws iam list-role-tags --role-name loopproof-<environment>-connector
```

## Registering the role again

The registration token stays in its parameter after the install. If the connector role is ever replaced, the next
apply registers it again with that token. A replaced role is a plan to stop at and show the person first.

If the token was replaced, or the parameter no longer holds one, the registration fails. Then:

1. The person mints a new registration token on LoopProof's Settings page, and stores it with the page's command.
2. Apply, on the person's go-ahead, within the token's 24 hours. If the registration is tainted, a plain apply
   registers. If it isn't, the module's README says how to run it again: see
   [Keep the token in its parameter][keep-token].

[module-readme]: https://github.com/infrahouse/terraform-aws-loopproof-connector#readme
[accepting-risks]: https://github.com/infrahouse/terraform-aws-loopproof-connector#accepting-risks
[settings]: https://github.com/infrahouse/terraform-aws-loopproof-connector#your-settings-in-loopproof
[rotation]: https://github.com/infrahouse/terraform-aws-loopproof-connector#rotating-the-externalid
[keep-token]: https://github.com/infrahouse/terraform-aws-loopproof-connector#keep-the-token-in-its-parameter
[upgrading]: https://infrahouse.github.io/terraform-aws-loopproof-connector/upgrading/
