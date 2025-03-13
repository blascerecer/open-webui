# First, let's modify the __init__.py file to add a reload_config function

import os
from mcp_bridge.config.env_subst import substitute_env_vars
from mcp_bridge.config.initial import initial_settings
from mcp_bridge.config.final import Settings
from typing import Any, Callable
from loguru import logger
from pydantic import ValidationError
import sys
from deepmerge import always_merger

__all__ = ["config", "reload_config", "get_config_files"]

config: Settings = None  # type: ignore
_config_files = ["mcp_config.json"]  # Keep track of loaded config files

def load_configs() -> Settings:
    """Load and merge all configurations"""
    global _config_files
    _config_files = []
    
    configs: list[dict[str, Any]] = []
    
    # Load the config
    if initial_settings.file is not None:
        logger.info(f"Loading config from {initial_settings.file}")
        from .file import load_config

        configs.append(load_config(initial_settings.file))
        _config_files.append(initial_settings.file)
        
        # Also load mcp_config.json
        mcp_config_file = initial_settings.file.replace("config.json", "mcp_config.json")
        if os.path.exists(mcp_config_file):
            logger.info(f"Loading MCP config from {mcp_config_file}")
            configs.append(load_config(mcp_config_file))
            _config_files.append(mcp_config_file)

    if initial_settings.http_url is not None:
        logger.info(f"Loading config from {initial_settings.http_url}")
        from .http import load_config

        configs.append(load_config(initial_settings.http_url))

    if initial_settings.json is not None:
        logger.info("Loading config from json string")
        configs.append(initial_settings.json)

    # Merge the configs
    result: dict = {}
    for cfg in configs:
        always_merger.merge(result, cfg)

    result = substitute_env_vars(result)

    # Build the config
    try:
        return Settings(**result)
    except ValidationError as e:
        logger.error("unable to load a valid configuration")
        for error in e.errors():
            logger.error(f"{error['loc'][0]}: {error['msg']}")
        exit(1)

def reload_config() -> Settings:
    """Reload the configuration from all sources"""
    global config
    
    logger.info("Reloading configuration...")
    
    # Store old config for comparison
    old_config_dict = None
    try:
        if config:
            old_config_dict = config.dict()
    except Exception as e:
        logger.warning(f"Could not serialize old config for comparison: {e}")
    
    # Load new config
    new_config = load_configs()
    
    # Compare configs if possible
    if old_config_dict:
        try:
            new_config_dict = new_config.dict()
            differences = []
            for key in new_config_dict:
                if key in old_config_dict and new_config_dict[key] != old_config_dict[key]:
                    differences.append(f"{key}: {old_config_dict[key]} -> {new_config_dict[key]}")
            
            if differences:
                logger.info(f"Configuration changes detected: {', '.join(differences)}")
            else:
                logger.info("Configuration reloaded but no changes detected")
        except Exception as e:
            logger.warning(f"Error comparing configurations: {e}")
    
    # Update the global config
    config = new_config
    
    # Update logger configuration if needed
    if config.logging.log_level != "DEBUG":
        logger.remove()
        logger.add(
            sys.stderr,
            format="{time} {level} {message}",
            level=config.logging.log_level,
            colorize=True,
        )
    
    logger.info("Configuration reloaded successfully")
    return config

def get_config_files() -> list[str]:
    """Return the list of loaded config files"""
    return _config_files

# Initial loading of the configuration
if initial_settings.load_config:
    config = load_configs()
    
    if config.logging.log_level != "DEBUG":
        logger.remove()
        logger.add(
            sys.stderr,
            format="{time} {level} {message}",
            level=config.logging.log_level,
            colorize=True,
        )