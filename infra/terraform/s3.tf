resource "aws_s3_bucket" "source_files" {
    bucket = "${var.app_name}-source-files-bucket"

    tags = {
        Name = "Source files bucket"
    }
}

resource "aws_s3_bucket" "documents" {
    bucket = "${var.app_name}-chunkated-docs-bucket"

    tags = {
        Name = "Chunkated documents bucket"
    }
}
