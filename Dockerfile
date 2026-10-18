# Container for Hugging Face Spaces (Docker SDK). Also runs anywhere Docker does:
#   docker build -t plantsense . && docker run -p 7860:7860 plantsense
FROM python:3.11-slim

# libglib2.0-0 is needed by opencv-python-headless at import time
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Spaces runs containers as UID 1000, so the app must not depend on root
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /home/user/app

# Install dependencies first so code changes don't invalidate this layer.
# requirements.txt pulls the CPU-only PyTorch wheel (no CUDA, much smaller).
COPY --chown=user requirements.txt .
RUN pip install --user --upgrade pip \
    && pip install --user -r requirements.txt

COPY --chown=user . .
RUN mkdir -p static/uploads

EXPOSE 7860

# One worker keeps a single copy of each model in memory; threads handle
# concurrent requests. Long timeout covers the first (model-loading) request.
CMD gunicorn app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 180
