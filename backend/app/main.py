from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from ollama import chat, ChatResponse
from collections.abc import AsyncIterator
import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse
from ollama import AsyncClient, ResponseError

MAX_HISTORY_MESSAGES = 20
app = FastAPI()

class UserMessageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=4000)

class Message (BaseModel):
    role: Literal["user", "assistant"]
    content:str

@app.get("/health")
def get_status():
    return {"status": "ok"}


def call_ollama (history: list[Message]):
    response: ChatResponse = chat (
    model='qwen3:8b',
    messages=[m.model_dump() for m in history],
    options={'num_ctx': 8192},
    think = False,
)
    print (response.prompt_eval_count, response.eval_count)
    return (response['message']['content'])


def trim_history(messages, max_messages):
    if max_messages <= 0:
        return []
    return messages[-max_messages:]

history: list[Message] = []
@app.post ("/chat", response_model=Message)
def post_chat (request : UserMessageRequest):
    user_message = Message (role="user", content=request.content)
    temp_history = history + [user_message]
    trimmed_history=trim_history(temp_history,MAX_HISTORY_MESSAGES)
    try :
        response_text = call_ollama (trimmed_history)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Le modèle local est indisponible")
    assistant_message = Message (role="assistant", content=response_text)
    history.append (user_message)
    history.append (assistant_message)

    return assistant_message


# --- Streaming (phase 3) : voir docs/evenements-sse.md ---

ollama_client = AsyncClient()


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    texte: str


class ErreurEvent(BaseModel):
    type: Literal["erreur"] = "erreur"
    message: str


class FinEvent(BaseModel):
    type: Literal["fin"] = "fin"


def to_sse(event: TokenEvent | ErreurEvent | FinEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


async def stream_ollama(history: list[Message]) -> AsyncIterator[str]:
    stream = await ollama_client.chat(
        model="qwen3:8b",
        messages=[m.model_dump() for m in history],
        options={"num_ctx": 8192},
        think=False,
        stream=True,
    )
    async for chunk in stream:
        yield chunk.message.content or ""


@app.post("/chat/stream")
async def post_chat_stream(body: UserMessageRequest, request: Request):
    user_message = Message(role="user", content=body.content)
    trimmed_history = trim_history(history + [user_message], MAX_HISTORY_MESSAGES)

    async def event_flow() -> AsyncIterator[str]:
        parts: list[str] = []
        try:
            async for piece in stream_ollama(trimmed_history):
                if await request.is_disconnected():
                    return
                parts.append(piece)
                yield to_sse(TokenEvent(texte=piece))
        except (ConnectionError, httpx.ConnectError):
            yield to_sse(ErreurEvent(message="Le modèle local est indisponible"))
            return
        except ResponseError as e:
            yield to_sse(ErreurEvent(message=f"Erreur du modèle : {e.error}"))
            return

        history.append(user_message)
        history.append(Message(role="assistant", content="".join(parts)))
        yield to_sse(FinEvent())

    return StreamingResponse(
        event_flow(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )