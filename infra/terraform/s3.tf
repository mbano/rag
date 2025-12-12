resource "aws_s3_bucket" "source_files" {
    bucket        = "${var.app_name}-source-files-bucket"
    force_destroy = true

    tags = {
        Name = "Source files bucket"
    }
}

resource "aws_s3_bucket" "documents" {
    bucket        = "${var.app_name}-chunkated-docs-bucket"
    force_destroy = true

    tags = {
        Name = "Chunkated documents bucket"
    }
}
