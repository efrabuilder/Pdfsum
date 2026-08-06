"""Extracción de texto y título desde archivos PDF, usando pypdf."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text(pdf_path: str | Path) -> str:
    """Extrae y concatena el texto de todas las páginas de un PDF.

    Lanza ``FileNotFoundError`` si la ruta no existe, y ``ValueError`` si
    el PDF no tiene texto extraíble (por ejemplo, un escaneo sin capa de
    texto, sin OCR).
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    reader = PdfReader(str(path))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages_text).strip()

    if not text:
        raise ValueError(
            f"No se pudo extraer texto de '{path.name}' "
            "(puede ser un escaneo sin capa de texto; esta herramienta no incluye OCR)."
        )

    return text


def extract_title(pdf_path: str | Path) -> str:
    """Obtiene un título legible para el PDF.

    Usa el metadato ``/Title`` del documento si existe y no está vacío;
    en caso contrario, usa el nombre del archivo sin extensión.
    """
    path = Path(pdf_path)
    reader = PdfReader(str(path))
    metadata_title = (reader.metadata.title or "").strip() if reader.metadata else ""
    return metadata_title or path.stem
