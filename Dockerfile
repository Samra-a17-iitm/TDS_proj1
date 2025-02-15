FROM python:3.12-slim-bookworm

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3-dev \
    git \
    wget \
    sqlite3 \
    ffmpeg \
    imagemagick \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and Prettier
RUN curl -sL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    apt-get install -y nodejs && \
    node -v && \
    npm install -g prettier@3.4.2 && \
    rm nodesource_setup.sh

# Upgrade pip and install Python packages
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    requests \
    httpx \
    python-dotenv\
    pydantic \
    typer\
    gitpython\
    db-sqlite3

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /TDS_proj1

RUN mkdir -p /data

COPY app.py /TDS_proj1

CMD ["uv", "run", "app.py"]