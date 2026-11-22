# Imagen para levantar el compilador y el editor web de RustiQ.
#
#   docker build -t rustiq .
#   docker run --rm -p 8000:8000 rustiq
#
# El editor queda en http://localhost:8000/ y la API en POST /compile.
# El editor ya viene construido en web/dist/, así que la imagen no necesita Node.

FROM python:3.12-slim-bookworm

# wabt trae wat2wasm y wasm-validate, que el pipeline usa para convertir y validar.
RUN apt-get update \
    && apt-get install -y --no-install-recommends wabt \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rustiq/ rustiq/
COPY server/ server/
COPY web/dist/ web/dist/
COPY tests/ tests/
COPY scripts/ scripts/
COPY pytest.ini pyproject.toml ./

# Usuario sin privilegios para correr el servidor.
RUN useradd --create-home rustiq
USER rustiq

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
