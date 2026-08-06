"""Backend gratuito de pdfsum.

Expone un endpoint HTTP que recibe un PDF y devuelve un resumen
abstractivo real, generado con un modelo open-source que corre en este
mismo servidor. No requiere ninguna clave de API por parte del
usuario: el costo lo asume quien hostea el backend (gratis en un plan
free de Hugging Face Spaces / Render, ver README.md).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ai_summarizer import LENGTH_PRESETS, summarize_ai
from pdfsum.extractor import extract_text

app = FastAPI(title="pdfsum backend", version="1.0.0")

# Permite que index.html (servido desde cualquier origen: GitHub Pages,
# file://, etc.) llame a este backend. Si despliegas el frontend en un
# dominio propio, puedes restringir esto a ese dominio.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/")
def health() -> dict:
    return {"status": "ok", "service": "pdfsum backend"}


@app.post("/api/summarize")
async def summarize_endpoint(
    file: UploadFile = File(...),
    language: str = Form("es"),
    length: str = Form("medium"),
) -> dict:
    if file.content_type not in ("application/pdf", "application/octet-stream") and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "El archivo debe ser un PDF.")

    if length not in LENGTH_PRESETS:
        raise HTTPException(400, f"length debe ser uno de: {', '.join(LENGTH_PRESETS)}")

    if language not in ("es", "en"):
        raise HTTPException(400, "language debe ser 'es' o 'en'.")

    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp.flush()

        try:
            text = extract_text(Path(tmp.name))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    result = summarize_ai(text, length_key=length, language=language)

    return {
        "summary": result.summary,
        "chunksUsed": result.chunks_used,
        "model": result.model,
        "documentWordCount": len(text.split()),
    }
