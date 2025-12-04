# Dockerfile para Document Embedding Service

FROM python:3.11-slim

# Metadados
LABEL maintainer="your-email@example.com"
LABEL description="Document Embedding Service with OCI Authentication"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Cria diretórios de trabalho
WORKDIR /app

# Cria usuário não-root
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/uploads /app/logs /app/config && \
    chown -R appuser:appuser /app

# Copia requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY --chown=appuser:appuser *.py ./
COPY --chown=appuser:appuser config/ ./config/

# Muda para usuário não-root
USER appuser

# Expõe porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Comando de inicialização
CMD ["python", "app.py"]
