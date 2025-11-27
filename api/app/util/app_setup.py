#!/usr/bin/env python3
"""
Application setup utilities.
Handles application initialization, logging configuration, and router mounting.
"""
import os
import logging
from fastapi import FastAPI, APIRouter
from app.util.config import config, get_logging_level, get_base_route_http
from app.util.app_config import setup_health_check_logging_filter

logger = logging.getLogger(__name__)


async def setup_app(app: FastAPI, api_router: APIRouter):
    """
    Setup the FastAPI application: load config, configure logging, mount routes.
    
    Args:
        app: FastAPI application instance
        api_router: API router to mount
    """
    try:
        await config.load_config()
        
        # Update logging level after config is loaded
        log_level = getattr(logging, get_logging_level().upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # Setup health check logging filter
        setup_health_check_logging_filter()
        
        # Log the active profile
        deployment_profile = os.getenv('DEPLOYMENT_PROFILE', 'dev')
        logger.info(f"Profile {deployment_profile} activated.")
        
        # Check if debug mode is enabled and log if so
        debug_mode = config.get_bool("app.debug", False) or (log_level == logging.DEBUG)
        if debug_mode:
            logger.debug("Debug mode has been activated")
        
        # Get base route and mount the API router with prefix
        base_route = get_base_route_http()
        # Mount router with prefix - all routes will be under base_route
        app.include_router(api_router, prefix=base_route)
        
        logger.info(f"Application started with logging level: {log_level}")
        logger.info(f"API routes mounted at base path: {base_route}")
        logger.info(f"Swagger docs available at: {base_route}/docs")
        logger.info(f"ReDoc available at: {base_route}/redoc")
        
        # Log all registered routes for debugging
        routes = [f"{route.path} ({route.methods})" for route in app.routes if hasattr(route, 'path')]
        logger.info(f"Registered routes: {routes}")
        logger.info(f"Health endpoint available at: /health")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        # Still try to mount router with default base route
        try:
            base_route = os.getenv('APP_BASE_ROUTE_HTTP', '/backend/luma-syncer')
            app.include_router(api_router, prefix=base_route)
            logger.warning(f"Using default base route: {base_route}")
        except Exception as e2:
            logger.error(f"Failed to mount router: {e2}", exc_info=True)

