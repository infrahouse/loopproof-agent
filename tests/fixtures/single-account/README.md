# widget-terraform

Terraform for Widget's one AWS account, 444455556666. A fixture of `infrahouse/loopproof-agent`: a single account's
repository, laid out as customers' are, applied by hand. Its account id is one of AWS's documentation examples.

## How it is applied

By hand, from a laptop, with the `widget` profile:

```bash
terraform init
terraform plan
terraform apply
```

Changes go through a pull request first, and someone applies after the merge.
