"""IST AI Voice Agent - LiveKit worker entrypoint. STT=Groq Whisper, LLM=RAG+Groq, TTS=Edge-TTS, VAD=Silero (barge-in)."""
import asyncio
import logging
import os

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import groq, silero

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ist-agent")


async def entrypoint(ctx: JobContext):
    """Main agent entrypoint called for each LiveKit room."""
    await ctx.connect()

    # Import here to avoid issues at module load time
    try:
        from llm_rag import RAGLLM
        llm = RAGLLM(session_id=ctx.room.name or "default")
    except Exception as e:
        logger.warning("RAGLLM import failed, falling back to groq LLM: %s", e)
        from livekit.plugins import groq as groq_plugin
        llm = groq_plugin.LLM(model="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"))

    try:
        from tts_edge import EdgeTTS
        tts = EdgeTTS(voice="en-US-AriaNeural")
    except Exception as e:
        logger.warning("EdgeTTS import failed: %s", e)
        from livekit.plugins import groq as groq_plugin
        # fallback - no tts if edge unavailable
        tts = None

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=groq.STT(
            model="whisper-large-v3",
            api_key=os.getenv("GROQ_API_KEY"),
            language="en",
        ),
        llm=llm,
        tts=tts,
        allow_interruptions=True,
        interrupt_speech_duration=0.5,
        interrupt_min_words=0,
    )

    assistant.start(ctx.room)

    await assistant.say(
        "Hello! I'm the IST admissions assistant. How can I help you today?",
        allow_interruptions=True,
    )

    await asyncio.sleep(3600)  # keep alive for 1 hour max


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint)
    )