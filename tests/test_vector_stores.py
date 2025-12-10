def test_vector_store_registry_has_required_types():
    """Test that all configured vector store types are registered"""
    from app.utils.vector_stores import VS_REGISTRY, VectorStoreType

    # Check that registry has entries for supported types
    assert VectorStoreType.FAISS in VS_REGISTRY
    assert VectorStoreType.OPENSEARCH in VS_REGISTRY

    # Each entry should have load and create functions
    for vs_type, funcs in VS_REGISTRY.items():
        assert "load" in funcs
        assert "create" in funcs
        assert callable(funcs["load"])
        assert callable(funcs["create"])


def test_vector_store_config_matches_registry():
    """Test that config references valid vector store types"""
    from app.utils.vector_stores import VS_REGISTRY
    from app.config import load_config

    config = load_config()

    # All configured vector stores should be in registry
    for vs_name, vs_config in config.rag.vector_stores.items():
        assert (
            vs_config.type in VS_REGISTRY
        ), f"Vector store type '{vs_config.type}' not in registry"
