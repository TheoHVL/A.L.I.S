from typing import Literal

from fastapi import FastAPI, HTTPException
from ollama import ChatResponse, chat
from pydantic import BaseModel, ConfigDict, Field

MAX_HISTORY_MESSAGES = 20
app = FastAPI()


class UserMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=4000)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


@app.get("/health")
def get_status():
    return {"status": "ok"}


def call_ollama(history: list[Message]):
    response: ChatResponse = chat(
        model="qwen3:8b",
        messages=[m.model_dump() for m in history],
        options={"num_ctx": 8192},
        think=False,
    )
    return response["message"]["content"]


def trim_history(messages, max_messages):
    if max_messages <= 0:
        return []
    return messages[-max_messages:]


history: list[Message] = []


@app.post("/chat", response_model=Message)
def post_chat(request: UserMessageRequest):
    user_message = Message(role="user", content=request.content)
    temp_history = history + [user_message]
    trimmed_history = trim_history(temp_history, MAX_HISTORY_MESSAGES)
    try:
        response_text = call_ollama(trimmed_history)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Le modèle local est indisponible")
    assistant_message = Message(role="assistant", content=response_text)
    history.append(user_message)
    history.append(assistant_message)

    return assistant_message
