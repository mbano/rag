from opensearchpy import RequestsHttpConnection, AWSV4SignerAuth
from functools import lru_cache
import os
import boto3

AOSS_SERVICE = "aoss"


@lru_cache(maxsize=1)
def get_opensearch_auth() -> AWSV4SignerAuth:
    region = os.getenv("AWS_REGION")
    service = AOSS_SERVICE
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, service)

    return auth


@lru_cache(maxsize=1)
def get_opensearch_langchain_kwargs() -> dict:
    connection_kwargs = {
        "http_auth": get_opensearch_auth(),
        "use_ssl": True,
        "verify_certs": True,
        "connection_class": RequestsHttpConnection,
        "timeout": 300,
    }
    return connection_kwargs
