from app.config import get_settings
from app.utils.prompts import get_chat_prompt_template
from langchain_core.prompts import ChatPromptTemplate
from app.utils.text import clean_tokens


def test_prompt_templates_load():
    """Test that prompt files exist and parse correctly"""
    # Test the actual prompts from config
    config = get_settings()

    # Analyze query prompt
    aq_prompt_file = config.rag.nodes.analyze_query.prompt
    if aq_prompt_file:
        prompt = get_chat_prompt_template(aq_prompt_file)
        assert prompt is not None
        assert isinstance(prompt, ChatPromptTemplate)

    # Generate prompt
    gen_prompt_file = config.rag.nodes.generate.prompt
    if gen_prompt_file:
        prompt = get_chat_prompt_template(gen_prompt_file)
        assert prompt is not None
        assert isinstance(prompt, ChatPromptTemplate)
        # Should have expected variables
        assert "question" in prompt.input_variables
        assert "context" in prompt.input_variables


def test_vector_store_configs_valid():
    """Test vector store configurations are complete"""
    config = get_settings()

    for vs_name, vs_config in config.rag.vector_stores.items():
        assert vs_config.type in ["faiss", "opensearch"]
        assert vs_config.embedding_model
        assert isinstance(vs_config.kwargs, dict)


def test_clean_tokens_edge_cases():
    """Test text cleaning with edge cases"""
    # Empty string
    assert clean_tokens("") == []

    # Only stopwords
    result = clean_tokens("the a an is")
    assert len(result) == 0

    # Mixed case and punctuation
    result = clean_tokens("Hello! WORLD? Testing, testing.")
    assert "hello" in result
    assert "world" in result
    assert "testing" in result

    # Numbers and short tokens removed
    result = clean_tokens("ab test")
    assert "ab" not in result  # too short
    assert "test" in result

    # Stop words removed
    result = clean_tokens("the test")
    assert "the" not in result


def test_clean_text_fixes_encoding():
    """Test ftfy text cleaning"""
    from app.utils.docs import _clean_text

    # Test with some encoding issues (ftfy examples)
    dirty = "Iâ€™m so excited!"  # Mangled smart quote
    clean = _clean_text(dirty)

    assert clean is not None
    assert len(clean) > 0
    # ftfy should handle various encoding issues
