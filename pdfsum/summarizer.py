"""Algoritmo de resumen extractivo.

Reimplementación en Python del mismo algoritmo usado en la versión web
(``index.html``): se puntúa cada oración por la frecuencia normalizada de
sus palabras significativas y se elige la mejor oración de cada tramo del
documento, para que el resumen cubra de principio a fin (no solo el
inicio).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

STOPWORDS_ES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las",
    "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como",
    "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque",
    "esta", "entre", "cuando", "muy", "sin", "sobre", "también", "me",
    "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso",
    "ante", "ellos", "e", "esto", "mí", "antes", "algunos", "qué",
    "unos", "yo", "otro", "otras", "otra", "él", "tanto", "esa",
    "estos", "mucho", "quienes", "nada", "muchos", "cual", "poco",
    "ella", "estar", "estas", "algunas", "algo", "nosotros", "es",
    "son", "fue", "ser", "han", "ha", "está",
}

STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "as", "by", "at", "from", "is", "are", "was", "were", "be",
    "been", "being", "this", "that", "these", "those", "it", "its",
    "if", "then", "than", "so", "such", "not", "no", "can", "will",
    "would", "could", "should", "may", "might", "must", "has", "have",
    "had", "do", "does", "did", "we", "you", "they", "he", "she",
    "his", "her", "their", "our", "your", "i", "which", "who", "whom",
    "what", "when", "where", "how", "there", "here", "also", "into",
    "about", "up", "out", "over", "under", "again", "further", "once",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ0-9])")
_WORD_RE = re.compile(r"[a-zA-ZáéíóúñÁÉÍÓÚÑüÜ]+")


@dataclass
class SummaryResult:
    """Resultado de un resumen extractivo."""

    sentences: list[str]
    total: int


def _stopword_set(language: str) -> set[str]:
    return STOPWORDS_EN if language == "en" else STOPWORDS_ES


def split_sentences(text: str) -> list[str]:
    """Segmenta el texto en oraciones."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    parts = _SENTENCE_SPLIT_RE.split(normalized)
    return [p.strip() for p in parts if p.strip()]


def tokenize(sentence: str) -> list[str]:
    """Extrae palabras (en minúscula) de una oración."""
    return _WORD_RE.findall(sentence.lower())


def word_frequencies(sentences: list[str], language: str) -> dict[str, float]:
    """Calcula la frecuencia normalizada (0-1) de palabras significativas."""
    stopwords = _stopword_set(language)
    freq: dict[str, int] = {}
    for sentence in sentences:
        for word in tokenize(sentence):
            if word in stopwords or len(word) < 3:
                continue
            freq[word] = freq.get(word, 0) + 1

    if not freq:
        return {}

    max_freq = max(freq.values())
    return {word: count / max_freq for word, count in freq.items()}


def score_sentences(sentences: list[str], language: str) -> list[float]:
    """Puntúa cada oración por el promedio de frecuencia de sus palabras."""
    freqs = word_frequencies(sentences, language)
    scores = []
    for sentence in sentences:
        words = tokenize(sentence)
        if not words:
            scores.append(0.0)
            continue
        scores.append(sum(freqs.get(w, 0.0) for w in words) / len(words))
    return scores


def _segment_bounds(total: int, num_segments: int) -> list[tuple[int, int]]:
    """Divide range(total) en num_segments tramos contiguos, lo más parejo posible."""
    bounds = []
    for i in range(num_segments):
        start = (i * total) // num_segments
        end = ((i + 1) * total) // num_segments
        bounds.append((start, end))
    return bounds


def summarize(text: str, num_sentences: int = 5, language: str = "es") -> list[str]:
    """Genera un resumen extractivo de ``text``.

    Elige la oración con mayor puntaje de cada tramo del documento, para
    que el resumen cubra de la primera a la última página en lugar de
    concentrarse en el inicio.
    """
    result = _summarize_detailed(text, num_sentences, language)
    return result.sentences


def _summarize_detailed(text: str, num_sentences: int, language: str) -> SummaryResult:
    sentences = split_sentences(text)
    if not sentences:
        return SummaryResult(sentences=[], total=0)
    if len(sentences) <= num_sentences:
        return SummaryResult(sentences=sentences, total=len(sentences))

    scores = score_sentences(sentences, language)

    chosen: set[int] = set()
    for start, end in _segment_bounds(len(sentences), num_sentences):
        if start >= end:
            continue
        best_index = start
        for i in range(start + 1, end):
            if scores[i] > scores[best_index]:
                best_index = i
        chosen.add(best_index)

    if len(chosen) < num_sentences:
        ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
        for i in ranked:
            if len(chosen) >= num_sentences:
                break
            chosen.add(i)

    top_indices = sorted(chosen)[:num_sentences]
    return SummaryResult(
        sentences=[sentences[i] for i in top_indices],
        total=len(sentences),
    )
