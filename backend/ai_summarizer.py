"""Resumen abstractivo gratuito, sin clave de API.

Usa un modelo open-source (mT5 multilingüe afinado para resumen,
``csebuetnlp/mT5_multilingual_XLSum``) que corre en el propio servidor,
así que no depende de ninguna API de pago ni de que el usuario tenga
una clave.

Para documentos largos, el texto se trocea en fragmentos, cada
fragmento se resume por separado y luego los resúmenes parciales se
combinan en un resumen final — el mismo enfoque de "map-reduce" que ya
usaba el modo "Con IA" original, pero con un modelo local y gratuito
en vez de una API externa.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pdfsum.summarizer import split_sentences

MODEL_NAME = "csebuetnlp/mT5_multilingual_XLSum"

# Longitud objetivo del resumen final, en palabras aproximadas.
LENGTH_PRESETS = {
    "short": (40, 90),
    "medium": (90, 180),
    "long": (180, 320),
}

# Cuántas palabras del documento original entran, como máximo, en cada
# fragmento antes de resumirlo. El modelo tiene un límite de ~512
# tokens de entrada; nos quedamos con margen.
CHUNK_WORD_LIMIT = 350


@dataclass
class AiSummaryResult:
    summary: str
    chunks_used: int
    model: str = MODEL_NAME


@lru_cache(maxsize=1)
def _load_pipeline():
    """Carga el modelo una sola vez (perezoso, para arrancar rápido)."""
    from transformers import pipeline

    return pipeline("summarization", model=MODEL_NAME, tokenizer=MODEL_NAME)


def _chunk_text(text: str, word_limit: int) -> list[str]:
    """Agrupa oraciones consecutivas en fragmentos de ~word_limit palabras."""
    sentences = split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        words = len(sentence.split())
        if current and current_words + words > word_limit:
            chunks.append(" ".join(current))
            current = []
            current_words = 0
        current.append(sentence)
        current_words += words

    if current:
        chunks.append(" ".join(current))

    return chunks or [text]


def _summarize_chunk(pipe, text: str, min_words: int, max_words: int) -> str:
    # El pipeline trabaja con tokens, no palabras; usamos un factor de
    # holgura (~1.3 tokens por palabra en español/inglés) para acercarnos
    # a la longitud objetivo en palabras.
    result = pipe(
        text,
        min_length=max(8, int(min_words * 1.3)),
        max_length=max(16, int(max_words * 1.3)),
        do_sample=False,
        truncation=True,
    )
    return result[0]["summary_text"].strip()


def summarize_ai(text: str, length_key: str = "medium", language: str = "es") -> AiSummaryResult:
    """Genera un resumen abstractivo real, gratis y sin clave de API."""
    min_words, max_words = LENGTH_PRESETS.get(length_key, LENGTH_PRESETS["medium"])
    pipe = _load_pipeline()

    chunks = _chunk_text(text, CHUNK_WORD_LIMIT)

    if len(chunks) == 1:
        summary = _summarize_chunk(pipe, chunks[0], min_words, max_words)
        return AiSummaryResult(summary=summary, chunks_used=1)

    # Paso 1 ("map"): resumir cada fragmento con una extensión intermedia,
    # conservando ideas y datos concretos.
    partials = [
        _summarize_chunk(pipe, chunk, min_words=40, max_words=90)
        for chunk in chunks
    ]

    # Paso 2 ("reduce"): combinar los resúmenes parciales en uno final.
    combined_input = " ".join(partials)
    final_summary = _summarize_chunk(pipe, combined_input, min_words, max_words)

    return AiSummaryResult(summary=final_summary, chunks_used=len(chunks))
