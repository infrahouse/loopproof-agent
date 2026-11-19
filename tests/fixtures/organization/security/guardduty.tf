resource "aws_guardduty_detector" "audit" {
  provider = aws.audit
  enable   = true
}

resource "aws_guardduty_organization_configuration" "audit" {
  provider                         = aws.audit
  detector_id                      = aws_guardduty_detector.audit.id
  auto_enable_organization_members = "ALL"
}
