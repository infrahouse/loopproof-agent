terraform {
  required_version = ">= 1.11"

  backend "s3" {
    bucket       = "acme-infra-terraform-state"
    key          = "management/terraform.tfstate"
    region       = "us-west-2"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
