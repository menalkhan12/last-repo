"""RAG-backed LLM for LiveKit: wraps app.llm.get_response and streams a single ChatChunk."""
from __future__ import annotations

import asyncio
from livekit.agents import llm
from livekit.agents.llm import ChatChunk, ChoiceDelta, CompletionUsage, LLMStream
from livekit.agents.types import APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS
from livekit.agents.llm.chat_context import ChatContext

from app.llm import get_response
from app.lead_capture import extract_pakistani_phone, log_lead


def _chat_ctx_to_history(chat_ctx: ChatContext) -> list:
    """Convert ChatContext to list of (user, assistant) turns for get_response."""
    history = []
    for msg in chat_ctx.messages:
        if msg.role == "user" and msg.content:
            history.append((msg.content, ""))
        elif msg.role == "assistant" and msg.content and history:
            user, _ = history[-1]
            history[-1] = (user, msg.content)
    return history


class RAGLLM(llm.LLM):
    """LLM that uses RAG + Groq and streams one chunk. Handles escalation and lead capture."""

    def __init__(self, *, session_id: str | None = None) -> None:
        super().__init__()
        self._session_id = session_id or ""

    @property
    def model(self) -> str:
        return "llama-3.3-70b-versatile"

    @property
    def provider(self) -> str:
        return "groq-rag"

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: list | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        **kwargs,
    ) -> LLMStream:
        tools = tools or []
        return RAGLLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=conn_options,
            session_id=self._session_id,
        )


class RAGLLMStream(LLMStream):
    def __init__(self, *, session_id: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._session_id = session_id

    async def _run(self) -> None:
        chat_ctx = self.chat_ctx
        last_user = ""
        for m in reversed(chat_ctx.messages):
            if m.role == "user" and m.content:
                last_user = m.content
                break
        if not last_user:
            return
        phone = extract_pakistani_phone(last_user)
        history = _chat_ctx_to_history(chat_ctx)
        if history and not history[-1][1]:
            history = history[:-1]
        loop = asyncio.get_event_loop()
        reply, should_escalate = await loop.run_in_executor(
            None,
            lambda: get_response(last_user, history=history, session_id=self._session_id or None),
        )
        # Log lead when user provides Pakistani phone (e.g. callback request)
        if phone and self._session_id:
            await loop.run_in_executor(
                None,
                lambda: log_lead(phone, last_user, self._session_id),
            )
        request_id = getattr(self, "_request_id", "rag-1")
        chunk = ChatChunk(
            id=request_id,
            delta=ChoiceDelta(role="assistant", content=reply),
            usage=CompletionUsage(
                completion_tokens=len(reply.split()) + 1,
                prompt_tokens=0,
                total_tokens=len(reply.split()) + 1,
            ),
        )
        self._event_ch.send_nowait(chunk)
