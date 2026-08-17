# Lightweight Python runtime for Hugging Face Spaces.
FROM python:3.11-slim

WORKDIR /app

# System packages for media tooling and common image libs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face cache directory (Swin2SR downloads on first startup).
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface

# DeOldify expects weights under $DEOLDIFY_ROOT/models/.
ENV DEOLDIFY_ROOT=/app
ENV PYTHONUNBUFFERED=1

# Copy dependency definitions first so Docker can cache installed packages.
COPY requirements.txt .

# Install Python dependencies for the FastAPI restoration service.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Pre-download DeOldify artistic generator weights at build time.
RUN mkdir -p /app/models \
    && curl -fsSL -o /app/models/ColorizeArtistic_gen.pth \
        https://data.deepai.org/deoldify/ColorizeArtistic_gen.pth

# Copy application code.
COPY index.html .
COPY app.py restore.py ./

# Expose the Hugging Face Spaces HTTP port.
EXPOSE 7860

# Run the API server on all interfaces for container hosting.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
