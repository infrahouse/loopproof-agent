provider "aws" {
  region              = "us-west-2"
  allowed_account_ids = ["777788889999"]

  assume_role {
    role_arn = "arn:aws:iam::777788889999:role/acme-infra-ci"
  }
}
