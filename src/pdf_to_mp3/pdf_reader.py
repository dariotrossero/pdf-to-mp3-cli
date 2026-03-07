"""Extrae texto de archivos PDF."""

import re
from pathlib import Path

from pypdf import PdfReader


def extract_text(pdf_path: str | Path, normalize_for_speech: bool = True) -> str:
    """
    Lee un PDF y devuelve todo el texto concatenado.
    Por defecto normaliza el texto para TTS (evita pausas en saltos de línea).
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"El archivo no es un PDF: {path}")

    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)

    raw = "\n".join(parts)
    return _normalize_text(raw) if normalize_for_speech else _minimal_clean(raw)


def _normalize_text(text: str) -> str:
    """
    Preprocesa el texto para TTS: evita pausas en saltos de línea.
    - Une palabras partidas con guión (ej. "convenien-\\nte" → "conveniente")
    - Reemplaza saltos de línea por espacios (evita pausas en medio de frases)
    - Colapsa espacios múltiples
    """
    # 1. Palabras partidas con guión al final de línea
    text = re.sub(r"-\s*\n\s*", "", text)
    # 2. Saltos de línea → espacio (evita que el TTS pause en cada línea)
    text = re.sub(r"\n+", " ", text)
    # 3. Múltiples espacios → uno solo
    text = re.sub(r" +", " ", text)
    return text.strip()


def _minimal_clean(text: str) -> str:
    """Limpieza mínima: solo líneas vacías y espacios redundantes."""
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)
