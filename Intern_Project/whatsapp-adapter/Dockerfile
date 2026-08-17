FROM python:3.10-slim

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create the static directory for storing temporary/restored media and give permission to appuser
RUN mkdir -p /app/static && chown -R appuser:appuser /app/static

ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
