from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from app.rag_pipeline import (
    analyze_query,
    retrieve,
    generate,
    answer_question,
    Search,
    State,
)


class TestRAGPipeline:
    """Test cases for the RAG pipeline functions."""

    def test_analyze_query(self):
        """Test the analyze_query function."""
        # Mock the structured LLM
        with patch("app.rag_pipeline.llm") as mock_llm:
            mock_structured_llm = MagicMock()
            mock_llm.with_structured_output.return_value = mock_structured_llm

            # Mock the structured output
            mock_query = Search(query="test search query")
            mock_structured_llm.invoke.return_value = mock_query

            state = State(
                question="What is AI?", query=Search(query=""), context=[], answer=""
            )
            result = analyze_query(state)

            assert "query" in result
            assert result["query"] == mock_query
            mock_structured_llm.invoke.assert_called_once_with("What is AI?")

    def test_retrieve(self):
        """Test the retrieve function."""
        # Mock the rerank_retriever
        with patch("app.rag_pipeline.rerank_retriever") as mock_retriever:
            mock_docs = [
                Document(page_content="Test content 1", metadata={"source": "doc1"}),
                Document(page_content="Test content 2", metadata={"source": "doc2"}),
            ]
            mock_retriever.invoke.return_value = mock_docs

            state = State(
                question="Test question",
                query=Search(query="test query"),
                context=[],
                answer="",
            )
            result = retrieve(state)

            assert "context" in result
            assert result["context"] == mock_docs
            mock_retriever.invoke.assert_called_once_with("test query")

    def test_generate(self):
        """Test the generate function."""
        # Mock the prompt and LLM
        with patch("app.rag_pipeline.prompt") as mock_prompt, patch(
            "app.rag_pipeline.llm"
        ) as mock_llm:

            # Mock prompt invoke
            mock_messages = [{"role": "user", "content": "test prompt"}]
            mock_prompt.invoke.return_value = mock_messages

            # Mock LLM response
            mock_response = MagicMock()
            mock_response.content = "Generated answer"
            mock_llm.invoke.return_value = mock_response

            # Create test state with context
            test_docs = [
                Document(
                    page_content="Test content 1",
                    metadata={"filename": "test.pdf", "page_number": 1},
                ),
                Document(
                    page_content="Test content 2",
                    metadata={"url": "https://example.com", "page_number": 2},
                ),
            ]

            state = State(
                question="Test question",
                query=Search(query="test query"),
                context=test_docs,
                answer="",
            )

            result = generate(state)

            assert "answer" in result
            assert "Generated answer" in result["answer"]
            assert "Source: test.pdf" in result["answer"]
            assert "Source: https://example.com" in result["answer"]

            # Verify prompt was called with correct context
            expected_context = "Test content 1Test content 2"
            mock_prompt.invoke.assert_called_once_with(
                {"question": "Test question", "context": expected_context}
            )

    def test_generate_with_missing_metadata(self):
        """Test generate function with documents missing metadata."""
        with patch("app.rag_pipeline.prompt") as mock_prompt, patch(
            "app.rag_pipeline.llm"
        ) as mock_llm:

            mock_prompt.invoke.return_value = [{"role": "user", "content": "test"}]
            mock_response = MagicMock()
            mock_response.content = "Generated answer"
            mock_llm.invoke.return_value = mock_response

            # Test with minimal metadata
            test_docs = [Document(page_content="Test content", metadata={})]

            state = State(
                question="Test question",
                query=Search(query="test query"),
                context=test_docs,
                answer="",
            )

            result = generate(state)

            assert "answer" in result
            assert "Generated answer" in result["answer"]
            # Should handle missing metadata gracefully
            assert "Source: None" in result["answer"]

    @patch("app.rag_pipeline.graph")
    def test_answer_question(self, mock_graph):
        """Test the answer_question function."""
        # Mock the graph invoke
        mock_result = {
            "answer": "Final answer with sources",
            "context": [],
            "question": "Test question",
        }
        mock_graph.invoke.return_value = mock_result

        result = answer_question("Test question")

        assert result == {"answer": "Final answer with sources"}
        mock_graph.invoke.assert_called_once_with({"question": "Test question"})

    def test_search_typedict(self):
        """Test the Search TypedDict structure."""
        search = Search(query="test query")
        assert search["query"] == "test query"

        # Test that it's mutable
        search["query"] = "updated query"
        assert search["query"] == "updated query"

    def test_state_typedict(self):
        """Test the State TypedDict structure."""
        state = State(
            question="Test question",
            query=Search(query="test query"),
            context=[],
            answer="",
        )

        assert state["question"] == "Test question"
        assert state["query"]["query"] == "test query"
        assert state["context"] == []
        assert state["answer"] == ""

    def test_analyze_query_with_empty_question(self):
        """Test analyze_query with empty question."""
        with patch("app.rag_pipeline.llm") as mock_llm:
            mock_structured_llm = MagicMock()
            mock_llm.with_structured_output.return_value = mock_structured_llm
            mock_structured_llm.invoke.return_value = Search(query="")

            state = State(question="", query=Search(query=""), context=[], answer="")
            result = analyze_query(state)

            assert "query" in result
            mock_structured_llm.invoke.assert_called_once_with("")

    def test_retrieve_with_empty_query(self):
        """Test retrieve with empty query."""
        with patch("app.rag_pipeline.rerank_retriever") as mock_retriever:
            mock_retriever.invoke.return_value = []

            state = State(
                question="Test question", query=Search(query=""), context=[], answer=""
            )
            result = retrieve(state)

            assert "context" in result
            assert result["context"] == []
            mock_retriever.invoke.assert_called_once_with("")

    def test_generate_with_empty_context(self):
        """Test generate with empty context."""
        with patch("app.rag_pipeline.prompt") as mock_prompt, patch(
            "app.rag_pipeline.llm"
        ) as mock_llm:

            mock_prompt.invoke.return_value = [{"role": "user", "content": "test"}]
            mock_response = MagicMock()
            mock_response.content = "Generated answer"
            mock_llm.invoke.return_value = mock_response

            state = State(
                question="Test question",
                query=Search(query="test query"),
                context=[],
                answer="",
            )

            result = generate(state)

            assert "answer" in result
            assert "Generated answer" in result["answer"]
            # Should handle empty context gracefully
            mock_prompt.invoke.assert_called_once_with(
                {"question": "Test question", "context": ""}
            )
