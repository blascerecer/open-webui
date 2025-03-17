# Open WebUI with MCP Access

This repository provides Open WebUI with MCP (Model Control Protocol) bridge access to connect with various AI models.

## Quick Setup Guide

Watch our setup video tutorial: [https://www.youtube.com/watch?v=F0bI2RsuzMI](https://www.youtube.com/watch?v=F0bI2RsuzMI)

### 1. Configuration Steps

#### Configure MCP Bridge
1. Copy the example configuration files:
   ```bash
   cp mcp-bridge/config.json.example mcp-bridge/config.json 
   cp mcp-bridge/mcp_config.json.example mcp-bridge/mcp_config.json
   ```
2. Update the `config.json` with your OpenAI API key:
   ```json
   {
     "openai_api_key": "your-api-key"
   }
   ```
   Replace "your-api-key" with your actual OpenAI API key.
3. No modifications needed for `mcp_config.json` - the default settings should work fine.

#### Configure Web UI
1. Sign in to Web UI locally
2. Go to Settings → Connections → Add a connection to `localhost:8000/v1` with your OpenAI API key
3. Go to Admin Settings → Settings → Edit the OpenAI connection to point to your MCP bridge (`localhost:8000/v1`)

### 2. Installation and Running

Run each component separately:

#### Frontend (from root directory)
```bash
# Install dependencies
npm i

# Start development server
npm run dev
```

#### Backend (from root/backend)
```bash
# Start backend services
sh ./dev.sh
```

#### MCP Bridge (from root/mcp-bridge)
```bash
# Install uv if not already installed
pip install uv

# Sync dependencies
uv sync

# Run the bridge
uv run mcp_bridge/main.py
```

> **Note**: Docker support is currently not stable and is being actively worked on. Please use the local setup method above for now.

## Support

If you have any questions or need assistance, please open an issue in this repository or join our community channels.