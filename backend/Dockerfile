# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including C++ build tools
RUN apt-get update && \
    apt-get install -y \
    git \
    build-essential \
    cmake \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
