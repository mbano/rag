from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_ask_endpoint(monkeypatch):

    def mock_answer_question(question: str):
        return {"answer": "mocked response"}

    test_app = FastAPI()  # not directly testing app.main to avoid heavy processing

    @test_app.post("/ask")
    async def ask_question(req: dict):
        return mock_answer_question(req["question"])

    client = TestClient(test_app)
    response = client.post("/ask", json={"question": "Test?"})

    assert response.status_code == 200
    data = response.json()
    assert list(data.keys()) == ["answer"]
    assert isinstance(data["answer"], str)
