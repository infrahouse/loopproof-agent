# CI's role is in the management account.
provider "aws" {
  region              = "us-west-2"
  allowed_account_ids = ["123456789012"]
}
