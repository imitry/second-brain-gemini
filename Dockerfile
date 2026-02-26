FROM python:3.12-slim

# Install system dependencies, Node.js and Xray
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    gettext-base \
    unzip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && curl -L -H "Cache-Control: no-cache" -o /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/download/v1.8.24/Xray-linux-64.zip \
    && mkdir -p /usr/local/bin/xray-core \
    && unzip /tmp/xray.zip -d /usr/local/bin/xray-core \
    && chmod +x /usr/local/bin/xray-core/xray \
    && rm /tmp/xray.zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install Gemini CLI globally
RUN npm install -g @google/gemini-cli

# Set working directory
WORKDIR /app

# Copy dependency + source files needed for pip install
COPY pyproject.toml README.md ./
COPY src/ src/

# Install Python dependencies using uv
RUN uv pip install --system .

# Copy the rest of the application (entrypoint, vault skeleton, .gemini, docs, etc.)
COPY . .

# Ensure the Gemini settings directory exists
# settings.json template is kept in /app/.gemini/ — envsubst runs at startup
RUN mkdir -p /root/.gemini

# Ensure vault directory exists (it should be mounted as a volume in Coolify)
RUN mkdir -p /app/vault

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Debug directory contents
RUN ls -la /app

# Set up entrypoint script
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

