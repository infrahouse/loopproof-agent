# Reading the plans

Read a plan as text, from `terraform plan` or from CI's log. Never print it as JSON, and never open a saved plan
file: the [rules](../SKILL.md#the-rules) say why.

Below, `<environment>` is LoopProof's environment, in the parameters' names in Part 1, and `module.loopproof_connector`
is Part 2's module block, by the name the page gave it.

## Part 1's plan

It creates two `aws_ssm_parameter` resources, both SecureString:

- `/loopproof/<environment>/external-ids`;
- `/loopproof/<environment>/registration-token`.

Their value is write-only: the plan shows it as a write-only attribute, not as text, and Terraform never stores it.
Nothing else of LoopProof's appears. If the plan changes anything else in the root, it was pending before Part 1:
point it out, and let the person decide whether it goes with this apply.

After the person stores the values, Part 1's parameters show no change in later plans: Terraform never reads or
compares a write-only value.

## Part 2's plan

It reads the ExternalIds parameter, as a data source, and creates, inside `module.loopproof_connector`:

- **The connector role,** `aws_iam_role`, named `loopproof-<environment>-connector`. Its trust policy shows as
  `(sensitive value)`: it holds the ExternalId.
- **The connector role's inline policies,** `aws_iam_role_policy`: reading Security Hub's findings and setting their
  status and comment, reading the module's own String parameters, reading ECR repositories' tags, and querying AWS
  Config aggregators.
- **The forwarder role,** `aws_iam_role` and its `aws_iam_role_policy`, which EventBridge uses to put the findings on
  LoopProof's bus.
- **The rule and its target,** `aws_cloudwatch_event_rule` and `aws_cloudwatch_event_target`, which forward Security
  Hub's findings to LoopProof's event bus in another account.
- **The module's String parameters,** `aws_ssm_parameter`: `/loopproof/<environment>/excluded-accounts`, holding the
  excluded accounts, and `/loopproof/<environment>/tenant-settings`, holding the tenant's settings or LoopProof's
  defaults; and one under `/loopproof/<environment>/accept-rules/` for each accept rule, if Part 2 holds any.
- **The registration,** `terraform_data`: creating it makes the one call that registers the role with LoopProof.

Part 2 also adds two outputs to the root, the connector role's ARN and the Region.

Check that:

- the excluded-accounts parameter's value is the list the person decided;
- every resource is created, and nothing is destroyed or replaced;
- Part 1's parameters don't change.

## What must never appear

- **A resource destroyed or replaced,** in the connector or anywhere else in the root. Stop, and show the person.
- **Part 1's parameters changing.** A value is never Terraform's to write after the placeholder.
- **A value in plain text:** a string that starts with `lprt_`, or the ExternalId. If one appears, follow rule 3.
- **Resources in another account or Region than step 2's.** The ExternalIds parameter's ARN, which Part 2's plan
  reads, names both; so do the role's ARN and the outputs, after the apply.

## After the apply

The apply's output shows the registration created once, its own output suppressed: Terraform hides a command's output
while an ephemeral value, the token, is in its environment. If the call failed, the apply failed there:
[when-it-fails.md](when-it-fails.md) says what to do, by cause.

Then a second `terraform plan` shows no changes. Later plans make no call to LoopProof, unless the role is replaced.

## Later plans

- **An accept rule, tenant settings, the excluded accounts:** the matching String parameter is created or changed in
  place, and nothing else. Read its published value in the plan: the module drops a field it doesn't know without an
  error, so a misspelled field is missing there.
- **An ExternalId rotation:** the connector role's trust policy changes in place, shown as `(sensitive value)`.
- **An upgrade of the module:** read the module's notes for the release, then check the plan against them, as
  [after-go-live.md](after-go-live.md) says.

None of them destroys or replaces the connector role, and none creates the registration again.
