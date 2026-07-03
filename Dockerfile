# Enterprise Agentic AI Platform - container image
FROM python:3.11-slim

WORKDIR /app

# Install CPU-only PyTorch first (avoids downloading unnecessary
# multi-GB GPU/CUDA packages we don't use — cuts image size and
# build time dramatically).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of our dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/

# Default command: run the supervisor as a demo entrypoint
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]