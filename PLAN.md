# Plan: CLI PDF → MP3 con Azure Speech SDK (Español Latino)

## Resumen

Aplicación CLI en Python que:
- **Entrada:** archivo `.pdf`
- **Salida:** archivo `.mp3` (audio del texto del PDF)
- **Idioma:** español latino (por defecto)
- **Gestión:** Python con **uv**, entorno virtual, Azure Speech SDK (TTS)

---

## 1. Estructura del proyecto (uv)

### 1.1 Requisitos previos

- **Python 3.10+** instalado.
- **uv** instalado:
  ```powershell
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  O con pip: `pip install uv`

### 1.2 Crear proyecto con uv

```powershell
# Crear carpeta y entrar
mkdir pdf-to-mp3-cli
cd pdf-to-mp3-cli

# Crear proyecto Python con uv (genera pyproject.toml y .venv)
uv init

# O si ya tienes la carpeta: crear solo el venv
uv venv
```

Esto crea:
- `pyproject.toml` (dependencias y metadatos)
- `.venv/` (entorno virtual)

### 1.3 Dependencias a añadir

```powershell
# PDF
uv add pypdf2

# Azure Speech SDK (TTS)
uv add azure-cognitiveservices-speech

# CLI
uv add click
```

En `pyproject.toml` quedarán algo como:
- `pypdf2` (o `pypdf` si prefieres la versión más moderna)
- `azure-cognitiveservices-speech`
- `click`

### 1.4 Activar el entorno

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Luego ejecutar con uv (recomendado, no hace falta activar)
uv run python -m pdf_to_mp3.cli documento.pdf
```

---

## 2. Configuración de Azure Speech (TTS)

### 2.1 Qué necesitas en Azure

