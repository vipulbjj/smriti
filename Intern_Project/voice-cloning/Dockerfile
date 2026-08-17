FROM python:3.10-slim

# ffmpeg is required by pydub for audio format conversion.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Auto-accept the Coqui XTTS-v2 license during model download.
ENV COQUI_TOS_AGREED=1

# Writable cache directory for Hugging Face model downloads.
ENV HF_HOME=/app/.cache
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# HF Spaces requires running as a non-root user.
RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py voice.py tts.py index.html ./

RUN mkdir -p /app/.cache /app/voice_profiles \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
