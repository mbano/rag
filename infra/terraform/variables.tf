variable "aws_region" {
    description = "AWS region to deploy to"
    type        = string
    default     = "eu-north-1"
}

variable "aws_profile" {
    description = "AWS CLI prfile to use for credentials"
    type        = string
    default     = "default"
}

variable "app_name" {
    description = "Base name for the app and related resources"
    type        = string
    default     = "rag-app"
}

variable "app_port" {
    description = "Port the application container listens on"
    type        = number
    default     = 8000
}

variable "container_image_tag" {
    description = "Tag of the container image to use"
    type        = string
    default     = "latest"
}

variable "task_cpu" {
    description = "Amount of CPU to allocate to the task"
    type        = number
    default     = 512
}

variable "task_memory" {
    description = "Amount of memory to allocate to the task"
    type        = number
    default     = 1024
}

variable "desired_count" {
    description = "Number of instances of the ECS task to keep running"
    type        = number
    default     = 1
}

variable "developer_iam_arns" {
    description = "List of IAM user/role ARNs for local devs who need OpenSearch access"
    type        = list(string)
    default     = []
}
