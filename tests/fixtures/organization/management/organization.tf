resource "aws_organizations_organization" "acme" {
  feature_set = "ALL"
  aws_service_access_principals = [
    "guardduty.amazonaws.com",
    "securityhub.amazonaws.com",
  ]
}

resource "aws_organizations_organizational_unit" "security" {
  name      = "Security"
  parent_id = aws_organizations_organization.acme.roots[0].id
}

resource "aws_organizations_organizational_unit" "sandbox" {
  name      = "Sandbox"
  parent_id = aws_organizations_organization.acme.roots[0].id
}

resource "aws_organizations_account" "audit" {
  name      = "audit"
  email     = "aws-audit@example.com"
  parent_id = aws_organizations_organizational_unit.security.id
}

resource "aws_organizations_account" "log_archive" {
  name      = "log-archive"
  email     = "aws-log-archive@example.com"
  parent_id = aws_organizations_organizational_unit.security.id
}

# Experiments only: nothing in it is in the audit's scope.
resource "aws_organizations_account" "sandbox" {
  name      = "sandbox"
  email     = "aws-sandbox@example.com"
  parent_id = aws_organizations_organizational_unit.sandbox.id
}
