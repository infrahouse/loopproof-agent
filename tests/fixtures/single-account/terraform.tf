terraform {
  required_version = ">= 1.11"

  backend "s3" {
    bucket       = "widget-terraform-state"
    key          = "terraform.tfstate"
    region       = "us-east-1"
    profile      = "widget"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
