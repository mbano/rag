from app.utils.urls import url_to_resource_name


class TestUrlsUtils:
    """Test cases for URL utility functions."""

    def test_url_to_resource_name_basic(self):
        """Test url_to_resource_name with basic URL."""
        url = "https://example.com/page"
        result = url_to_resource_name(url)

        assert isinstance(result, str)
        assert "example.com" in result
        assert "page" in result
        assert len(result) > 0

    def test_url_to_resource_name_with_path(self):
        """Test url_to_resource_name with URL containing path."""
        url = "https://example.com/articles/2023/01/15/my-article"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert "articles" in result
        assert "2023" in result
        assert "01" in result
        assert "15" in result
        assert "my-article" in result

    def test_url_to_resource_name_with_query_params(self):
        """Test url_to_resource_name with query parameters."""
        url = "https://example.com/search?q=test&category=news"
        result = url_to_resource_name(url)

        # Should handle query parameters
        assert "example.com" in result
        assert "search" in result

    def test_url_to_resource_name_with_fragment(self):
        """Test url_to_resource_name with URL fragment."""
        url = "https://example.com/page#section1"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert "page" in result

    def test_url_to_resource_name_with_port(self):
        """Test url_to_resource_name with port number."""
        url = "https://example.com:8080/api/v1/data"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert "api" in result
        assert "v1" in result
        assert "data" in result

    def test_url_to_resource_name_with_subdomain(self):
        """Test url_to_resource_name with subdomain."""
        url = "https://blog.example.com/posts/hello-world"
        result = url_to_resource_name(url)

        assert "blog.example.com" in result
        assert "posts" in result
        assert "hello-world" in result

    def test_url_to_resource_name_special_characters(self):
        """Test url_to_resource_name with special characters."""
        url = "https://example.com/path/with/special@chars#and!symbols"
        result = url_to_resource_name(url)

        # Should replace special characters with underscores
        assert "example.com" in result
        assert "_" in result  # Special chars should be replaced
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result

    def test_url_to_resource_name_unicode(self):
        """Test url_to_resource_name with unicode characters."""
        url = "https://example.com/café/naïve/résumé"
        result = url_to_resource_name(url)

        # Should handle unicode characters
        assert isinstance(result, str)
        assert len(result) > 0

    def test_url_to_resource_name_empty_path(self):
        """Test url_to_resource_name with empty path."""
        url = "https://example.com"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert len(result) > 0

    def test_url_to_resource_name_root_path(self):
        """Test url_to_resource_name with root path."""
        url = "https://example.com/"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert len(result) > 0

    def test_url_to_resource_name_multiple_slashes(self):
        """Test url_to_resource_name with multiple consecutive slashes."""
        url = "https://example.com//path//with//slashes"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert "path" in result
        assert "with" in result
        assert "slashes" in result

    def test_url_to_resource_name_very_long_url(self):
        """Test url_to_resource_name with very long URL."""
        long_path = "/" + "/".join([f"segment{i}" for i in range(100)])
        url = f"https://example.com{long_path}"
        result = url_to_resource_name(url)

        # Should handle long URLs
        assert isinstance(result, str)
        assert len(result) > 0
        assert "example.com" in result

    def test_url_to_resource_name_different_protocols(self):
        """Test url_to_resource_name with different protocols."""
        urls = [
            "http://example.com/page",
            "https://example.com/page",
            "ftp://example.com/file",
            "file:///local/path",
        ]

        for url in urls:
            result = url_to_resource_name(url)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_url_to_resource_name_consistency(self):
        """Test url_to_resource_name produces consistent results."""
        url = "https://example.com/test-page"

        # Should produce same result multiple times
        result1 = url_to_resource_name(url)
        result2 = url_to_resource_name(url)

        assert result1 == result2

    def test_url_to_resource_name_hash_uniqueness(self):
        """Test url_to_resource_name includes hash for uniqueness."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"

        result1 = url_to_resource_name(url1)
        result2 = url_to_resource_name(url2)

        # Results should be different
        assert result1 != result2

        # Both should contain the domain
        assert "example.com" in result1
        assert "example.com" in result2

    def test_url_to_resource_name_handles_underscores(self):
        """Test url_to_resource_name handles existing underscores."""
        url = "https://example.com/path_with_underscores"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert "path" in result
        assert "with" in result
        assert "underscores" in result

    def test_url_to_resource_name_handles_dashes(self):
        """Test url_to_resource_name handles dashes."""
        url = "https://example.com/path-with-dashes"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert "path" in result
        assert "with" in result
        assert "dashes" in result

    def test_url_to_resource_name_handles_numbers(self):
        """Test url_to_resource_name handles numbers."""
        url = "https://example.com/page123"
        result = url_to_resource_name(url)

        assert "example.com" in result
        assert "page" in result
        assert "123" in result

    def test_url_to_resource_name_handles_mixed_case(self):
        """Test url_to_resource_name handles mixed case."""
        url = "https://Example.COM/Path/With/MixedCase"
        result = url_to_resource_name(url)

        # Should handle mixed case (exact behavior depends on implementation)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_url_to_resource_name_very_short_url(self):
        """Test url_to_resource_name with very short URL."""
        url = "https://a.co"
        result = url_to_resource_name(url)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_url_to_resource_name_invalid_url(self):
        """Test url_to_resource_name with invalid URL format."""
        # This should still work as urlparse is quite permissive
        url = "not-a-valid-url"
        result = url_to_resource_name(url)

        assert isinstance(result, str)
        assert len(result) > 0
