#!/usr/bin/env python3
"""
Application configuration utilities for FastAPI setup.
Handles CORS, base route sync reading, and app initialization.
"""
import os
import logging
import yaml
from pathlib import Path as PathlibPath
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

logger = logging.getLogger(__name__)


def get_base_route_sync() -> str:
    """
    Get base route synchronously from environment variable, YAML file, or default.
    Used for setting docs_url at app creation time before config loads.
    """
    # Check environment variable first
    env_value = os.getenv('APP_BASE_ROUTE_HTTP')
    if env_value:
        return env_value
    
    # Try to read from YAML file synchronously
    try:
        resources_path = PathlibPath(__file__).parent.parent.parent / "resources"
        app_yaml = resources_path / "application.yaml"
        if app_yaml.exists():
            with open(app_yaml, 'r') as f:
                yaml_data = yaml.safe_load(f) or {}
                base_route = yaml_data.get('app', {}).get('base_route_http')
                if base_route:
                    return base_route
    except Exception as e:
        logger.debug(f"Could not read base_route from YAML synchronously: {e}")
    
    # Default fallback
    return '/backend/luma-syncer'


def setup_cors(app: FastAPI):
    """Configure CORS middleware for the FastAPI application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class SuppressHealthCheckLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to suppress access logging for health check endpoints."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        # Check if this is a health check request
        is_health_check = request.url.path in ["/health", "/health/"]
        
        # If it's a health check, temporarily disable access logging
        if is_health_check:
            # Get the uvicorn access logger
            access_logger = logging.getLogger("uvicorn.access")
            original_level = access_logger.level
            # Temporarily set to WARNING to suppress INFO logs
            access_logger.setLevel(logging.WARNING)
            try:
                response = await call_next(request)
                return response
            finally:
                # Restore original log level
                access_logger.setLevel(original_level)
        else:
            return await call_next(request)


def setup_health_check_logging_filter():
    """Setup logging filter to suppress health check access logs."""
    class HealthCheckFilter(logging.Filter):
        def filter(self, record):
            # Filter out health check access logs
            message = record.getMessage()
            return "/health" not in message and '"GET /health' not in message
    
    # Apply filter to uvicorn access logger
    access_logger = logging.getLogger("uvicorn.access")
    # Remove existing filters to avoid duplicates
    access_logger.filters = [f for f in access_logger.filters if not isinstance(f, HealthCheckFilter)]
    access_logger.addFilter(HealthCheckFilter())


def setup_middleware(app: FastAPI):
    """Setup all middleware for the FastAPI application."""
    # Add middleware to suppress health check logging (before CORS)
    app.add_middleware(SuppressHealthCheckLoggingMiddleware)
    # Setup CORS
    setup_cors(app)

