"""IST AI Voice Agent - LiveKit worker entrypoint. STT=Groq Whisper, LLM=RAG+Groq, TTS=Edge-TTS, VAD=Silero (barge-in)."""
import asyncio
import logging
import os

from dotenv import load_dotenv
from livekit.agents import AgentServer, JobContext, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import groq, silero

from app.llm_rag import RAGLLM
from app.rag import get_rag
from app.tts_edge import EdgeTTS

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ist-agent")


def _make_session(session_id: str) -> AgentSession:
    """Build AgentSession with Groq STT, RAG LLM, Edge-TTS, Silero VAD. Barge-in enabled via VAD."""
    return AgentSession(
        stt=groq.STT(
            model="whisper-large-v3",
            api_key=os.getenv("GROQ_API_KEY"),
            language="en",
        ),
        llm=RAGLLM(session_id=session_id),
        tts=EdgeTTS(voice="en-US-AriaNeural"),
        vad=silero.VAD.load(),
        allow_interruptions=True,
    )


class ISTAgent(Agent):
    """Single agent: RAG-grounded IST admissions assistant."""

    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are the official voice assistant for the Institute of Space Technology (IST) Admissions. "
                "Answer only from the context provided to you. Be concise (1-2 sentences). "
                "Do not repeat the user's question. Do not apologize or say 'I think'."
            ),
        )


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    # Prewarm RAG so first user message is fast
    try:
        get_rag()
    except Exception as e:
        logger.warning("RAG prewarm failed: %s", e)
    await ctx.connect()
    session_id = ctx.room.name or getattr(ctx.job, "id", "unknown")
    session = _make_session(session_id)
    agent = ISTAgent()
    await session.start(agent=agent, room=ctx.room)
    logger.info("IST agent started for room %s", session_id)


if __name__ == "__main__":
    cli.run_app(server)
