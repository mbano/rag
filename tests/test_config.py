import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from app.config import load_config, PROJECT_ROOT


class TestConfigUtils:
    """Test cases for configuration utility functions."""

    def test_project_root(self):
        """Test PROJECT_ROOT is set correctly."""
        # Should be the parent directory of the config.py file
        expected_root = Path(__file__).resolve().parents[1]  # tests/ -> rag/ -> parent
        assert PROJECT_ROOT == expected_root

    def test_load_config_valid_yaml(self):
        """Test load_config with valid YAML configuration."""
        test_config = {
            "embedding_model": "text-embedding-3-large",
            "vector_store": "faiss",
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "retriever_params": {"k": 10},
            "reranker_params": {"model": "rerank-v3.5", "top_n": 4},
        }

        yaml_content = yaml.dump(test_config)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result == test_config
            assert result["embedding_model"] == "text-embedding-3-large"
            assert result["vector_store"] == "faiss"
            assert result["chunk_size"] == 1000

    def test_load_config_file_not_found(self):
        """Test load_config when config file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                load_config()

    def test_load_config_invalid_yaml(self):
        """Test load_config with invalid YAML content."""
        invalid_yaml = "invalid: yaml: content: ["

        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(yaml.YAMLError):
                load_config()

    def test_load_config_empty_file(self):
        """Test load_config with empty file."""
        with patch("builtins.open", mock_open(read_data="")):
            result = load_config()
            assert result is None

    def test_load_config_nested_structure(self):
        """Test load_config with nested YAML structure."""
        test_config = {
            "embedding_model": "text-embedding-3-large",
            "loader_params": {
                "pdf": {
                    "strategy": "hi_res",
                    "chunking_strategy": "by_title",
                    "infer_table_structure": True,
                },
                "web": {"max_characters": 500},
            },
            "retriever_params": {"k": 10},
        }

        yaml_content = yaml.dump(test_config)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result == test_config
            assert result["loader_params"]["pdf"]["strategy"] == "hi_res"
            assert result["loader_params"]["pdf"]["infer_table_structure"] is True
            assert result["retriever_params"]["k"] == 10

    def test_load_config_with_comments(self):
        """Test load_config with YAML containing comments."""
        yaml_content = """
        # Configuration file
        embedding_model: "text-embedding-3-large"  # OpenAI model
        vector_store: "faiss"  # Vector store type
        chunk_size: 1000  # Chunk size in characters
        chunk_overlap: 100  # Overlap between chunks
        """

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result["embedding_model"] == "text-embedding-3-large"
            assert result["vector_store"] == "faiss"
            assert result["chunk_size"] == 1000
            assert result["chunk_overlap"] == 100

    def test_load_config_with_booleans(self):
        """Test load_config with boolean values."""
        test_config = {
            "infer_table_structure": True,
            "enable_reranking": False,
            "use_hybrid_search": True,
        }

        yaml_content = yaml.dump(test_config)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result["infer_table_structure"] is True
            assert result["enable_reranking"] is False
            assert result["use_hybrid_search"] is True

    def test_load_config_with_numbers(self):
        """Test load_config with various number types."""
        test_config = {
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "max_characters": 500,
            "top_n": 4,
            "k": 10,
            "learning_rate": 0.001,
        }

        yaml_content = yaml.dump(test_config)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result["chunk_size"] == 1000
            assert result["chunk_overlap"] == 100
            assert result["max_characters"] == 500
            assert result["top_n"] == 4
            assert result["k"] == 10
            assert result["learning_rate"] == 0.001

    def test_load_config_with_lists(self):
        """Test load_config with list values."""
        test_config = {
            "supported_formats": ["pdf", "docx", "txt"],
            "retriever_types": ["dense", "sparse", "hybrid"],
            "model_versions": ["v1", "v2", "v3"],
        }

        yaml_content = yaml.dump(test_config)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result["supported_formats"] == ["pdf", "docx", "txt"]
            assert result["retriever_types"] == ["dense", "sparse", "hybrid"]
            assert result["model_versions"] == ["v1", "v2", "v3"]

    def test_load_config_with_null_values(self):
        """Test load_config with null values."""
        test_config = {
            "api_key": None,
            "endpoint": "https://api.example.com",
            "timeout": None,
        }

        yaml_content = yaml.dump(test_config)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result["api_key"] is None
            assert result["endpoint"] == "https://api.example.com"
            assert result["timeout"] is None

    def test_load_config_file_path(self):
        """Test that load_config reads from the correct file path."""
        with patch("builtins.open", mock_open(read_data="test: value")) as mock_file:
            load_config()

            # Should open the config file in the project root
            expected_path = PROJECT_ROOT / "config.yaml"
            mock_file.assert_called_once_with(expected_path, "r")

    def test_load_config_encoding(self):
        """Test load_config handles file encoding correctly."""
        test_config = {
            "description": "Test configuration with unicode: café, naïve",
            "model": "text-embedding-3-large",
        }

        yaml_content = yaml.dump(test_config, allow_unicode=True)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert (
                result["description"] == "Test configuration with unicode: café, naïve"
            )
            assert result["model"] == "text-embedding-3-large"

    def test_load_config_large_file(self):
        """Test load_config with a large configuration file."""
        large_config = {f"param_{i}": f"value_{i}" for i in range(1000)}
        large_config.update(
            {"embedding_model": "text-embedding-3-large", "vector_store": "faiss"}
        )

        yaml_content = yaml.dump(large_config)

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert len(result) == 1002  # 1000 params + 2 additional
            assert result["embedding_model"] == "text-embedding-3-large"
            assert result["vector_store"] == "faiss"
            assert result["param_0"] == "value_0"
            assert result["param_999"] == "value_999"

    def test_load_config_with_anchors(self):
        """Test load_config with YAML anchors and aliases."""
        yaml_content = """
        default_params: &default_params
          k: 10
          top_n: 4

        retriever_params: *default_params
        reranker_params: *default_params
        """

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_config()

            assert result["retriever_params"]["k"] == 10
            assert result["retriever_params"]["top_n"] == 4
            assert result["reranker_params"]["k"] == 10
            assert result["reranker_params"]["top_n"] == 4
