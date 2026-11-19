resource "aws_acm_certificate" "site" {
  provider          = aws.us_east_1
  domain_name       = "www.example.com"
  validation_method = "DNS"
}