1. **Cuenta Azure** (cuenta gratuita sirve).
2. **Recurso “Speech”** (Cognitive Services / Speech):
   - Portal: [Azure Portal](https://portal.azure.com) → Crear recurso → buscar “Speech”.
   - Crear un recurso **Speech** (no solo “Cognitive Services” genérico).
   - Anota:
     - **Region** (ej: `eastus`, `westeurope`).
     - **Key 1** (o Key 2) en “Keys and Endpoint”.

### 2.2 Variables de entorno (recomendado)

No guardes la clave en el código. Usa variables de entorno:

| Variable | Descripción | Ejemplo |
|----------|-------------|--------|
| `AZURE_SPEECH_KEY` | Key del recurso Speech | `a1b2c3d4e5...` |
| `AZURE_SPEECH_REGION` | Región del recurso | `eastus` |

En PowerShell (solo para la sesión actual):

```powershell
$env:AZURE_SPEECH_KEY = "TU_KEY_AQUI"
$env:AZURE_SPEECH_REGION = "eastus"
```

O en un archivo `.env` (y cargarlo con `python-dotenv` si quieres):

```
AZURE_SPEECH_KEY=tu_key
AZURE_SPEECH_REGION=eastus
```

### 2.3 Idioma: español latino

Azure tiene varios locales de español; para **español latino** puedes usar:

| Locale | Nombre | Voces ejemplo (Neural) |
|--------|--------|------------------------|
| **es-MX** | Español (México) | `es-MX-DaliaNeural` (F), `es-MX-JorgeNeural` (M) |
| es-AR | Español (Argentina) | `es-AR-ElenaNeural` (F), `es-AR-TomasNeural` (M) |
| es-CO | Español (Colombia) | `es-CO-SalomeNeural` (F), `es-CO-GonzaloNeural` (M) |
| es-US | Español (EE.UU.) | `es-US-PalomaNeural` (F), `es-US-AlonsoNeural` (M) |

Recomendación por defecto: **es-MX** con voz **es-MX-DaliaNeural** (o **es-MX-JorgeNeural**). Dejar el locale y el nombre de voz configurables (variable de entorno o flag CLI).

---

## 3. Flujo de la aplicación

1. **Leer PDF**  
   Con `PyPDF2` (o `pypdf`): abrir el `.pdf`, extraer texto de todas las páginas y concatenar en un solo string. Opcional: limpiar saltos de línea excesivos.

2. **Dividir texto para TTS**  
   Azure TTS tiene límite por request (~5000 caracteres en muchas APIs). Dividir el texto en bloques (por ejemplo ≤4000 caracteres por petición) y sintetizar cada uno.

3. **Sintetizar a audio**  
   - Crear `SpeechConfig` con `AZURE_SPEECH_KEY` y `AZURE_SPEECH_REGION`.
   - Configurar voz en español latino, ej.: `speech_config.speech_synthesis_voice_name = "es-MX-DaliaNeural"`.
   - Usar salida en **MP3**: con el SDK de Python suele hacerse con `SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3` (o el formato MP3 que exponga el SDK) y `AudioConfig` para guardar en archivo.
   - Por cada bloque: `synthesizer.speak_text_async(text_chunk)` (o equivalente) y escribir el resultado en un buffer/archivo temporal.

4. **Unir fragmentos y guardar MP3**  
   Concatenar los audios (bytes) en orden y escribir un único `.mp3` de salida. Si el SDK devuelve WAV por defecto, convertir a MP3 (por ejemplo con `pydub`) o usar directamente el formato MP3 del SDK si está disponible.

5. **CLI**  
   - Argumento posicional: ruta al `.pdf`.
   - Opcional: ruta de salida del `.mp3` (por defecto: mismo nombre que el PDF pero con extensión `.mp3`).
   - Opcionales: `--voice` (ej. `es-MX-JorgeNeural`), `--locale` (ej. `es-MX`), y si quieres: `--region` / `--key` (sino, solo variables de entorno).

---

## 4. Estructura de archivos sugerida

```
pdf-to-mp3-cli/
├── .venv/                  # uv venv
├── .env.example             # Ejemplo de variables (sin claves reales)
├── pyproject.toml           # uv/pip dependencies
├── PLAN.md                  # Este plan
├── README.md                # Instrucciones de uso
└── src/
    └── pdf_to_mp3/
        ├── __init__.py
        ├── cli.py            # Entrypoint CLI (click)
        ├── pdf_reader.py     # Lectura de PDF
        └── tts_azure.py      # Llamadas a Azure Speech SDK, salida MP3
```

En `pyproject.toml` puedes definir el script de entrada:

```toml
[project.scripts]
pdf2mp3 = "pdf_to_mp3.cli:main"
```

Así podrás ejecutar: `uv run pdf2mp3 documento.pdf`.

---

## 5. Cómo usar la app (resumen)

1. **Configurar Azure** (una vez): crear recurso Speech, obtener Key y Region, exportar `AZURE_SPEECH_KEY` y `AZURE_SPEECH_REGION`.
2. **Instalar y ejecutar con uv:**
   ```powershell
   cd pdf-to-mp3-cli
   uv sync
   uv run pdf2mp3 ruta/al/documento.pdf
   uv run pdf2mp3 documento.pdf -o mi-audio.mp3
   uv run pdf2mp3 documento.pdf --voice es-MX-JorgeNeural
   ```
3. **Idioma:** por defecto español latino (es-MX + voz es-MX-DaliaNeural o similar); modificable con `--voice` y `--locale` si los implementas.

---

## 6. Checklist de implementación

- [ ] Proyecto uv creado (`uv init` / `uv venv`).
- [ ] Dependencias en `pyproject.toml`: `pypdf2` (o `pypdf`), `azure-cognitiveservices-speech`, `click`.
- [ ] Módulo de lectura de PDF (todas las páginas, texto limpio).
- [ ] Módulo TTS: `SpeechConfig`, voz `es-MX-...`, salida MP3, chunking si el texto es largo.
- [ ] CLI: argumento PDF, opción de salida, opcionalmente `--voice`/`--locale`.
- [ ] Documentar en README: requisitos, variables de entorno, ejemplos de uso en español latino.

Con esto tienes un plan detallado para una app CLI que tome un PDF y devuelva un MP3 usando Azure Speech SDK, con idioma por defecto en **español latino** (es-MX u otro locale que elijas).
