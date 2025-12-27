output "aws_account_id" {
    description = "The AWS account ID Terraform is connected to"
    value       = data.aws_caller_identity.current.account_id
}

output "aws_current_caller_arn" {
    description = "The ARN of the current caller"
    value       = data.aws_caller_identity.current.arn
}

output "vpc_id" {
    description = "The ID of the main VPC"
    value       = aws_vpc.main.id
}

output "public_subnet_ids" {
    description = "Public subnet IDs"
    value       = [
        aws_subnet.public_a.id,
        aws_subnet.public_b.id,
    ]
}

output "private_subnet_ids" {
    description = "Private subnet IDs"
    value       = [
        aws_subnet.private_a.id,
        aws_subnet.private_b.id,
    ]
}

output "alb_security_group_id" {
    description = "ALB security group ID"
    value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
    description = "ECS security group ID"
    value       = aws_security_group.ecs_service.id
}

output "ecs_cluster_name" {
    description = "ECS cluster name"
    value       = aws_ecs_cluster.main.name
}

output "ecr_repository_url" {
    description = "ECR repository URL"
    value       = aws_ecr_repository.app.repository_url
}

output "ecs_task_execution_role_arn" {
    description = "ECS task execution role ARN"
    value       = aws_iam_role.ecs_task_execution.arn
}

output "task_definition_arn" {
    description = "ECR task definition ARN"
    value       = aws_ecs_task_definition.app.arn
}

output "alb_dns_name" {
    description = "Public DNS name of the ALB"
    value       = aws_lb.app.dns_name
}

output "ecs_service_name" {
    description = "ECS service name"
    value       = aws_ecs_service.app.name
}

output "opensearch_collection_arn" {
    description = "OpenSearch Serverless collection ARN"
    value       = aws_opensearchserverless_collection.rag_app.arn
}

output "opensearch_collection_endpoint" {
    description = "OpenSearch Serverless collection endpoint"
    value       = aws_opensearchserverless_collection.rag_app.collection_endpoint
}

output "opensearch_collection_name" {
    description = "OpenSearch Serverless collection name"
    value       = aws_opensearchserverless_collection.rag_app.name
}

output "opensearch_dashboard_endpoint" {
    description = "OpenSearch Serverless dashboard endpoint"
    value       = aws_opensearchserverless_collection.rag_app.dashboard_endpoint
}

output "cognito_user_pool_id" {
    description = "ID of the Cognito user pool"
    value = aws_cognito_user_pool.pool.id
}

output "cognito_app_client_id" {
    description = "ID of the Cognito app client"
    value = aws_cognito_user_pool_client.public.id
}

output "cognito_domain" {
    description = "Cognito domain"
    value = aws_cognito_user_pool_domain.main.domain
}
