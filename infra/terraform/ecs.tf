resource "aws_ecs_cluster" "main" {
    name = "${var.app_name}-cluster"

    tags = {
        Name = "${var.app_name}-cluster"
    }
}

resource "aws_ecs_task_definition" "app" {
    family                   = "${var.app_name}-task"
    network_mode             = "awsvpc"
    requires_compatibilities = ["FARGATE"]
    cpu                      = var.task_cpu
    memory                   = var.task_memory

    execution_role_arn       = aws_iam_role.ecs_task_execution.arn
    task_role_arn            = aws_iam_role.ecs_task.arn

    container_definitions = jsonencode([
        {
            name      = var.app_name
            image     = "${aws_ecr_repository.app.repository_url}:${var.container_image_tag}"
            essential = true

            portMappings = [
                {
                    protocol      = "tcp"
                    containerPort = var.app_port
                    hostPort      = var.app_port
                }
            ]

            logConfiguration = {
                logDriver = "awslogs"
                options = {
                    awslogs-group         = aws_cloudwatch_log_group.app.name
                    awslogs-region        = var.aws_region
                    awslogs-stream-prefix = var.app_name
                }
            }

            "environment": [
                {
                "name": "LANGSMITH_TRACING",
                "value": "true"
                },
                {
                "name": "APP_DATA_DIR",
                "value": "data"
                },
                {
                "name": "LANGSMITH_ENDPOINT",
                "value": "https://api.smith.langchain.com"
                },
                {
                "name": "LANGSMITH_PROJECT",
                "value": "rag_demo_aws"
                },
                {
                "name": "HF_DATASET_REPO",
                "value": "m-bano/rag-assets"
                },
                {
                "name": "APP_ARTIFACTS_DIR",
                "value": "/artifacts"
                },
                {
                "name": "HF_HUB_ENABLE_HF_TRANSFER",
                "value": "1"
                },
                {
                "name": "HF_DATASET_REVISION",
                "value": "main"
                },
                {
                    "name": "OPENSEARCH_COLLECTION_ENDPOINT",
                    "value": aws_opensearchserverless_collection.rag_app.collection_endpoint
                },
                {
                    "name": "OPENSEARCH_COLLECTION_NAME",
                    "value": aws_opensearchserverless_collection.rag_app.name
                },
                {
                    "name": "OPENSEARCH_DASHBOARD_ENDPOINT",
                    "value": "https://qy9q7mumiymu2rx0k3ja.eu-north-1.aoss.amazonaws.com/_dashboards"
                    "value": aws_opensearchserverless_collection.rag_app.dashboard_endpoint
                }
            ],
            "secrets": [
                {
                "name": "LANGSMITH_API_KEY",
                "valueFrom": "arn:aws:secretsmanager:eu-north-1:259153338192:secret:demo/rag-NvDdyL:LANGSMITH_API_KEY::"
                },
                {
                "name": "OPENAI_API_KEY",
                "valueFrom": "arn:aws:secretsmanager:eu-north-1:259153338192:secret:demo/rag-NvDdyL:OPENAI_API_KEY::"
                },
                {
                "name": "COHERE_API_KEY",
                "valueFrom": "arn:aws:secretsmanager:eu-north-1:259153338192:secret:demo/rag-NvDdyL:COHERE_API_KEY::"
                },
                {
                "name": "HF_TOKEN",
                "valueFrom": "arn:aws:secretsmanager:eu-north-1:259153338192:secret:demo/rag-NvDdyL:HF_TOKEN::"
                }
            ],
        }
    ])

    tags = {
        Name = "${var.app_name}-task-def"
    }
}

resource "aws_ecs_service" "app" {
    name            = "${var.app_name}-service"
    cluster         = aws_ecs_cluster.main.id
    task_definition = aws_ecs_task_definition.app.arn
    desired_count   = var.desired_count
    launch_type     = "FARGATE"
    platform_version = "LATEST"

    network_configuration {
        security_groups  = [aws_security_group.ecs_service.id]
        subnets          = [
            aws_subnet.private_a.id,
            aws_subnet.private_b.id,
        ]
        assign_public_ip = false
    }

    load_balancer {
        target_group_arn = aws_lb_target_group.app.arn
        container_name   = var.app_name
        container_port   = var.app_port
    }

    depends_on = [
        aws_lb_listener.http
    ]

    tags = {
        Name = "${var.app_name}-service"
    }
}
