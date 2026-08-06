# pdfsum backend (gratis, sin clave de API)

Este backend genera resúmenes **abstractivos reales** (con palabras
propias, no oraciones copiadas) usando el modelo open-source
[`csebuetnlp/mT5_multilingual_XLSum`](https://huggingface.co/csebuetnlp/mT5_multilingual_XLSum),
que corre en tu propio servidor. Nadie necesita una clave de API para
usarlo: el costo (cómputo) lo pone quien hostea el backend, y con las
opciones de abajo eso es **gratis**.

## Cómo funciona

1. El frontend (`index.html`, modo "Con IA (gratis)") sube el PDF a
   `POST /api/summarize`.
2. El backend extrae el texto con `pypdf` (reutiliza `pdfsum/extractor.py`).
3. Si el documento es largo, lo trocea, resume cada parte con el modelo
   local y combina los resúmenes parciales en uno final
   (`backend/ai_summarizer.py`).
4. Devuelve JSON: `{ summary, model, chunksUsed, documentWordCount }`.

## Probarlo en local

```bash
cd Pdfsum-main
pip install -e .
pip install -r backend/requirements.txt
cd backend
uvicorn app:app --reload --port 7860
```

La primera vez que llegue una petición, se descarga el modelo
(~2 GB) — puede tardar varios minutos. Las siguientes veces usa la
copia en caché.

Luego, en `index.html`, antes del `<script>` principal, define:

```html
<script>window.PDFSUM_BACKEND_URL = "http://localhost:7860";</script>
```

o edita directamente la constante `BACKEND_URL` dentro del `<script>`.

## Desplegarlo gratis

### Opción recomendada: Hugging Face Spaces (Docker)

Hugging Face ofrece Spaces gratuitos con CPU (sin tarjeta de crédito):

1. Crea una cuenta en huggingface.co y un nuevo Space → SDK: **Docker**.
2. Sube todo el contenido de este repo (`Pdfsum-main/`) al Space —
   el `Dockerfile` está en `backend/Dockerfile`, pero el build debe
   correr desde la raíz del repo (donde está `pyproject.toml`). En la
   configuración del Space, indica `backend/Dockerfile` como ruta del
   Dockerfile.
3. (Opcional pero recomendado) Activa **almacenamiento persistente**
   en el Space y monta `/data`, así el modelo no se vuelve a descargar
   en cada reinicio.
4. Cuando el Space esté "Running", tu backend queda en
   `https://TU-USUARIO-TU-SPACE.hf.space`. Pon esa URL en `BACKEND_URL`
   dentro de `index.html`.
5. El plan CPU gratis de Spaces "duerme" tras un rato de inactividad y
   tarda ~30-60s en despertar en la siguiente petición — normal en
   planes gratuitos.

### Alternativa: Render / Railway (free tier)

Cualquier plataforma que soporte Docker sirve igual: apunta el build a
`backend/Dockerfile` con el contexto en la raíz del repo, expone el
puerto `7860` (o el que definan como `$PORT`), y usa la URL pública
resultante como `BACKEND_URL`. Los planes gratuitos de este tipo
también "duermen" el servicio tras inactividad.

## Notas sobre costo y límites

- El cómputo es 100% CPU por defecto (no requiere GPU), a costa de que
  documentos largos tarden más (segundos a un par de minutos según el
  tamaño del PDF y el plan gratuito que uses).
- No hay clave de API ni facturación por uso: el único "costo" es el
  tiempo de cómputo del servidor gratuito que elijas.
- Si esperas mucho tráfico, considera un plan pago con más CPU/RAM
  para bajar los tiempos de espera — pero para uso personal o
  demostraciones, el nivel gratuito alcanza.
