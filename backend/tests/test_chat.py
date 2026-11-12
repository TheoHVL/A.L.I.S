import pytest
from fastapi.testclient import TestClient

from app.main import app, history

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_history():
    history.clear()
    yield
    history.clear()


def test_first_chat_request_returns_assistant_response(monkeypatch):
    fake_reply = "Bonjour ! Je suis l'assistant A.L.I.S"

    def mock_call_ollama(messages):
        return fake_reply

    monkeypatch.setattr("app.main.call_ollama", mock_call_ollama)

    response = client.post("/chat", json={"content": "Bonjour"})

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "assistant"
    assert data["content"] == fake_reply


def test_memory_accumulates_across_requests(monkeypatch):
    received_calls = []

    def mock_call_ollama(messages):
        received_calls.append(list(messages))
        return f"Reponse #{len(received_calls)}"

    monkeypatch.setattr("app.main.call_ollama", mock_call_ollama)

    res1 = client.post("/chat", json={"content": "Premier message"})
    assert res1.status_code == 200

    res2 = client.post("/chat", json={"content": "Deuxieme message"})
    assert res2.status_code == 200

    assert len(received_calls) == 2

    second_call_messages = received_calls[1]
    assert len(second_call_messages) == 3

    assert second_call_messages[0].role == "user"
    assert second_call_messages[0].content == "Premier message"

    assert second_call_messages[1].role == "assistant"
    assert second_call_messages[1].content == "Reponse #1"

    assert second_call_messages[2].role == "user"
    assert second_call_messages[2].content == "Deuxieme message"


@pytest.mark.parametrize(
    "invalid_content",
    [
        "",
        "   ",
        "\t  \n",
    ],
)
def test_empty_or_whitespace_content_returns_422(invalid_content):
    response = client.post("/chat", json={"content": invalid_content})
    assert response.status_code == 422

def test_content_exceeding_max_length_returns_422():
    too_long_content = "a" * 4001
    response = client.post("/chat", json={"content": too_long_content})
    assert response.status_code == 422

def test_ollama_closed_returns_503 (monkeypatch):
    def mock_call_ollama(messages):
        raise ConnectionError()
    monkeypatch.setattr("app.main.call_ollama", mock_call_ollama)
    response = client.post("/chat", json={"content": "Premier message"})

    assert response.status_code == 503
    assert history==[]
    expected = "Le modèle local est indisponible"
    assert expected==response.json()["detail"]
