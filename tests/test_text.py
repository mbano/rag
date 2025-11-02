from app.utils.text import clean_tokens


class TestTextUtils:
    """Test cases for text utility functions."""

    def test_clean_tokens_basic(self):
        """Test clean_tokens with basic text."""
        text = "This is a test sentence with some words."
        result = clean_tokens(text)

        # Should return list of tokens
        assert isinstance(result, list)
        assert "test" in result
        assert "sentence" in result
        assert "words" in result

    def test_clean_tokens_removes_punctuation(self):
        """Test clean_tokens removes punctuation."""
        text = "Hello, world! How are you? I'm fine."
        result = clean_tokens(text)

        # Should not contain punctuation
        for token in result:
            assert not any(char in ".,!?;:" for char in token)

    def test_clean_tokens_removes_stopwords(self):
        """Test clean_tokens removes English stopwords."""
        text = "The quick brown fox jumps over the lazy dog"
        result = clean_tokens(text)

        # Should not contain common stopwords
        stopwords = [
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        ]
        for stopword in stopwords:
            assert stopword not in result

    def test_clean_tokens_filters_short_words(self):
        """Test clean_tokens filters out words shorter than 3 characters."""
        text = "I am a cat in the hat"
        result = clean_tokens(text)

        # Should not contain words shorter than 3 characters
        for token in result:
            assert len(token) > 2

    def test_clean_tokens_lowercase(self):
        """Test clean_tokens converts to lowercase."""
        text = "HELLO WORLD This Is A Test"
        result = clean_tokens(text)

        # All tokens should be lowercase
        for token in result:
            assert token.islower()

    def test_clean_tokens_empty_string(self):
        """Test clean_tokens with empty string."""
        result = clean_tokens("")
        assert result == []

    def test_clean_tokens_whitespace_only(self):
        """Test clean_tokens with whitespace-only string."""
        result = clean_tokens("   \n\t  ")
        assert result == []

    def test_clean_tokens_special_characters(self):
        """Test clean_tokens with special characters."""
        text = "Hello@#$%world! This&that*test"
        result = clean_tokens(text)

        # Should handle special characters gracefully
        assert isinstance(result, list)
        # Should not contain special characters
        for token in result:
            assert token.isalnum() or token.isalpha()

    def test_clean_tokens_numbers(self):
        """Test clean_tokens with numbers."""
        text = "I have 123 apples"
        result = clean_tokens(text)

        # Should include numbers as tokens
        assert "123" in result

    def test_clean_tokens_mixed_case_punctuation(self):
        """Test clean_tokens with mixed case and punctuation."""
        text = "Dr. Smith's car is a 2023 BMW!"
        result = clean_tokens(text)

        # Should handle mixed case and punctuation
        assert isinstance(result, list)
        # Should not contain punctuation
        for token in result:
            assert not any(char in ".,!?'" for char in token)

    def test_clean_tokens_long_text(self):
        """Test clean_tokens with longer text."""
        text = """
        This is a longer piece of text that contains multiple sentences.
        It has various punctuation marks, numbers like 123, and different cases.
        The quick brown fox jumps over the lazy dog in the park.
        """
        result = clean_tokens(text)

        # Should process long text correctly
        assert isinstance(result, list)
        assert len(result) > 0

        # Should contain meaningful words
        meaningful_words = [
            "longer",
            "piece",
            "text",
            "contains",
            "multiple",
            "sentences",
        ]
        for word in meaningful_words:
            assert word in result

    def test_clean_tokens_unicode(self):
        """Test clean_tokens with unicode characters."""
        text = "Café naïve résumé"
        result = clean_tokens(text)

        # Should handle unicode characters
        assert isinstance(result, list)
        # Should contain the words (possibly normalized)
        assert len(result) > 0

    def test_clean_tokens_only_stopwords(self):
        """Test clean_tokens with only stopwords."""
        text = "the a an and or but in on at to for of with by"
        result = clean_tokens(text)

        # Should return empty list since all words are stopwords
        assert result == []

    def test_clean_tokens_only_short_words(self):
        """Test clean_tokens with only short words."""
        text = "I am a an or at to"
        result = clean_tokens(text)

        # Should return empty list since all words are too short
        assert result == []

    def test_clean_tokens_only_punctuation(self):
        """Test clean_tokens with only punctuation."""
        text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = clean_tokens(text)

        # Should return empty list since no valid tokens
        assert result == []

    def test_clean_tokens_preserves_meaningful_words(self):
        """Test clean_tokens preserves meaningful words while filtering noise."""
        text = "The quick brown fox jumps over the lazy dog in the park"
        result = clean_tokens(text)

        # Should contain meaningful words
        expected_words = ["quick", "brown", "fox", "jumps", "lazy", "dog", "park"]
        for word in expected_words:
            assert word in result

        # Should not contain stopwords
        stopwords = ["the", "over", "in"]
        for stopword in stopwords:
            assert stopword not in result

    def test_clean_tokens_handles_contractions(self):
        """Test clean_tokens handles contractions."""
        text = "I'm don't won't can't shouldn't"
        result = clean_tokens(text)

        # Should handle contractions (they become separate tokens)
        assert isinstance(result, list)
        # The exact behavior depends on NLTK tokenization
        assert len(result) > 0
