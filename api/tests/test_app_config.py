#!/usr/bin/env python3
"""
Tests for app_config module.
"""
import pytest
import os
import logging
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
from fastapi import FastAPI
from starlette.requests import Request
from app.util.app_config import (
    get_base_route_sync,
    setup_cors,
    SuppressHealthCheckLoggingMiddleware,
    setup_health_check_logging_filter,
    setup_middleware
)


class TestGetBaseRouteSync:
    """Tests for get_base_route_sync function."""
    
    def test_get_base_route_from_env(self):
        """Test getting base route from environment variable."""
        with patch.dict(os.environ, {'APP_BASE_ROUTE_HTTP': '/custom-route'}):
            result = get_base_route_sync()
            assert result == '/custom-route'
    
    def test_get_base_route_from_yaml(self):
        """Test getting base route from YAML file."""
        mock_yaml_content = "app:\n  base_route_http: '/yaml-route'"
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('builtins.open', mock_open(read_data=mock_yaml_content)):
                # Mock the Path construction
                with patch('app.util.app_config.PathlibPath') as mock_path_class:
                    mock_path_instance = MagicMock()
                    mock_path_instance.parent.parent.parent = MagicMock()
                    mock_path_instance.parent.parent.parent.__truediv__ = MagicMock(return_value=MagicMock())
                    mock_path_instance.parent.parent.parent.__truediv__.return_value.__truediv__ = MagicMock(return_value=MagicMock())
                    mock_path_instance.parent.parent.parent.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
                    mock_path_class.return_value = mock_path_instance
                    
                    result = get_base_route_sync()
                    assert result == '/yaml-route'
    
    def test_get_base_route_default(self):
        """Test getting default base route."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('builtins.open', side_effect=FileNotFoundError):
                result = get_base_route_sync()
                assert result == '/backend/luma-syncer'


class TestSetupCors:
    """Tests for setup_cors function."""
    
    def test_setup_cors_adds_middleware(self):
        """Test that CORS middleware is added."""
        app = FastAPI()
        setup_cors(app)
        
        # Check that CORS middleware was added
        cors_middleware = None
        for middleware in app.user_middleware:
            if 'CORSMiddleware' in str(middleware):
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None


class TestSuppressHealthCheckLoggingMiddleware:
    """Tests for SuppressHealthCheckLoggingMiddleware."""
    
    @pytest.mark.asyncio
    async def test_health_check_suppresses_logging(self):
        """Test that health check requests suppress logging."""
        middleware = SuppressHealthCheckLoggingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/health"
        
        mock_call_next = AsyncMock(return_value=MagicMock())
        
        access_logger = logging.getLogger("uvicorn.access")
        original_level = access_logger.level
        
        try:
            await middleware.dispatch(mock_request, mock_call_next)
            mock_call_next.assert_called_once()
        finally:
            access_logger.setLevel(original_level)
    
    @pytest.mark.asyncio
    async def test_non_health_check_passes_through(self):
        """Test that non-health check requests pass through normally."""
        middleware = SuppressHealthCheckLoggingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/events"
        
        mock_call_next = AsyncMock(return_value=MagicMock())
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        mock_call_next.assert_called_once()
        assert result is not None


class TestSetupHealthCheckLoggingFilter:
    """Tests for setup_health_check_logging_filter function."""
    
    def test_setup_health_check_logging_filter(self):
        """Test that health check logging filter is set up."""
        setup_health_check_logging_filter()
        
        access_logger = logging.getLogger("uvicorn.access")
        # Check that filter was added
        filters = [f for f in access_logger.filters if hasattr(f, 'filter')]
        assert len(filters) > 0


class TestSetupMiddleware:
    """Tests for setup_middleware function."""
    
    def test_setup_middleware_adds_all(self):
        """Test that all middleware is added."""
        app = FastAPI()
        setup_middleware(app)
        
        # Should have both health check suppression and CORS middleware
        assert len(app.user_middleware) >= 2

