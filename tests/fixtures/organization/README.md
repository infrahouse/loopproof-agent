# acme-infra

Terraform for Acme's AWS organization. A fixture of `infrahouse/loopproof-agent`: an organization's repository, laid
out as customers' are, applied by CI. Its account ids are AWS's documentation examples.

| Root                  | Account                                   | Provider                       |
|-----------------------|-------------------------------------------|--------------------------------|
| `management/`         | management, 123456789012                  | `aws`                          |
| `security/`           | audit, 111122223333; log archive, 444455556666 | `aws.audit`, `aws.log_archive` |
| `workloads/sandbox/`  | sandbox, 777788889999                     | `aws`                          |

Every root is in `us-west-2`, but where a resource says otherwise.

## How it is applied

By CI, `.github/workflows/terraform.yml`: a pull request plans every root it changes, and a merge to `main` applies
them. Nobody applies by hand.
