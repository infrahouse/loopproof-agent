resource "aws_securityhub_account" "this" {}

resource "aws_guardduty_detector" "this" {
  enable = true
}
