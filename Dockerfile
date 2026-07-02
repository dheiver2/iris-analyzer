# Imagem para a WEB APP (camera fica no navegador do usuario; o container so
# recebe e analisa a imagem). Nao empacota o app desktop (PyQt6).
FROM python:3.11-slim

# libgl1/libglib2.0-0: dependencias de runtime do opencv-python.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

COPY iris_analyzer ./iris_analyzer
COPY web ./web
COPY run_web.py download_model.py ./

RUN python3 download_model.py

ENV IRIS_WEB_HOST=0.0.0.0
ENV IRIS_WEB_PORT=8000
EXPOSE 8000

# Sem servidor X/webbrowser.open no container: roda o uvicorn diretamente.
CMD ["python3", "-m", "uvicorn", "iris_analyzer.server:app", "--host", "0.0.0.0", "--port", "8000"]
