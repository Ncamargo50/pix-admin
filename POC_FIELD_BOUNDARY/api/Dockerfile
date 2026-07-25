# Pixadvisor Field Delineation API - production image
FROM python:3.13-slim

# Dependencias del sistema (rasterio/GDAL via wheels, pero scipy/skimage requieren build deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev gdal-bin libgomp1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .
COPY *.html .

# Modelos: bind-mount en runtime via -v $PWD/output:/app/output
# Asi no se hornea en la imagen (modelos pesados ~140 MB combinados)
RUN mkdir -p /app/output

EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/health', timeout=3)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765", "--workers", "2"]
