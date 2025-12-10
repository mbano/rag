from app.config import get_settings


def test_config_loads_successfully():
    """
    Validates config structure
    """
    config = get_settings()
    assert config.rag is not None
    assert config.ingestion is not None
    assert config.evaluation is not None

    assert len(config.rag.vector_stores) > 0
    assert config.rag.nodes.analyze_query is not None
    assert config.rag.nodes.retrieve is not None
    assert config.rag.nodes.generate is not None

    # LLM configs are properly structured
    for llm in config.rag.llms.values():
        assert llm.model_name
        assert llm.model_provider


def test_config_keys_are_consistent():
    """Validates that config references point to existing keys"""
    config = get_settings()

    # Analyze query LLM key exists
    assert config.rag.nodes.analyze_query.llm_key in config.rag.llms

    # Generate LLM key exists
    assert config.rag.nodes.generate.llm_key in config.rag.llms

    # Retrieve vector store key exists
    vs_key = config.rag.nodes.retrieve.dense_vector_store_key
    assert vs_key in config.rag.vector_stores
