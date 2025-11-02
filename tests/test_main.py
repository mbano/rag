from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app, QueryRequest


class TestMainAPI:
    """Test cases for the main FastAPI application."""

    def test_root_endpoint(self):
        """Test the root status endpoint."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "status OK"

    @patch("app.main.answer_question")
    def test_ask_endpoint_success(self, mock_answer_question):
        """Test the /ask endpoint with successful response."""
        # Mock the answer_question function
        mock_answer_question.return_value = {"answer": "Test response"}

        client = TestClient(app)
        response = client.post(
            "/ask", json={"question": "What is the meaning of life?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "Test response"
        mock_answer_question.assert_called_once_with("What is the meaning of life?")

    def test_ask_endpoint_invalid_request(self):
        """Test the /ask endpoint with invalid request data."""
        client = TestClient(app)

        # Test missing question field
        response = client.post("/ask", json={})
        assert response.status_code == 422

        # Test invalid JSON
        response = client.post("/ask", data="invalid json")
        assert response.status_code == 422

    #  TODO maybe fix in QueryRequest?
    def _test_ask_endpoint_empty_question(self):
        """Test the /ask endpoint with empty question."""
        client = TestClient(app)
        response = client.post("/ask", json={"question": ""})

        # Should still be valid request, but might return empty answer
        assert response.status_code == 200

    #  TODO
    @patch("app.main.answer_question")
    def _test_ask_endpoint_exception_handling(self, mock_answer_question):
        """Test the /ask endpoint when answer_question raises an exception."""
        # Mock the answer_question function to raise an exception
        mock_answer_question.side_effect = Exception("RAG pipeline error")

        client = TestClient(app)
        response = client.post("/ask", json={"question": "Test question"})

        # FastAPI should handle the exception and return 500
        assert response.status_code == 500

    def test_query_request_model(self):
        """Test the QueryRequest Pydantic model."""
        # Valid request
        valid_request = QueryRequest(question="What is AI?")
        assert valid_request.question == "What is AI?"

        # Test with different question types
        questions = [
            "Simple question?",
            "Question with numbers: 123",
            "Question with special chars: @#$%",
            "Very long question " * 100,
        ]

        for question in questions:
            request = QueryRequest(question=question)
            assert request.question == question
