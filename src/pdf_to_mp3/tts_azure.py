"""Síntesis de voz con Azure Speech SDK (TTS) a MP3, español latino."""

import os
from collections.abc import Callable
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk

# Límite recomendado por petición (Azure ~5000 caracteres)
CHUNK_SIZE = 4000

# Español latino por defecto (México)
DEFAULT_VOICE = "es-MX-DaliaNeural"


def _chunk_text(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Divide el texto en bloques sin cortar palabras en medio."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    while text:
        if len(text) <= max_chars:
            chunks.append(text)
            break
        break_at = text.rfind(" ", 0, max_chars + 1)
        if break_at == -1:
            break_at = max_chars
        chunks.append(text[:break_at].strip())
        text = text[break_at:].strip()
    return chunks


def _get_speech_config(
    *,
    key: str | None = None,
    region: str | None = None,
    voice: str | None = None,
) -> speechsdk.SpeechConfig:
    key = key or os.environ.get("AZURE_SPEECH_KEY")
    region = region or os.environ.get("AZURE_SPEECH_REGION")
    voice = voice or os.environ.get("AZURE_SPEECH_VOICE") or DEFAULT_VOICE

    if not key or not region:
        raise ValueError(
            "Faltan credenciales de Azure. Configura AZURE_SPEECH_KEY y "
            "AZURE_SPEECH_REGION (o pasa --key y --region por CLI)."
        )

    config = speechsdk.SpeechConfig(subscription=key, region=region)
    config.speech_synthesis_voice_name = voice
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )
    return config


def text_to_mp3(
    text: str,
    output_path: str | Path,
    *,
    key: str | None = None,
    region: str | None = None,
    voice: str | None = None,
    on_chunk: Callable[[int, int], None] | None = None,
) -> Path:
    """
    Convierte texto a audio MP3 usando Azure TTS.
    Para textos largos, divide en chunks y concatena el audio.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not text.strip():
        raise ValueError("El texto está vacío.")

    config = _get_speech_config(key=key, region=region, voice=voice)
    chunks = _chunk_text(text)

    # Sin AudioConfig para obtener bytes en memoria y concatenar
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=config, audio_config=None
    )
    all_audio: list[bytes] = []

    total = len(chunks)
    for i, chunk in enumerate(chunks):
        result = synthesizer.speak_text_async(chunk).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            all_audio.append(result.audio_data)
            if on_chunk is not None:
                on_chunk(i + 1, total)
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            raise RuntimeError(
                f"Azure TTS cancelado: {cancellation.reason}. "
                f"Detalle: {cancellation.error_details}"
            )
        else:
            raise RuntimeError(f"Síntesis fallida: {result.reason}")

    with open(output_path, "wb") as f:
        for data in all_audio:
            f.write(data)

    return output_path
