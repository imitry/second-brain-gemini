FROM python:3.12-slim

# Prevent prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies including Node.js prerequisites
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (v20) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Gemini CLI globally
RUN npm install -g @google/gemini-cli

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy dependency definition files first for caching
COPY pyproject.toml .
# Note: if uv.lock exists, it's better to copy it too: COPY pyproject.toml uv.lock ./

# Copy the rest of the application
COPY . .

# Install python dependencies using uv
RUN uv sync

# Copy entrypoint that maps PROXY_URL to ALL_PROXY/HTTP_PROXY/HTTPS_PROXY
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Command to run the bot
CMD ["uv", "run", "python", "-m", "d_brain"]
