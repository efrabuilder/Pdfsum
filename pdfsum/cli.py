"""Interfaz de línea de comandos para pdfsum."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .extractor import extract_text, extract_title
from .summarizer import summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdfsum",
        description=(
            "Genera resúmenes extractivos de archivos PDF, sin depender de "
            "ningún modelo de IA ni conexión a internet."
        ),
    )
    parser.add_argument(
        "pdfs",
        nargs="+",
        help="Uno o más archivos PDF a resumir.",
    )
    parser.add_argument(
        "--sentences",
        "-n",
        type=int,
        default=5,
        help="Número de oraciones a incluir en el resumen (por defecto: 5).",
    )
    parser.add_argument(
        "--language",
        "-l",
        choices=["es", "en"],
        default="es",
        help="Idioma del documento, usado para filtrar palabras vacías (por defecto: es).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Archivo de salida donde guardar los resúmenes. Si no se indica, se imprime en pantalla.",
    )
    return parser


def _summarize_one(pdf_path: str, num_sentences: int, language: str) -> str:
    path = Path(pdf_path)
    title = extract_title(path)
    text = extract_text(path)
    sentences = summarize(text, num_sentences=num_sentences, language=language)

    lines = [f"# {title}", ""]
    lines.extend(sentences if sentences else ["(no se pudo generar un resumen)"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    outputs = []
    exit_code = 0

    for pdf_path in args.pdfs:
        try:
            outputs.append(_summarize_one(pdf_path, args.sentences, args.language))
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error con '{pdf_path}': {exc}", file=sys.stderr)
            exit_code = 1

    if not outputs:
        return exit_code

    result_text = "\n\n".join(outputs)

    if args.output:
        Path(args.output).write_text(result_text, encoding="utf-8")
        print(f"Resumen(es) guardado(s) en {args.output}")
    else:
        print(result_text)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
