resource "aws_s3_bucket" "logs" {
  provider = aws.log_archive
  bucket   = "acme-log-archive-444455556666"
}
