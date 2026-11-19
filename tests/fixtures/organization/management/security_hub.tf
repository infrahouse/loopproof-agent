# The audit account administers Security Hub and GuardDuty for the organization.
resource "aws_securityhub_organization_admin_account" "audit" {
  admin_account_id = "111122223333"
  depends_on       = [aws_organizations_organization.acme]
}

resource "aws_guardduty_organization_admin_account" "audit" {
  admin_account_id = "111122223333"
  depends_on       = [aws_organizations_organization.acme]
}
