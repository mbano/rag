resource "aws_ecr_repository" "app" {
    name = "${var.app_name}-repo"
    force_delete = true

    image_scanning_configuration {
        scan_on_push = true
    }

    tags = {
        Name = "${var.app_name}-repo"
    }
}
