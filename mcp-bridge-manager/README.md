# MCP Bridge Manager

A service that dynamically manages MCP Bridge instances for users of Open WebUI.

## Overview

MCP Bridge Manager creates and manages per-user MCP Bridge instances. When a user logs into Open WebUI, the Manager creates a dedicated MCP Bridge instance for that user, which manages their API keys securely. When the user logs out, their bridge instance is destroyed.

## Features

- Dynamic creation of user-specific MCP Bridge instances
- Secure storage of API keys in Kubernetes Secrets
- API for users to manage their API keys
- Automatic cleanup of resources when users log out

## Architecture

The system consists of:

1. **MCP Bridge Manager** - A service that creates and manages MCP Bridge instances
2. **Per-user MCP Bridge instances** - Dynamically created when users log in
3. **Open WebUI integration** - Connects users to their MCP Bridge instances

## Setup

### Prerequisites

- Kubernetes cluster
- kubectl configured
- Helm (for deployment)

### Installation

1. Build the Docker image:

```bash
docker build -t gcr.io/blagent-prod/mcp-bridge-manager:latest .
docker push gcr.io/blagent-prod/mcp-bridge-manager:latest
```

2. Deploy the MCP Bridge Manager:

```bash
kubectl apply -f kubernetes/mcp-bridge-manager.yaml
```

3. Configure the Open WebUI to use the MCP Bridge Manager:

```bash
kubectl apply -f kubernetes/open-webui-config.yaml
```

## Configuration

The MCP Bridge Manager can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Host address to bind | `0.0.0.0` |
| `PORT` | Port to listen on | `8081` |
| `DEBUG` | Enable debug mode | `False` |
| `NAMESPACE` | Kubernetes namespace | `default` |
| `MCP_BRIDGE_IMAGE` | MCP Bridge image to use | `ghcr.io/secretiveshell/mcp-bridge/mcp-bridge:0.1.0` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

## API Reference

### Create MCP Bridge

```
POST /api/bridge/create
```

Creates a new MCP Bridge instance for a user.

**Request Body:**

```json
{
  "userId": "user123",
  "inferenceServer": {
    "baseUrl": "https://inference.example.com",
    "apiKey": "api-key-example"
  },
  "mcpServers": {
    "github": {
      "command": "github-api",
      "args": [],
      "apiKey": "github-api-key-example"
    }
  }
}
```

### Get Bridge Status

```
GET /api/bridge/{userId}
```

Returns the status of a user's MCP Bridge.

### Delete Bridge

```
DELETE /api/bridge/{userId}
```

Removes a user's MCP Bridge instance.

### Store API Key

```
PUT /api/keys/{userId}
```

Stores a new API key for a user.

**Request Body:**

```json
{
  "server": "github",
  "command": "github-api",
  "args": [],
  "apiKey": "new-github-api-key"
}
```

### List API Keys

```
GET /api/keys/{userId}
```

Lists the available MCP servers for a user.

## Integration with Open WebUI

See the [Integration Guide](docs/integration-guide.md) for details on how to integrate with Open WebUI.

## Security Considerations

- API keys are stored as Kubernetes Secrets
- Each user's MCP Bridge instance is isolated
- Network policies restrict communication
- Resources are cleaned up when users log out

## License

[MIT License](LICENSE)