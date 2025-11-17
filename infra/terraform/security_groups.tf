resource "aws_security_group" "alb" {
    name        = "${var.app_name}-alb-sg"
    description = "Allow HTTP traffic from the internet to the ALB"
    vpc_id      = aws_vpc.main.id

    ingress {
        description = "HTTP from anywhere"
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        description = "All outbound"
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "${var.app_name}-alb-sg"
    }
}

resource "aws_security_group" "ecs_service" {
    name        = "${var.app_name}-ecs-sg"
    description = "Allow ALB to reach ECS tasks"
    vpc_id      = aws_vpc.main.id

    ingress {
        description = "From ALB to app port"
        from_port   = var.app_port
        to_port     = var.app_port
        protocol    = "tcp"
        security_groups = [aws_security_group.alb.id]
    }

    egress {
        description = "All outbound"
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "${var.app_name}-ecs-sg"
    }
}
