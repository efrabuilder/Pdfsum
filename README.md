# pdfsum

Genera resúmenes de archivos PDF de dos formas:

- **Extractivo (local)**: selecciona las oraciones más representativas del documento por frecuencia de palabras. 100% en el navegador, sin servidor ni internet, pero no redacta ideas nuevas — solo copia oraciones existentes.
- **Con IA (gratis)**: un resumen abstractivo real (en palabras propias, cubriendo de qué trata el documento) generado por un modelo open-source que corre en un backend propio. Es gratis y no requiere ninguna clave de API — ver `backend/README.md` para desplegarlo.

Incluye tres formas de uso:

1. **Paquete Python** (`pdfsum/`) — librería y CLI instalables (modo extractivo).
2. **`index.html`** — versión web con ambos modos: extractivo 100% local (usa [pdf.js](https://mozilla.github.io/pdf.js/)) y "Con IA (gratis)", que sube el PDF al backend propio.
3. **`backend/`** — API en FastAPI que sirve el modo "Con IA (gratis)"; se despliega sin costo (Hugging Face Spaces, Render, etc.).

## Cómo funciona el algoritmo

1. El texto se segmenta en oraciones.
2. Se calcula la frecuencia normalizada de las palabras significativas (se descartan palabras vacías como "de", "la", "que", "the", "and", etc.).
3. Cada oración recibe un puntaje: el promedio de frecuencia de sus palabras, con un pequeño bono para las oraciones que aparecen al inicio del documento.
4. Se devuelven las N oraciones con mayor puntaje, respetando su orden original de aparición.

Es un método clásico de resumen **extractivo** (no genera texto nuevo, selecciona texto existente) — rápido, predecible y que no requiere GPU, API keys ni conexión a internet.

## Instalación (paquete Python)

```bash
git clone https://github.com/tu-usuario/pdfsum.git
cd pdfsum
pip install -e .
```

## Uso por línea de comandos

```bash
pdfsum documento.pdf
pdfsum documento.pdf --sentences 8 --language en
pdfsum a.pdf b.pdf --output resumenes.txt
```

## Uso como librería

```python
from pdfsum import extract_text, summarize

texto = extract_text("documento.pdf")
resumen = summarize(texto, num_sentences=5, language="es")
print("\n".join(resumen))
```

## Uso web (`index.html`)

Abre `index.html` en cualquier navegador (o publícalo con GitHub Pages) y arrastra un PDF. La página:

1. Lee el PDF con pdf.js directamente en tu navegador — el archivo nunca sale de tu computadora.
2. Extrae el texto de todas las páginas.
3. Aplica el mismo algoritmo de resumen (reescrito en JavaScript) y muestra las oraciones más relevantes.
4. Permite ajustar el número de oraciones y el idioma, y copiar el resultado.

## Estructura del proyecto

```
pdfsum/
├── pdfsum/
│   ├── __init__.py
│   ├── extractor.py    # extracción de texto y título desde PDF (pypdf)
│   ├── summarizer.py    # algoritmo de resumen extractivo
│   └── cli.py            # interfaz de línea de comandos
├── tests/
│   ├── test_summarizer.py
│   └── test_extractor.py
├── backend/
│   ├── app.py             # API FastAPI (POST /api/summarize)
│   ├── ai_summarizer.py   # resumen abstractivo con modelo open-source local
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md          # cómo desplegarlo gratis
├── index.html             # versión web (modo extractivo local + modo IA gratis)
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Limitaciones

- El modo **extractivo** no genera oraciones nuevas ni parafrasea: selecciona las oraciones existentes más relevantes según frecuencia de palabras. No es capaz de explicar "de qué trata" el documento en sus propias palabras — para eso usa el modo "Con IA (gratis)".
- El modo **"Con IA (gratis)"** sí sube el PDF al backend (deja de ser 100% local) y depende de que tengas ese backend desplegado (ver `backend/README.md`); en el free tier de la mayoría de plataformas, la primera petición tras inactividad puede tardar en "despertar" el servidor.
- PDFs escaneados sin capa de texto (imágenes puras) no tienen texto extraíble; esta herramienta no incluye OCR.
- La calidad del resumen extractivo depende de que el documento tenga oraciones bien formadas; PDFs con mucho texto en columnas, tablas o formato irregular pueden dar resultados menos precisos.

## Pruebas

```bash
pip install pytest
pytest tests/
```

## Licencia

MIT
