from pdfsum.summarizer import (
    split_sentences,
    tokenize,
    word_frequencies,
    score_sentences,
    summarize,
)


def test_split_sentences_basic():
    # El separador solo corta cuando la siguiente oración empieza con
    # mayúscula o dígito (igual que en la versión JS de index.html), así
    # que "¿Funciona bien?" no se separa de la oración anterior.
    text = "Hola mundo. Esto es una prueba. Todo funciona bien."
    sentences = split_sentences(text)
    assert sentences == ["Hola mundo.", "Esto es una prueba.", "Todo funciona bien."]


def test_split_sentences_empty():
    assert split_sentences("") == []
    assert split_sentences("   ") == []


def test_split_sentences_collapses_whitespace():
    text = "Primera oración.\n\n   Segunda oración."
    assert split_sentences(text) == ["Primera oración.", "Segunda oración."]


def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("¡Hola, Mundo! 123") == ["hola", "mundo"]


def test_tokenize_empty_sentence():
    assert tokenize("") == []
    assert tokenize("123 456") == []


def test_word_frequencies_ignores_stopwords_and_short_words():
    sentences = ["El gato come pescado.", "El perro come carne."]
    freqs = word_frequencies(sentences, "es")
    assert "el" not in freqs  # stopword
    assert "come" in freqs
    assert freqs["come"] == 1.0  # aparece en ambas oraciones, es el máximo


def test_word_frequencies_empty_input():
    assert word_frequencies([], "es") == {}


def test_word_frequencies_english_stopwords():
    sentences = ["The cat runs fast.", "The dog runs slow."]
    freqs = word_frequencies(sentences, "en")
    assert "the" not in freqs
    assert "runs" in freqs


def test_score_sentences_length_matches_input():
    sentences = ["Primera oración de prueba.", "Segunda oración distinta."]
    scores = score_sentences(sentences, "es")
    assert len(scores) == len(sentences)
    assert all(isinstance(s, float) for s in scores)


def test_summarize_returns_all_when_fewer_than_requested():
    text = "Primera oración. Segunda oración."
    result = summarize(text, num_sentences=5, language="es")
    assert len(result) == 2


def test_summarize_respects_num_sentences():
    text = " ".join(f"Esta es la oración número {i} sobre gatos y perros." for i in range(20))
    result = summarize(text, num_sentences=4, language="es")
    assert len(result) == 4


def test_summarize_preserves_original_order():
    text = " ".join(f"Oración {i} habla de tecnología y ciencia." for i in range(10))
    original_sentences = split_sentences(text)
    result = summarize(text, num_sentences=3, language="es")
    positions = [original_sentences.index(s) for s in result]
    assert positions == sorted(positions)


def test_summarize_covers_whole_document_not_just_start():
    # El resumen debe incluir oraciones de distintos tramos del documento,
    # no solo las primeras.
    text = " ".join(f"Oración número {i} sobre gatos y perros y ciencia." for i in range(30))
    original_sentences = split_sentences(text)
    result = summarize(text, num_sentences=5, language="es")
    positions = [original_sentences.index(s) for s in result]
    assert max(positions) > len(original_sentences) // 2


def test_summarize_empty_text():
    assert summarize("", num_sentences=5, language="es") == []
