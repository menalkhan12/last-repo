"""Edge-TTS plugin for LiveKit Agents: high quality, free, fast."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

import edge_tts
from livekit.agents import tts
from livekit.agents.types import APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS

# Edge-TTS typically outputs 24kHz mono MP3
SAMPLE_RATE = 24000
NUM_CHANNELS = 1
DEFAULT_VOICE = "en-US-AriaNeural"


@dataclass
class _EdgeOptions:
    voice: str
    rate: str
    volume: str


class EdgeTTS(tts.TTS):
    def __init__(
        self,
        *,
        voice: str = DEFAULT_VOICE,
        rate: str = "+0%",
        volume: str = "+0%",
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
        )
        self._opts = _EdgeOptions(voice=voice, rate=rate, volume=volume)

    @property
    def model(self) -> str:
        return "edge-tts"

    @property
    def provider(self) -> str:
        return "microsoft"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return EdgeChunkedStream(tts=self, input_text=text, conn_options=conn_options)


class EdgeChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts: EdgeTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._edge_tts: EdgeTTS = tts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        communicate = edge_tts.Communicate(
            self.input_text,
            self._edge_tts._opts.voice,
            rate=self._edge_tts._opts.rate,
            volume=self._edge_tts._opts.volume,
        )
        request_id = str(uuid.uuid4())
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=SAMPLE_RATE,
            num_channels=NUM_CHANNELS,
            mime_type="audio/mpeg",
        )
        try:
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio" and chunk.get("data"):
                    output_emitter.push(chunk["data"])
            output_emitter.flush()
        finally:
            output_emitter.end_input()
