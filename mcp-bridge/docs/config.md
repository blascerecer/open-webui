# Config

The config file is a json file that contains all the information needed to run the application.

## Writing a config file

| Section          | Description                                                                                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| inference_server | The inference server configuration. This should point to openai/vllm/ollama etc. Any OpenAI compatible base url should work.                                                   |
| sampling         | Sampling model preferences. You must have at least one sampling model configured, and you can configure the same model with different intelligence, cost, and speed many times |
| mcp_servers      | MCP server connection info/configuration. This is mostly the same as claude desktop but with some extra options.                                                               |
| network          | uvicorn network configuration. Only used outside of docker environment                                                                                                         |
| logging          | The logging configuration. Set to DEBUG for debug logging                                                                                                                      |

Here is an example config.json file:

```json
{
    "inference_server": {
        "base_url": "http://localhost:8000/v1",
        "api_key": "None"
    },
    "sampling": {
        "timeout": 10,
        "models": [
            {
                "model": "gpt-4o",
                "intelligence": 0.8,
                "cost": 0.9,
                "speed": 0.3
            },
            {
                "model": "gpt-4o-mini",
                "intelligence": 0.4,
                "cost": 0.1,
                "speed": 0.7
            }
        ]
    },
    "mcp_servers": {
        "fetch": {
            "command": "uvx",
            "args": [
                "mcp-server-fetch"
            ]
        },
        "sse-example-server": {
            "url": "http://localhost:8000/mcp-server/sse"
        },
        "docker-example-server": {
            "image": "example-server:latest",
        }
    },
    "network": {
        "host": "0.0.0.0",
        "port": 9090
    },
    "logging": {
        "log_level": "DEBUG"
    }
}
```

## Loading a config file

### Docker

when using docker you will need to add a reference to the config.json file in the `compose.yml` file. Pick any of

- add the `config.json` file to the same directory as the compose.yml file and use a volume mount (you will need to add the volume manually)
  ```bash
  environment:
    - MCP_BRIDGE__CONFIG__FILE=config.json # mount the config file for this to work
  ```
  
  The mount point for using the config file would look like:
  ```yaml
    volumes:
      - ./config.json:/mcp_bridge/config.json
  ```

- add a http url to the environment variables to download the config.json file from a url
  ```bash
  environment:
    - MCP_BRIDGE__CONFIG__HTTP_URL=http://10.88.100.170:8888/config.json
  ```

- add the config json directly as an environment variable
  ```bash
  environment:
    - MCP_BRIDGE__CONFIG__JSON={"inference_server":{"base_url":"http://example.com/v1","api_key":"None"},"mcp_servers":{"fetch":{"command":"uvx","args":["mcp-server-fetch"]}}}
  ```

### Non Docker

For non docker, the system will look for a `config.json` file in the current directory. This means that there is no special configuration needed. You can still use the advanced loading mechanisms if you want to, but you will need to modify the environment variables for your system as in the docker section.

