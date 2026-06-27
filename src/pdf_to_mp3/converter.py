"""Lógica compartida de conversión PDF/DOCX → MP3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .pdf_reader import extract_text
from .tts_azure import text_to_mp3 as text_to_mp3_azure
from .tts_edge import text_to_mp3 as text_to_mp3_edge

ProgressCallback = Callable[[str, float], None]
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


@dataclass
class ConvertOptions:
    engine: str = "edge-tts"
    voice: str | None = None
    api_key: str | None = None
    region: str | None = None
    preserve_line_breaks: bool = False
    save_text: bool = False


def convert_file(
    pdf_file: Path,
    *,
    output_mp3: Path | None = None,
    output_txt: Path | None = None,
    options: ConvertOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> Path:
    """Convierte un PDF/DOCX a MP3. Devuelve la ruta del MP3 generado."""

    def report(message: str, fraction: float) -> None:
        if on_progress is not None:
            on_progress(message, fraction)

    opts = options or ConvertOptions()
    out_mp3 = output_mp3 if output_mp3 is not None else pdf_file.with_suffix(".mp3")
    out_txt = output_txt if output_txt is not None else pdf_file.with_suffix(".txt")

    report(f"Leyendo: {pdf_file.name}", 0.0)
    text = extract_text(pdf_file, normalize_for_speech=not opts.preserve_line_breaks)

    if not text.strip():
        raise ValueError("El archivo no contiene texto extraíble.")

    if opts.save_text:
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_text(text, encoding="utf-8")

    report(f"Sintetizando: {pdf_file.name}", 0.15)

    def on_chunk(current: int, total: int) -> None:
        fraction = 0.15 + (0.85 * current / total) if total else 1.0
        report(f"Sintetizando {pdf_file.name} ({current}/{total})", fraction)

    if opts.engine == "edge-tts":
        result = text_to_mp3_edge(text, out_mp3, voice=opts.voice, on_chunk=on_chunk)
    else:
        result = text_to_mp3_azure(
            text,
            out_mp3,
            key=opts.api_key,
            region=opts.region,
            voice=opts.voice,
            on_chunk=on_chunk,
        )

    report(f"Listo: {pdf_file.name}", 1.0)
    return result


def convert_batch(
    files: list[Path],
    *,
    options: ConvertOptions | None = None,
    on_progress: ProgressCallback | None = None,
) -> list[tuple[Path, Path | Exception]]:
    """Convierte varios archivos. Devuelve (archivo, resultado o error) por cada uno."""
    results: list[tuple[Path, Path | Exception]] = []
    total = len(files)

    for index, pdf_file in enumerate(files):
        base_fraction = index / total

        def file_progress(message: str, fraction: float) -> None:
            if on_progress is not None:
                overall = base_fraction + (fraction / total)
                on_progress(message, overall)

        try:
            mp3_path = convert_file(
                pdf_file,
                options=options,
                on_progress=file_progress,
            )
            results.append((pdf_file, mp3_path))
        except Exception as exc:
            results.append((pdf_file, exc))

    if on_progress is not None:
        on_progress("Completado", 1.0)

    return results
