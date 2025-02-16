# Use a lightweight Python base image
FROM python:3.12-slim-bookworm

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    sqlite3 \
    ffmpeg \
    imagemagick \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Tesseract-OCR for OCR processing
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev

# Set Tesseract environment variable
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

# Install nvm (Node Version Manager) and Node.js
RUN curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash

# Set up environment variables for nvm
ENV NVM_DIR="/root/.nvm"
ENV PATH="$NVM_DIR/versions/node/v22.14.0/bin:$PATH"

# Install Node.js & npm
RUN . "$NVM_DIR/nvm.sh" && \
    nvm install 22 && \
    nvm use 22 && \
    nvm alias default 22

# Set npm to use an alternate registry and install Prettier
RUN . "$NVM_DIR/nvm.sh" && \
    npm config set registry https://registry.npmmirror.com/ && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 60000 && \
    npm install -g prettier@3.4.2

# Upgrade pip and install common Python libraries
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir \
    fastapi uvicorn[standard] requests httpx python-dotenv pydantic typer gitpython \
    db-sqlite3 numpy pandas scipy scikit-learn matplotlib seaborn tqdm \
    opencv-python-headless pillow pytesseract

# Download and install `uv`
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure `uv` is in PATH
ENV PATH="/root/.local/bin/:$PATH"

# Set working directory
WORKDIR /TDS_proj1

# Create necessary directories
RUN mkdir -p /data

# Copy application files
COPY app.py /TDS_proj1



# Run the application
CMD ["uv", "run", "app.py"]
