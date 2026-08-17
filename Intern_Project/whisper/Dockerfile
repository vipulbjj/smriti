# Use a small Python 3.11 base image.
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container.
WORKDIR /app

# Copy dependency definitions first so Docker can cache package installs.
COPY requirements.txt .

# Install Python dependencies without keeping pip's cache.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application into the container.
COPY app.py .
COPY index.html .

# Expose the port expected by Hugging Face Spaces.
EXPOSE 7860

# Run the FastAPI app with uvicorn on all network interfaces.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
