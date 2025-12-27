resource "aws_cognito_user_pool" "pool" {
    name = "${var.app_name}-user-pool"

    auto_verified_attributes = ["email"]
    username_attributes = ["email"]

    admin_create_user_config {
        allow_admin_create_user_only = false
    }

    tags = {
        Name = "${var.app_name}-user-pool"
    }
}

resource "aws_cognito_user_pool_domain" "main" {
    domain       = "${var.app_name}-auth-${random_id.cognito_suffix.hex}"
    user_pool_id = aws_cognito_user_pool.pool.id
}

resource "aws_cognito_user_pool_client" "public" {
    name         = "${var.app_name}-public-client"
    user_pool_id = aws_cognito_user_pool.pool.id

    generate_secret = false

    # allow non-hosted-UI auth for CLI
    explicit_auth_flows = [
        "ALLOW_USER_PASSWORD_AUTH",
        "ALLOW_REFRESH_TOKEN_AUTH",
        "ALLOW_ADMIN_USER_PASSWORD_AUTH"
    ]

    # OAuth config
    allowed_oauth_flows_user_pool_client = true
    allowed_oauth_flows = ["code"]
    allowed_oauth_scopes = [
        "openid",
        "email",
        "profile",
        "${aws_cognito_resource_server.api.identifier}/rag.query",
        "${aws_cognito_resource_server.api.identifier}/ingest.write"
    ]

    callback_urls = [
        "http://localhost:8000/docs/oauth2-redirect"
    ]
    logout_urls = [
        "http://localhost:8000/docs"
    ]

    supported_identity_providers = ["COGNITO"]

    access_token_validity = 60
    id_token_validity = 60
    refresh_token_validity = 30

    token_validity_units {
      access_token = "minutes"
      id_token = "minutes"
      refresh_token = "days"
    }
}

resource "aws_cognito_user_group" "admin" {
    name         = "admin"
    user_pool_id = aws_cognito_user_pool.pool.id
    description  = "Admin permissions"
}

resource "aws_cognito_user_group" "demo_user" {
    name         = "demo_user"
    user_pool_id = aws_cognito_user_pool.pool.id
    description  = "Can call query endpoints"
}

resource "aws_cognito_resource_server" "cognito_resource_server"{
    identifier = "https://api.${var.app_name}"
    name = "${var.app_name}-api"
    user_pool_id = aws_cognito_user_pool.pool.id

    scope {
      scope_name = "rag.query"
      scope_description = "Permission to call RAG query endpoints"
    }

    scope {
      scope_name = "ingest.write"
      scope_description = "Permissions to run ingestion write operations"
    }
}
