#!/usr/bin/env python3
"""
Configuration module for loading application settings from resources/application-{profile}.yaml
and optionally from Spring Cloud Config.
"""
import os
import yaml
import logging
import httpx
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def deep_merge(d1: dict, d2: dict) -> dict:
    """Deep merge two dictionaries, with d2 taking precedence."""
    for k, v in d2.items():
        if isinstance(v, dict) and k in d1 and isinstance(d1[k], dict):
            deep_merge(d1[k], v)
        else:
            d1[k] = v
    return d1


async def get_jwt_token() -> str:
    """Get JWT token from Azure AD for Spring Cloud Config authentication."""
    tenant = os.getenv('SPRING_TENANT')
    client_id = os.getenv('SPRING_CLIENT_ID')
    client_secret = os.getenv('SPRING_CLIENT_SECRET')
    scope = os.getenv('SPRING_SCOPE')

    if not all([tenant, client_id, client_secret, scope]):
        raise ValueError("Missing required Spring Cloud Config credentials")

    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        response.raise_for_status()
        response_json = response.json()
        return response_json['access_token']


async def load_from_file(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load configuration from resources/application.yaml and application-{profile}.yaml files."""
    # Go up from app/util/ to api/ directory, then to resources/
    base_dir = Path(__file__).parent.parent.parent
    resources_dir = base_dir / "resources"
    
    # Load base application.yaml first
    base_config_path = resources_dir / "application.yaml"
    if base_config_path.exists():
        try:
            async with aiofiles.open(base_config_path, 'r') as ymlfile:
                cfg = yaml.safe_load(await ymlfile.read()) or {}
            deep_merge(config, cfg)
            logger.info(f"Loaded base configuration from {base_config_path}")
        except Exception as e:
            logger.error(f"Failed to load base config from {base_config_path}: {e}")
    
    # Load profile-specific config
    deployment_profile = os.getenv('DEPLOYMENT_PROFILE', 'dev')
    profile_config_path = resources_dir / f"application-{deployment_profile}.yaml"
    
    if profile_config_path.exists():
        try:
            async with aiofiles.open(profile_config_path, 'r') as ymlfile:
                cfg = yaml.safe_load(await ymlfile.read()) or {}
            deep_merge(config, cfg)
            logger.info(f"Loaded profile configuration from {profile_config_path} (profile: {deployment_profile})")
        except Exception as e:
            logger.error(f"Failed to load profile config from {profile_config_path}: {e}")
    else:
        logger.debug(f"Profile config file not found: {profile_config_path}, using base config only")
    
    return config


async def load_from_spring_cloud_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load configuration from Spring Cloud Config if enabled."""
    # Check if Spring Cloud Config fetching is enabled
    if not config.get('app', {}).get('enable_spring_config', False):
        return config
    
    try:
        jwt_token = await get_jwt_token()
        app_name = config['app']['spring_cloud_config_name']
        profile = os.getenv('DEPLOYMENT_PROFILE', 'dev')
        sccs_url = f"http://spring-cloud-config:8888/backend/spring-cloud-config/{app_name}-{profile}.yml"
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {jwt_token}"}
            response = await client.get(sccs_url, headers=headers)
            response.raise_for_status()
            spring_cfg = yaml.safe_load(response.text) or {}
            deep_merge(config, spring_cfg)
            logger.info(f"Loaded configuration from Spring Cloud Config: {sccs_url}")
    except Exception as e:
        logger.error(f"Failed to load config from Spring Cloud Config: {e}")
    
    return config


class AppConfig:
    """Application configuration loaded from YAML files and Spring Cloud Config.
    
    Supports dictionary-style access like Quart's app.config:
        config['events']['cover_url']
        config.get('events', {}).get('cover_url')
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        # Note: This is synchronous initialization, but actual loading happens in load_config()
        # For async loading, use load_config() separately after app startup
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access: config['events']"""
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists: 'events' in config"""
        return key in self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get method: config.get('events', {})"""
        return self._config.get(key, default)
    
    def keys(self):
        """Get all top-level keys"""
        return self._config.keys()
    
    def items(self):
        """Get all top-level items"""
        return self._config.items()
    
    def values(self):
        """Get all top-level values"""
        return self._config.values()
    
    async def load_config(self):
        """Load configuration asynchronously from files and Spring Cloud Config."""
        # Start with environment variables as base
        self._config = {}
        
        # Load from file
        await load_from_file(self._config)
        
        # Load from Spring Cloud Config if enabled
        await load_from_spring_cloud_config(self._config)
        
        logger.info("Configuration loaded successfully")
    
    def _get_env_or_config(self, key_path: str, default: Any = None) -> Any:
        """Get value from environment variable first, then from config."""
        # Check environment variables first (highest priority)
        env_key = key_path.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            # Try to convert to appropriate type
            if env_value.lower() in ('true', 'false'):
                return env_value.lower() == 'true'
            try:
                return int(env_value)
            except ValueError:
                try:
                    return float(env_value)
                except ValueError:
                    return env_value
        
        # Then check YAML config
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value if value is not None else default
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'app.logging_level')."""
        return self._get_env_or_config(key_path, default)
    
    def get_bool(self, key_path: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(key_path, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def get_int(self, key_path: str, default: int = 0) -> int:
        """Get integer configuration value."""
        value = self.get(key_path, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_str(self, key_path: str, default: str = "") -> str:
        """Get string configuration value."""
        value = self.get(key_path, default)
        return str(value) if value is not None else default


# Global config instance
config = AppConfig()

# Convenience functions for common config values
def get_base_route_http() -> str:
    """Get the base HTTP route for the API."""
    return config.get_str("app.base_route_http", "/backend/luma-syncer")

def get_logging_level() -> str:
    """Get the logging level."""
    return config.get_str("app.logging_level", "INFO")

def is_spring_config_enabled() -> bool:
    """Check if Spring Cloud Config is enabled."""
    return config.get_bool("app.enable_spring_config", False)

def get_spring_cloud_config_name() -> str:
    """Get the Spring Cloud Config application name."""
    return config.get_str("app.spring_cloud_config_name", "api-google-calendar-to-luma")

