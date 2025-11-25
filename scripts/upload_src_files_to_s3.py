import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from app.utils.paths import DATA_DIR

load_dotenv()

s3 = boto3.client("s3")
bucket = os.environ["AWS_S3_SOURCE_FILES_BUCKET"]

for dir in DATA_DIR.glob("*"):
    if dir.is_dir():
        for file in dir.glob("*"):
            if file.is_file():
                try:
                    s3.upload_file(str(file), bucket, str(file.name))
                except ClientError as e:
                    print(e)
