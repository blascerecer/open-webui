# Use official Node.js image for the specific version
FROM node:22.14.0-slim AS node

# Use Python as the main image
FROM python:3.12-bullseye

# install uv to run stdio clients (uvx)
RUN pip install --no-cache-dir uv

# Copy Node.js binaries and npm from the Node.js image
COPY --from=node /usr/local/bin/node /usr/local/bin/
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Verify installation
RUN node -v && npm -v && npx -v
    
COPY pyproject.toml .

## FOR GHCR BUILD PIPELINE
COPY mcp_bridge/__init__.py mcp_bridge/__init__.py
COPY README.md README.md

RUN uv sync

COPY mcp_bridge mcp_bridge

EXPOSE 8000

WORKDIR /mcp_bridge
ENTRYPOINT ["uv", "run", "main.py"]