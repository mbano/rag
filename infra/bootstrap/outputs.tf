output "tf_state_bucket" {
  description = "S3 bucket name for Terraform remote state."
  value       = aws_s3_bucket.tf_state.bucket
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions to assume."
  value       = aws_iam_role.github_actions.arn
}
