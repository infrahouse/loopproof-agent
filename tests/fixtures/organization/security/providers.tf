# CI's role is in the management account; it reaches each account through a role there, by an alias.

provider "aws" {
  alias               = "audit"
  region              = "us-west-2"
  allowed_account_ids = ["111122223333"]

  assume_role {
    role_arn = "arn:aws:iam::111122223333:role/acme-infra-ci"
  }
}

provider "aws" {
  alias               = "log_archive"
  region              = "us-west-2"
  allowed_account_ids = ["444455556666"]

  assume_role {
    role_arn = "arn:aws:iam::444455556666:role/acme-infra-ci"
  }
}
