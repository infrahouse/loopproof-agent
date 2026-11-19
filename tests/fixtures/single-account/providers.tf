provider "aws" {
  region              = "us-west-2"
  profile             = "widget"
  allowed_account_ids = ["444455556666"]
}

# For the CloudFront certificate, which must be in us-east-1 whatever the default Region is.
provider "aws" {
  alias               = "us_east_1"
  region              = "us-east-1"
  profile             = "widget"
  allowed_account_ids = ["444455556666"]
}
