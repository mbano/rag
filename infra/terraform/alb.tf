resource "aws_lb" "app" {
    name               = "${var.app_name}-alb"
    load_balancer_type = "application"
    internal           = false

    security_groups = [aws_security_group.alb.id]
    subnets         = [
        aws_subnet.public_a.id,
        aws_subnet.public_b.id,
    ]

    tags = {
        Name = "${var.app_name}-alb"
    }
}

resource "aws_lb_target_group" "app" {
    name        = "${var.app_name}-tg"
    port        = var.app_port
    protocol    = "HTTP"
    target_type = "ip"
    vpc_id      = aws_vpc.main.id

    health_check {
        path                = "/"
        protocol            = "HTTP"
        matcher             = "200-399"
        interval            = 30
        timeout             = 5
        healthy_threshold   = 3
        unhealthy_threshold = 2
    }

    tags = {
        Name = "${var.app_name}-tg"
    }
}

resource "aws_lb_listener" "http" {
    load_balancer_arn = aws_lb.app.arn
    port              = 80
    protocol          = "HTTP"

    default_action {
        type             = "forward"
        target_group_arn = aws_lb_target_group.app.arn
    }
}
