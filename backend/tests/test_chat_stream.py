import json

import pytest
from fastapi.testclient import TestClient

from app.main import app, history

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_history():
    history.clear()
    yield
    history.clear()


def read_events(response) -> list[dict]:
    blocks = response.text.split("\n\n")
    return [json.loads(b.removeprefix("data: ")) for b in blocks if b.strip()]


def test_stream_sends_tokens_then_fin(monkeypatch):
    async def fake_stream(messages):
        for piece in ["Bon", "jour", " !"]:
            yield piece

    monkeypatch.setattr("app.main.stream_ollama", fake_stream)

    response = client.post("/chat/stream", json={"content": "Salut"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert read_events(response) == [
        {"type": "token", "texte": "Bon"},
        {"type": "token", "texte": "jour"},
        {"type": "token", "texte": " !"},
        {"type": "fin"},
    ]


def test_stream_saves_full_answer_in_history(monkeypatch):
    async def fake_stream(messages):
        for piece in ["Bon", "jour"]:
            yield piece

    monkeypatch.setattr("app.main.stream_ollama", fake_stream)

    client.post("/chat/stream", json={"content": "Salut"})

    assert [(m.role, m.content) for m in history] == [
        ("user", "Salut"),
        ("assistant", "Bonjour"),
    ]


def test_stream_sends_previous_messages_to_model(monkeypatch):
    received_calls = []

    async def fake_stream(messages):
        received_calls.append(list(messages))
        yield "ok"

    monkeypatch.setattr("app.main.stream_ollama", fake_stream)

    client.post("/chat/stream", json={"content": "Premier"})
    client.post("/chat/stream", json={"content": "Deuxième"})

    assert [m.content for m in received_calls[1]] == ["Premier", "ok", "Deuxième"]


def test_stream_ollama_down_sends_erreur_and_keeps_history(monkeypatch):
    async def fake_stream(messages):
        raise ConnectionError()
        yield  # rend la fonction génératrice

    monkeypatch.setattr("app.main.stream_ollama", fake_stream)

    response = client.post("/chat/stream", json={"content": "Salut"})

    assert response.status_code == 200
    assert read_events(response) == [
        {"type": "erreur", "message": "Le modèle local est indisponible"},
    ]
    assert history == []


def test_stream_rejects_empty_message():
    response = client.post("/chat/stream", json={"content": "   "})
    assert response.status_code == 422
