variable "app_name" {
    type        = string
    description = "App name, used to name TF state resources"
    default     = "rag-app"
}

variable "aws_region" {
    type        = string
    description = "AWS region for Terraform state + OIDC role"
    default     = "eu-north-1"
}

variable "github_owner" {
    type        = string
    description = "GitHub org or username"
    default     = "mbano"
}

variable "github_repo" {
    type        = string
    description = "GitHub repository name"
    default     = "mbano/rag"
}
