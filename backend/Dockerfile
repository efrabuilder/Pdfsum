FROM python:3.11-slim

WORKDIR /app

# Copiamos todo el repo (necesitamos el paquete pdfsum/ además del backend).
COPY . /app

# Dependencias: el paquete pdfsum (pypdf) + las del backend (fastapi, transformers...).
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir -r backend/requirements.txt

# El modelo (~2 GB) se descarga la primera vez que se usa (lru_cache
# perezoso en ai_summarizer.py) y HF lo cachea en /root/.cache/huggingface.
# Espacios gratuitos de Hugging Face incluyen almacenamiento persistente
# en /data si quieres evitar re-descargarlo en cada reinicio (ver README).
ENV HF_HOME=/data/.cache/huggingface
ENV PORT=7860
EXPOSE 7860

WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
