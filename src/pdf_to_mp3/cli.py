"""CLI: PDF/DOCX → MP3 (edge-tts o Azure Speech, español latino)."""

from pathlib import Path

import click

from .converter import ConvertOptions, convert_file
from .pdf_reader import extract_text


def main() -> None:
    """Punto de entrada de la CLI."""
    cli()


def _collect_pdfs(path: Path, recursive: bool) -> list[Path]:
    """Devuelve la lista de documentos (PDF o DOCX) a procesar (archivo único o carpeta)."""
    exts = {".pdf", ".docx"}
    if path.is_file():
        return [path] if path.suffix.lower() in exts else []
    if path.is_dir():
        pattern = "**/*" if recursive else "*"
        return sorted(
            p for p in path.glob(pattern) if p.is_file() and p.suffix.lower() in exts
        )
    return []


@click.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    metavar="FILE_OR_FOLDER",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Archivo MP3 de salida (por defecto: mismo nombre que el PDF).",
)
@click.option(
    "--engine",
    type=click.Choice(["edge-tts", "azure"], case_sensitive=False),
    default="edge-tts",
    help="Motor TTS: edge-tts (sin API key) o azure (requiere key/region).",
)
@click.option(
    "--voice",
    default=None,
    help="Voz (ej: es-MX-DaliaNeural). Por defecto: es-MX-DaliaNeural.",
)
@click.option(
    "--key",
    "api_key",
    default=None,
    envvar="AZURE_SPEECH_KEY",
    help="Azure Speech key (solo con --engine azure).",
)
@click.option(
    "--region",
    default=None,
    envvar="AZURE_SPEECH_REGION",
    help="Región de Azure, ej: eastus (solo con --engine azure).",
)
@click.option(
    "-t",
    "--save-text",
    "save_text",
    is_flag=True,
    help="Guardar el texto extraído del PDF en un .txt.",
)
@click.option(
    "--text-output",
    "text_path",
    type=click.Path(path_type=Path),
    default=None,
    metavar="TXT_FILE",
    help="Ruta del .txt (por defecto: mismo nombre que el PDF).",
)
@click.option(
    "--extract-only",
    "extract_only",
    is_flag=True,
    help="Solo extraer texto a .txt, sin convertir a MP3.",
)
@click.option(
    "--preserve-line-breaks",
    "preserve_line_breaks",
    is_flag=True,
    help="No normalizar saltos de línea (por defecto se unen para evitar pausas en TTS).",
)
@click.option(
    "-r",
    "--recursive",
    "recursive",
    is_flag=True,
    help="Si es carpeta, procesar también subcarpetas.",
)
def cli(
    input_path: Path,
    output_path: Path | None,
    engine: str,
    voice: str | None,
    api_key: str | None,
    region: str | None,
    save_text: bool,
    text_path: Path | None,
    extract_only: bool,
    preserve_line_breaks: bool,
    recursive: bool,
) -> None:
    """
    Convierte un PDF/DOCX (o todos los documentos de una carpeta) a MP3.

    Por defecto usa edge-tts (sin cuenta Azure). Usa --engine azure si
    prefieres Azure Speech (configura AZURE_SPEECH_KEY y AZURE_SPEECH_REGION).
    """
    pdf_files = _collect_pdfs(input_path, recursive)
    if not pdf_files:
        click.echo(
            click.style(
                "No se encontraron archivos PDF/DOCX en la ruta indicada.",
                fg="red",
            ),
            err=True,
        )
        raise SystemExit(1)

    if len(pdf_files) > 1:
        click.echo(f"Procesando {len(pdf_files)} archivos...\n")

    failed = 0
    for pdf_file in pdf_files:
        try:
            _process_one(
                pdf_file=pdf_file,
                output_path=output_path,
                engine=engine,
                voice=voice,
                api_key=api_key,
                region=region,
                save_text=save_text,
                text_path=text_path,
                extract_only=extract_only,
                preserve_line_breaks=preserve_line_breaks,
                batch_mode=len(pdf_files) > 1,
            )
        except (SystemExit, Exception) as e:
            failed += 1
            if not isinstance(e, SystemExit):
                click.echo(
                    click.style(f"  Error: {e}", fg="red"), err=True
                )

    if len(pdf_files) > 1:
        done = len(pdf_files) - failed
        click.echo(
            click.style(
                f"\nCompletado: {done}/{len(pdf_files)} archivos.", fg="green"
            )
        )
    if failed:
        raise SystemExit(1)


def _process_one(
    pdf_file: Path,
    output_path: Path | None,
    engine: str,
    voice: str | None,
    api_key: str | None,
    region: str | None,
    save_text: bool,
    text_path: Path | None,
    extract_only: bool,
    preserve_line_breaks: bool,
    batch_mode: bool,
) -> None:
    """Procesa un único documento (PDF o DOCX)."""
    # En modo batch, -o y --text-output se ignoran; cada PDF usa su propia ruta
    if batch_mode:
        out_mp3 = pdf_file.with_suffix(".mp3")
        out_txt = pdf_file.with_suffix(".txt")
    else:
        out_mp3 = output_path if output_path is not None else pdf_file.with_suffix(".mp3")
        out_txt = text_path if text_path is not None else pdf_file.with_suffix(".txt")

    if out_mp3.suffix.lower() != ".mp3":
        out_mp3 = out_mp3.with_suffix(".mp3")
    if out_txt.suffix.lower() != ".txt":
        out_txt = out_txt.with_suffix(".txt")

    click.echo(f"Leyendo archivo: {pdf_file}")
    try:
        opts = ConvertOptions(
            engine=engine,
            voice=voice,
            api_key=api_key,
            region=region,
            preserve_line_breaks=preserve_line_breaks,
            save_text=save_text,
        )

        if extract_only:
            text = extract_text(pdf_file, normalize_for_speech=not preserve_line_breaks)
            if not text.strip():
                click.echo(
                    click.style("El archivo no contiene texto extraíble.", fg="red"),
                    err=True,
                )
                raise SystemExit(1)
            out_txt.parent.mkdir(parents=True, exist_ok=True)
            out_txt.write_text(text, encoding="utf-8")
            click.echo(
                click.style(
                    f"Texto extraído: {len(text)} caracteres → {out_txt}", fg="green"
                )
            )
            return

        def on_progress(message: str, fraction: float) -> None:
            if "Sintetizando" in message and fraction > 0.15:
                return
            click.echo(message)

        result = convert_file(
            pdf_file,
            output_mp3=out_mp3,
            output_txt=out_txt,
            options=opts,
            on_progress=on_progress,
        )
    except SystemExit:
        raise
    except ValueError as e:
        click.echo(click.style(str(e), fg="red"), err=True)
        raise SystemExit(1) from e
    except RuntimeError as e:
        click.echo(click.style(f"Error TTS: {e}", fg="red"), err=True)
        raise SystemExit(1) from e
    except Exception as e:
        click.echo(
            click.style(f"Error al leer el archivo: {e}", fg="red"), err=True
        )
        raise SystemExit(1) from e

    click.echo(click.style(f"Listo: {result}", fg="green"))


if __name__ == "__main__":
    main()
