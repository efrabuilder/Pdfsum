from pathlib import Path

import pytest

from pdfsum.extractor import extract_text, extract_title


def _make_minimal_pdf(path: Path, text: str, title: str | None = None) -> None:
    """Genera un PDF de una sola página con texto plano, sin dependencias extra.

    Construye el archivo directamente con la sintaxis mínima de PDF
    (suficiente para que pypdf pueda extraer el texto), evitando depender
    de una librería de terceros solo para las pruebas.
    """
    content = f"BT /F1 18 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")

    info_obj = f"<< /Title ({title}) >>".encode("latin-1") if title else b"<< >>"

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        b"/MediaBox [0 0 612 792] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode("latin-1") + b" >>\nstream\n"
        + content + b"\nendstream",
        info_obj,
    ]

    buf = bytearray()
    buf += b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(buf))
        buf += f"{i} 0 obj\n".encode("latin-1") + obj + b"\nendobj\n"

    xref_offset = len(buf)
    buf += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    buf += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        buf += f"{off:010d} 00000 n \n".encode("latin-1")

    buf += b"trailer\n"
    buf += f"<< /Size {len(objects) + 1} /Root 1 0 R /Info 6 0 R >>\n".encode("latin-1")
    buf += b"startxref\n"
    buf += str(xref_offset).encode("latin-1")
    buf += b"\n%%EOF"

    path.write_bytes(bytes(buf))


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "documento.pdf"
    _make_minimal_pdf(pdf_path, "Hola mundo desde una prueba", title="Mi Titulo")
    return pdf_path


def test_extract_text_returns_page_content(sample_pdf: Path):
    text = extract_text(sample_pdf)
    assert "Hola mundo desde una prueba" in text


def test_extract_text_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        extract_text(tmp_path / "no-existe.pdf")


def test_extract_title_uses_metadata(sample_pdf: Path):
    assert extract_title(sample_pdf) == "Mi Titulo"


def test_extract_title_falls_back_to_filename(tmp_path: Path):
    pdf_path = tmp_path / "reporte_final.pdf"
    _make_minimal_pdf(pdf_path, "Texto sin titulo en metadata")
    assert extract_title(pdf_path) == "reporte_final"
