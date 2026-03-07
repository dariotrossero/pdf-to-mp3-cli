"""Extrae texto de archivos PDF y DOCX."""

import re
from pathlib import Path

from pypdf import PdfReader
from docx import Document


def extract_text(file_path: str | Path, normalize_for_speech: bool = True) -> str:
    """
    Lee un PDF o DOCX y devuelve todo el texto concatenado.
    Por defecto normaliza el texto para TTS
    (evita pausas en saltos de línea).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw = _extract_pdf_text(path)
    elif suffix == ".docx":
        raw = _extract_docx_text(path)
    else:
        raise ValueError(f"El archivo no es un PDF ni un DOCX: {path}")

    if normalize_for_speech:
        return _normalize_text(raw)
    return _minimal_clean(raw)


def _extract_pdf_text(path: Path) -> str:
    """Extrae texto de un PDF."""
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)

    return "\n".join(parts)


def _extract_docx_text(path: Path) -> str:
    """Extrae texto de un DOCX (párrafos concatenados con saltos de línea)."""
    doc = Document(path)
    parts: list[str] = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            parts.append(paragraph.text)
    return "\n".join(parts)


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
