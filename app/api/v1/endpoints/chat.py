"""Chat completions + conversation memory (Phase 4).

Auth: every endpoint requires the ``chat`` scope. A session belongs to
the calling key/user; asking for someone else's session returns 404.

Streaming contract (v0.4): ``POST /chat/completions?stream=true`` returns
``text/event-stream`` where the full reply is yielded word-by-word as
``data: {"delta": "<word> "}`` lines followed by ``data: [DONE]``.
There is no provider streaming because the engine is local and
deterministic — the reply is computed in full first, then streamed in word
chunks, which keeps usage accounting (model + tokens) exact for every
streamed call.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.errors import APIError
from app.core.security import require_scope
from app.schemas.chat import ChatCompletionRequest, CreateSessionRequest
from app.services.chat_service import ChatService
from app.services.creox_engine import MODEL_ID, CreoXEngine

router = APIRouter(tags=["chat"])

# Accepted model ids. "creox-brain" is a short alias for the built-in engine.
MODEL_ALIASES = {"creox": MODEL_ID, "creox-brain": MODEL_ID}


def get_adapter(temperature: float | None = None):
    """Module-level factory for the built-in engine.

    Temperature is accepted for interface compatibility but unused — the
    engine's answers are deterministic.
    """
    return CreoXEngine(temperature=temperature)


def _chat_service() -> ChatService:
    return ChatService()


@router.post("/chat/completions")
def chat_completions(payload: ChatCompletionRequest, request: Request,
                     stream: bool = False,
                     key: dict = Depends(require_scope("chat"))):
    canonical = MODEL_ALIASES.get(payload.model)
    if canonical is None:
        raise APIError(400, "unsupported_model",
                       f"Model '{payload.model}' is not supported. "
                       f"Supported models: {sorted(MODEL_ALIASES)}.")
    service = _chat_service()
    history: list[dict] = []
    session_id = payload.session_id
    if session_id is not None:
        if service.get_session(session_id, key["id"], key["user_id"]) is None:
            raise APIError(404, "session_not_found",
                           "No chat session with that id belongs to this key.")
        history = service.list_messages(session_id, key["id"], key["user_id"]) or []
    if session_id is None:
        session_id = service.create_session(key["id"], key["user_id"])["id"]
    full_messages = [{"role": m["role"], "content": m["content"]} for m in history]
    full_messages += [{"role": m.role, "content": m.content} for m in payload.messages]

    adapter = get_adapter(temperature=payload.temperature)
    result = adapter.complete(full_messages, canonical)

    for m in payload.messages:
        service.add_message(session_id, m.role, m.content)
    service.add_message(session_id, "assistant", result.reply)

    # Enrich the usage row the middleware writes for this request.
    request.state.chat_model = canonical
    request.state.chat_tokens = result.total_tokens

    body = {"reply": result.reply, "model": canonical,
            "usage": {"prompt_tokens": result.prompt_tokens,
                      "completion_tokens": result.completion_tokens,
                      "total_tokens": result.total_tokens},
            "session_id": session_id}
    if not stream:
        return body

    def _events():
        for word in result.reply.split():
            yield f"data: {json.dumps({'delta': word + ' '})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_events(), media_type="text/event-stream")


@router.post("/chat/sessions", status_code=201)
def create_session(payload: CreateSessionRequest, request: Request,
                   key: dict = Depends(require_scope("chat"))):
    return _chat_service().create_session(key["id"], key["user_id"], payload.title)


@router.get("/chat/sessions")
def list_sessions(request: Request, key: dict = Depends(require_scope("chat"))):
    return {"sessions": _chat_service().list_sessions(key["id"], key["user_id"])}


@router.get("/chat/sessions/{session_id}/messages")
def session_messages(session_id: int, request: Request,
                     key: dict = Depends(require_scope("chat"))):
    messages = _chat_service().list_messages(session_id, key["id"], key["user_id"])
    if messages is None:
        raise APIError(404, "session_not_found",
                       "No chat session with that id belongs to this key.")
    return {"session_id": session_id, "messages": messages}
