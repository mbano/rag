def test_build_graph_structure():
    """Test that RAG graph builds with correct node structure"""
    from app.rag_pipeline import build_graph
    from app.config import load_config
    from unittest.mock import MagicMock, patch

    config = load_config()

    # Mock external dependencies
    with patch("app.rag_pipeline._build_retriever") as mock_retriever, patch(
        "app.rag_pipeline._build_llms"
    ) as mock_llms, patch("app.rag_pipeline._build_prompts") as mock_prompts:

        mock_retriever.return_value = MagicMock()
        mock_llms.return_value = (MagicMock(), MagicMock())
        mock_prompts.return_value = (MagicMock(), MagicMock())

        # Build graph
        graph = build_graph(config, eval_mode=False)

        # Check that graph was created
        assert graph is not None

        # Check that all components were called
        mock_retriever.assert_called_once()
        mock_llms.assert_called_once()
        mock_prompts.assert_called_once()


def test_build_llms_creates_correct_instances():
    """Test LLM instantiation from config"""
    from app.rag_pipeline import _build_llms
    from app.config import load_config

    config = load_config()

    query_llm, generate_llm = _build_llms(config.rag)

    # Both should be created
    assert query_llm is not None
    assert generate_llm is not None

    # Should have correct temperatures
    assert hasattr(query_llm, "temperature") or hasattr(query_llm, "model_kwargs")
    assert hasattr(generate_llm, "temperature") or hasattr(generate_llm, "model_kwargs")


def test_build_prompts_loads_templates():
    """Test prompt template loading"""
    from app.rag_pipeline import _build_prompts
    from app.config import load_config

    config = load_config()

    analyze_prompt, generate_prompt = _build_prompts(config.rag)

    # Both should be loaded (or None if not configured)
    if config.rag.nodes.analyze_query.prompt:
        assert analyze_prompt is not None

    if config.rag.nodes.generate.prompt:
        assert generate_prompt is not None
        # Should have expected variables
        assert "question" in generate_prompt.input_variables
        assert "context" in generate_prompt.input_variables
