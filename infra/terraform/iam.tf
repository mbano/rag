resource "aws_iam_role" "ecs_task_execution" {
    name = "${var.app_name}-task-execution-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Sid    = ""
                Principal = {
                    Service = "ecs-tasks.amazonaws.com"
                }
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
    role       = aws_iam_role.ecs_task_execution.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_task_execution_secrets" {
    statement {
        actions   = [
            "secretsmanager:GetSecretValue",
            "secretsmanager:DescribeSecret",
        ]
        effect    = "Allow"
        resources = [
            "${data.aws_secretsmanager_secret.app.arn}*",
        ]
    }
}

resource "aws_iam_policy" "ecs_task_execution_secrets" {
    name = "${var.app_name}-task-execution-secrets"
    policy = data.aws_iam_policy_document.ecs_task_execution_secrets.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_secrets" {
    role       = aws_iam_role.ecs_task_execution.name
    policy_arn = aws_iam_policy.ecs_task_execution_secrets.arn
}

resource "aws_iam_role" "ecs_task" {
    name = "${var.app_name}-task-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "ecs-tasks.amazonaws.com"
                }
            }
        ]
    })
}
