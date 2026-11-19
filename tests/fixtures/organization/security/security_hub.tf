resource "aws_securityhub_account" "audit" {
  provider = aws.audit
}

resource "aws_securityhub_organization_configuration" "audit" {
  provider              = aws.audit
  auto_enable           = true
  auto_enable_standards = "DEFAULT"
  depends_on            = [aws_securityhub_account.audit]
}
