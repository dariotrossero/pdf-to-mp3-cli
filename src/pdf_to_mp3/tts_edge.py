"""Síntesis de voz con edge-tts (motor de Edge, sin API key) a MP3."""

import asyncio
import tempfile
from pathlib import Path

import edge_tts

# Textos muy largos pueden fallar; dividir en bloques (como Azure)
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


async def _synthesize_chunk(chunk: str, voice: str, out_path: Path) -> bytes:
    """Sintetiza un bloque y devuelve los bytes del MP3."""
    communicate = edge_tts.Communicate(chunk, voice)
    await communicate.save(str(out_path))
    return out_path.read_bytes()


async def _text_to_mp3_async(
    text: str,
    output_path: Path,
    voice: str,
) -> Path:
    """Coroutine: convierte texto a MP3 con edge-tts (chunks + concatenar)."""
    chunks = _chunk_text(text)
    all_audio: list[bytes] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, chunk in enumerate(chunks):
            chunk_path = Path(tmpdir) / f"chunk_{i}.mp3"
            data = await _synthesize_chunk(chunk, voice, chunk_path)
            all_audio.append(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for data in all_audio:
            f.write(data)

    return output_path


def text_to_mp3(
    text: str,
    output_path: str | Path,
    *,
    voice: str | None = None,
) -> Path:
    """
    Convierte texto a audio MP3 usando edge-tts (motor de Edge, sin API key).
    Para textos largos, divide en chunks y concatena el audio.
    """
    output_path = Path(output_path)
    voice = voice or DEFAULT_VOICE

    if not text.strip():
        raise ValueError("El texto está vacío.")

    return asyncio.run(_text_to_mp3_async(text, output_path, voice))
