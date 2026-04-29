FROM debian:bookworm-slim

# Essential packages
RUN apt-get update && apt-get install -y \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    curl \
    wget \
    gnupg \
    git \
    ca-certificates

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

WORKDIR /app

ENV NODE_ENV=production

COPY . .

RUN uv sync --no-cache

EXPOSE 8000