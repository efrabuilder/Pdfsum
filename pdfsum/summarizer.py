"""Algoritmo de resumen extractivo.

Reimplementación en Python del mismo algoritmo usado en la versión web
(``index.html``). El resumen tiene dos partes:

1. Una **línea de tema**, sintetizada (no copiada) a partir de las
   palabras/frases más relevantes del documento, que responde a "¿de
   qué trata esto?".
2. Un conjunto de **oraciones representativas**, elegidas con un
   algoritmo tipo TextRank (cada oración "vota" por las oraciones
   parecidas a ella; las más centrales ganan) en vez de solo frecuencia
   de palabras, cubriendo el documento de principio a fin y evitando
   redundancia entre las oraciones elegidas.

Sigue siendo un resumen **extractivo**: no reescribe el texto ni
"entiende" el documento como lo haría un modelo de lenguaje. La línea
de tema y la selección por TextRank lo acercan más a lo que alguien
esperaría de un resumen, pero para un resumen realmente abstractivo
(en prosa, con las ideas explicadas en otras palabras) hay que usar el
modo "Con IA" de la versión web.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

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

# Palabras/artefactos típicos de tablas o listas mal extraídas de un PDF
# (encabezados de tabla de decisión, celdas repetidas, etc.).
_TABLE_MARKER_RE = re.compile(
    r"\[[^\]]{0,20}\]|\bregla\b.*\bregla\b|\bvalor\b.*\bvalor\b",
    re.IGNORECASE,
)

TOPIC_LINE_TEMPLATES = {
    "es": "Este documento trata principalmente sobre {items}.",
    "en": "This document is mainly about {items}.",
}


@dataclass
class SummaryResult:
    """Resultado de un resumen extractivo."""

    sentences: list[str]
    total: int
    keywords: list[str] = field(default_factory=list)
    topic_line: str = ""
    overview: str = ""


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


def _is_junk_sentence(sentence: str, words: list[str]) -> bool:
    """Detecta fragmentos de tablas/listas mal extraídas de un PDF.

    Cosas como ``[Condición] [Condición] ... Regla Regla Regla valor
    valor valor X X X F I G H A B`` no son oraciones reales: son celdas
    de una tabla concatenadas por el extractor de texto. No aportan
    nada a un resumen y solo lo ensucian, así que se descartan antes de
    puntuar.
    """
    if _TABLE_MARKER_RE.search(sentence):
        return True
    if len(words) < 4:
        return True
    # Mucha repetición de la misma palabra corta (celdas repetidas) o
    # puros "tokens" de una letra (encabezados tipo "X X X F I G H A B").
    single_letter_ratio = sum(1 for w in words if len(w) == 1) / len(words)
    if single_letter_ratio > 0.3:
        return True
    unique_ratio = len(set(words)) / len(words)
    if len(words) >= 6 and unique_ratio < 0.5:
        return True
    return False


def _significant_words(words: list[str], stopwords: set[str]) -> list[str]:
    return [w for w in words if w not in stopwords and len(w) >= 3]


def extract_keywords(sentences: list[str], language: str, top_n: int = 8) -> list[str]:
    """Extrae los términos (palabras o pares de palabras) más relevantes.

    Se usan para construir la línea de tema del resumen. Se prefieren
    bigramas (pares de palabras significativas consecutivas) que
    aparecen varias veces, porque suelen ser frases más específicas
    ("análisis de sistemas") que una sola palabra suelta.
    """
    stopwords = _stopword_set(language)
    unigram_counts: dict[str, int] = {}
    bigram_counts: dict[str, int] = {}

    for sentence in sentences:
        words = tokenize(sentence)
        for i, word in enumerate(words):
            if word in stopwords or len(word) < 4:
                continue
            unigram_counts[word] = unigram_counts.get(word, 0) + 1
            if i + 1 < len(words):
                nxt = words[i + 1]
                if nxt != word and nxt not in stopwords and len(nxt) >= 4:
                    bigram = f"{word} {nxt}"
                    bigram_counts[bigram] = bigram_counts.get(bigram, 0) + 1

    candidates: list[tuple[str, float]] = [
        (bigram, count * 1.5) for bigram, count in bigram_counts.items() if count >= 2
    ]
    words_used_in_bigrams: set[str] = set()
    for bigram, _ in candidates:
        words_used_in_bigrams.update(bigram.split(" "))

    for word, count in unigram_counts.items():
        if word in words_used_in_bigrams:
            continue
        candidates.append((word, float(count)))

    candidates.sort(key=lambda item: item[1], reverse=True)

    keywords: list[str] = []
    seen_stems: set[str] = set()
    for term, _ in candidates:
        stem = term[:5]
        if stem in seen_stems:
            continue
        seen_stems.add(stem)
        keywords.append(term)
        if len(keywords) >= top_n:
            break
    return keywords


def _join_with_conjunction(items: list[str], language: str) -> str:
    if len(items) == 1:
        return items[0]
    conjunction = "and" if language == "en" else "y"
    return ", ".join(items[:-1]) + f" {conjunction} " + items[-1]


def build_topic_line(keywords: list[str], language: str) -> str:
    """Sintetiza (no copia) una línea que resume el/los tema(s) del texto."""
    if not keywords:
        return ""
    top = keywords[:5]
    items = _join_with_conjunction(top, language)
    template = TOPIC_LINE_TEMPLATES.get(language, TOPIC_LINE_TEMPLATES["es"])
    return template.format(items=items)


_ARC_CONNECTORS = {
    "es": {
        1: ["En general"],
        2: ["Al inicio", "Hacia el final"],
        3: ["Al inicio", "En la parte central", "Hacia el final"],
        4: ["Al inicio", "Después", "Más adelante", "Hacia el final"],
    },
    "en": {
        1: ["Overall"],
        2: ["At the start", "Toward the end"],
        3: ["At the start", "In the middle", "Toward the end"],
        4: ["At the start", "Then", "Further along", "Toward the end"],
    },
}

_ARC_TEMPLATES = {
    "es": "{connector}, el documento aborda {items}.",
    "en": "{connector}, the document covers {items}.",
}


def build_global_overview(pool_sentences: list[str], language: str) -> str:
    """Sintetiza un párrafo que describe el recorrido de TODO el documento.

    A diferencia de :func:`build_topic_line` (un tema general) o de las
    oraciones elegidas por :func:`summarize_detailed` (fragmentos
    puntuales), esto divide el documento en tramos (inicio, medio,
    final) y arma, con las palabras clave de cada tramo, una frase por
    tramo — para dar una idea de cómo evoluciona el contenido de
    principio a fin, no solo de qué "temas sueltos" aparecen.
    """
    if not pool_sentences:
        return ""

    if len(pool_sentences) >= 8:
        num_segments = 4
    elif len(pool_sentences) >= 5:
        num_segments = 3
    elif len(pool_sentences) >= 3:
        num_segments = 2
    else:
        num_segments = 1

    connectors = _ARC_CONNECTORS.get(language, _ARC_CONNECTORS["es"])[num_segments]
    template = _ARC_TEMPLATES.get(language, _ARC_TEMPLATES["es"])

    parts: list[str] = []
    for (start, end), connector in zip(_segment_bounds(len(pool_sentences), num_segments), connectors):
        if start >= end:
            continue
        segment_keywords = extract_keywords(pool_sentences[start:end], language, top_n=4)
        if not segment_keywords:
            continue
        items = _join_with_conjunction(segment_keywords, language)
        parts.append(template.format(connector=connector, items=items))

    return " ".join(parts)


def _sentence_similarity(words_a: list[str], words_b: list[str]) -> float:
    """Similitud simple entre dos oraciones (solapamiento normalizado)."""
    if not words_a or not words_b:
        return 0.0
    set_a, set_b = set(words_a), set(words_b)
    overlap = len(set_a & set_b)
    if overlap == 0:
        return 0.0
    denom = math.log(len(set_a) + 1) + math.log(len(set_b) + 1)
    return overlap / denom if denom > 0 else 0.0


def _textrank_scores(
    sentences: list[str], language: str, damping: float = 0.85, iterations: int = 20
) -> list[float]:
    """Puntúa oraciones por centralidad (tipo TextRank/PageRank).

    A diferencia de la frecuencia simple, esto premia oraciones que se
    parecen a muchas otras oraciones del documento (es decir, oraciones
    "centrales" al contenido), no solo las que usan palabras frecuentes.
    """
    stopwords = _stopword_set(language)
    sig_words = [_significant_words(tokenize(s), stopwords) for s in sentences]
    n = len(sentences)
    if n == 0:
        return []

    similarity = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            sim = _sentence_similarity(sig_words[i], sig_words[j])
            similarity[i][j] = sim
            similarity[j][i] = sim

    row_sums = [sum(row) for row in similarity]
    scores = [1.0 / n] * n
    for _ in range(iterations):
        new_scores = []
        for i in range(n):
            incoming = 0.0
            for j in range(n):
                if i == j or row_sums[j] == 0:
                    continue
                incoming += (similarity[j][i] / row_sums[j]) * scores[j]
            new_scores.append((1 - damping) / n + damping * incoming)
        scores = new_scores

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
    """Genera un resumen extractivo de ``text`` (solo las oraciones).

    Para obtener también la línea de tema y las palabras clave, usar
    :func:`summarize_detailed`.
    """
    return summarize_detailed(text, num_sentences, language).sentences


def summarize_detailed(text: str, num_sentences: int, language: str) -> SummaryResult:
    stopwords = _stopword_set(language)
    all_sentences = split_sentences(text)
    if not all_sentences:
        return SummaryResult(sentences=[], total=0)

    # Descarta fragmentos de tablas/listas antes de puntuar y antes de
    # sacar palabras clave, para que no compitan por un lugar en el
    # resumen ni contaminen la línea de tema. Si el filtro deja muy
    # pocas oraciones (documento raro), se usa la lista completa como
    # respaldo.
    tokenized = [tokenize(s) for s in all_sentences]
    junk_flags = [_is_junk_sentence(s, w) for s, w in zip(all_sentences, tokenized)]
    if sum(1 for j in junk_flags if not j) >= max(num_sentences, 3):
        pool_indices = [i for i, j in enumerate(junk_flags) if not j]
    else:
        pool_indices = list(range(len(all_sentences)))

    pool_sentences = [all_sentences[i] for i in pool_indices]

    keywords = extract_keywords(pool_sentences, language)
    topic_line = build_topic_line(keywords, language)
    overview = build_global_overview(pool_sentences, language)

    if len(pool_sentences) <= num_sentences:
        return SummaryResult(
            sentences=pool_sentences,
            total=len(all_sentences),
            keywords=keywords,
            topic_line=topic_line,
            overview=overview,
        )

    pool_scores = _textrank_scores(pool_sentences, language)
    pool_words = [
        set(_significant_words(tokenize(s), stopwords)) for s in pool_sentences
    ]

    chosen: list[int] = []

    def similar_to_chosen(idx: int) -> bool:
        words = pool_words[idx]
        if not words:
            return False
        for c in chosen:
            other = pool_words[c]
            if not other:
                continue
            overlap = len(words & other) / min(len(words), len(other))
            if overlap > 0.6:
                return True
        return False

    for start, end in _segment_bounds(len(pool_sentences), num_sentences):
        if start >= end:
            continue
        ranked = sorted(range(start, end), key=lambda i: pool_scores[i], reverse=True)
        pick = next((i for i in ranked if i not in chosen and not similar_to_chosen(i)), None)
        if pick is None:
            pick = next((i for i in ranked if i not in chosen), ranked[0])
        chosen.append(pick)

    if len(chosen) < num_sentences:
        ranked_all = sorted(
            range(len(pool_sentences)), key=lambda i: pool_scores[i], reverse=True
        )
        for i in ranked_all:
            if len(chosen) >= num_sentences:
                break
            if i not in chosen:
                chosen.append(i)

    top_indices = sorted(chosen)[:num_sentences]
    return SummaryResult(
        sentences=[pool_sentences[i] for i in top_indices],
        total=len(all_sentences),
        keywords=keywords,
        topic_line=topic_line,
        overview=overview,
    )
