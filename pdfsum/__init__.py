"""pdfsum: resúmenes extractivos de archivos PDF, sin IA ni internet."""

from .extractor import extract_text, extract_title
from .summarizer import summarize

__version__ = "0.1.0"

__all__ = ["extract_text", "extract_title", "summarize"]
