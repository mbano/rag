resource "aws_opensearchserverless_security_policy" "encryption_policy" {
    name = "encryption-policy"
    type = "encryption"
    policy = jsonencode({
        "Rules" = [
            {
                "Resource" = [
                    "collection/rag-app-collection"
                ],
                "ResourceType" = "collection"
            }
        ],
        "AWSOwnedKey" = true
    })
}

resource "aws_opensearchserverless_collection" "rag_app" {
    name = "rag-app-collection"
    description = "Vector search collection for RAG demo app"
    type = "VECTORSEARCH"

    depends_on = [aws_opensearchserverless_security_policy.encryption_policy]

    tags = {
        Project = "RAG DEMO"
    }
}

resource "aws_opensearchserverless_security_policy" "network_policy" {
    name = "network-policy"
    description = "Public network policy for RAG demo app"
    type = "network"
    policy = jsonencode([
        {
            Description = "Public access to collection and Dashboard endpoints"
            Rules = [
                {
                    ResourceType = "collection",
                    Resource = [
                        "collection/rag-app-collection",
                    ]
                },
                {
                    ResourceType = "dashboard",
                    Resource = [
                        "collection/rag-app-collection"
                    ]
                }
            ],
            AllowFromPublic = true
        }
    ])
}

resource "aws_opensearchserverless_access_policy" "data_access_policy" {
    name = "data-access-policy"
    description = "Read and write access policy for RAG demo app"
    type = "data"
    policy = jsonencode([
        {
            Rules = [
                {
                    ResourceType = "collection",
                    Resource = [
                        "collection/rag-app-collection",
                    ],
                    Permission = ["aoss:*"]
                },
                {
                    ResourceType = "index",
                    Resource = [
                        "index/rag-app-collection/*"
                    ],
                    Permission = ["aoss:*"]
                }
            ],
            Principal = [
                data.aws_caller_identity.current.arn,
                aws_iam_role.ecs_task.arn
            ]
        }
    ])
}
