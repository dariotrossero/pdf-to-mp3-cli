# PDF a MP3 (CLI) — Español Latino

CLI en Python que convierte un PDF a archivo MP3. Por defecto usa **edge-tts** (motor de Microsoft Edge, sin API key). Opcionalmente puedes usar **Azure Speech SDK** con `--engine azure`.

## Requisitos

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (gestor de proyecto y dependencias)
- **Con edge-tts (por defecto):** no necesitas cuenta Azure.
- **Con Azure:** cuenta Azure y recurso **Speech** (Cognitive Services).

## Instalación

```powershell
cd pdf-to-mp3-cli
uv sync
```

## Uso (edge-tts por defecto, sin configuración)

```powershell
# Un PDF: salida mismo nombre con extensión .mp3
uv run pdf2mp3 documento.pdf

# Una carpeta: convierte todos los PDFs de la carpeta
uv run pdf2mp3 C:\ruta\a\mis-pdfs

# Carpeta con subcarpetas (-r)
uv run pdf2mp3 C:\ruta\a\mis-pdfs -r

# Especificar archivo de salida (solo con un PDF)
uv run pdf2mp3 documento.pdf -o mi-audio.mp3

# Otra voz (español latino)
uv run pdf2mp3 documento.pdf --voice es-MX-JorgeNeural

# Guardar también el texto extraído (documento.txt)
uv run pdf2mp3 documento.pdf -t

# Solo extraer texto (sin MP3)
uv run pdf2mp3 documento.pdf --extract-only

# Solo extraer de una carpeta
uv run pdf2mp3 C:\mis-pdfs --extract-only
```

## Usar Azure en lugar de edge-tts

Si prefieres el motor oficial de Azure (por ejemplo para SSML o cuotas propias):

1. En [Azure Portal](https://portal.azure.com) crea un recurso **Speech**.
2. Copia **Key 1** y **Region** (por ejemplo `eastus`).
3. Configura variables o pasa opciones:

```powershell
$env:AZURE_SPEECH_KEY = "tu_key"
$env:AZURE_SPEECH_REGION = "eastus"
uv run pdf2mp3 documento.pdf --engine azure
```

O en una sola línea:

```powershell
uv run pdf2mp3 documento.pdf --engine azure --key TU_KEY --region eastus
```

## Opciones de la CLI

| Opción | Descripción |
|--------|-------------|
| `--engine edge-tts` | Motor Edge (por defecto, sin API key) |
| `--engine azure` | Azure Speech SDK (requiere key y region) |
| `-o, --output` | Archivo MP3 de salida |
| `-t, --save-text` | Guardar el texto extraído del PDF en un .txt |
| `--text-output` | Ruta del .txt (con `-t` o `--extract-only`; por defecto mismo nombre que el PDF) |
| `--extract-only` | Solo extraer texto a .txt, sin convertir a MP3 |
| `--preserve-line-breaks` | No normalizar saltos de línea (por defecto se unen para evitar pausas en TTS) |
| `-r, --recursive` | Si es carpeta, procesar también subcarpetas |
| `--voice` | Voz (ej: es-MX-DaliaNeural) |
| `--key` | Azure Speech key (solo con `--engine azure`) |
| `--region` | Región Azure (solo con `--engine azure`) |

## Idioma: Español Latino

Por defecto la app usa voz **es-MX-DaliaNeural** (español de México). Otras voces con `--voice`:

| Locale | Voces ejemplo |
|--------|----------------|
| es-MX  | es-MX-DaliaNeural, es-MX-JorgeNeural |
| es-AR  | es-AR-ElenaNeural, es-AR-TomasNeural |
| es-CO  | es-CO-SalomeNeural, es-CO-GonzaloNeural |
| es-US  | es-US-PalomaNeural, es-US-AlonsoNeural |

## Preprocesado del texto para TTS

Por defecto el texto se normaliza para que el TTS no haga pausas en cada salto de línea del PDF:

- **Palabras partidas con guión** (ej. `convenien-\nte`) → se unen (`conveniente`)
- **Saltos de línea** → se reemplazan por espacios (evita pausas en medio de frases)
- **Espacios múltiples** → se colapsan a uno solo

Ejemplo: `"me ha parecido\nconveniente recordar"` → `"me ha parecido conveniente recordar"` (sin pausa tras "parecido").

Para conservar el formato original (p. ej. al extraer solo texto), usa `--preserve-line-breaks`.

## Plan detallado

Ver [PLAN.md](PLAN.md) para arquitectura, dependencias con uv, configuración de Azure y flujo PDF → MP3.
