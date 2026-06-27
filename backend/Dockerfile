FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first to prevent downloading heavy CUDA dependencies
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements from the backend folder and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project folders so backend/ remains a valid package directory
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Run API command referencing the backend module package
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
