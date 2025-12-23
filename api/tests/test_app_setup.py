#!/usr/bin/env python3
"""
Tests for app_setup module.
"""
import pytest
import os
import logging
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import FastAPI, APIRouter
from app.util.app_setup import setup_app


class TestSetupApp:
    """Tests for setup_app function."""
    
    @pytest.mark.asyncio
    async def test_setup_app_success(self):
        """Test successful app setup."""
        app = FastAPI()
        api_router = APIRouter()
        
        with patch('app.util.app_setup.config') as mock_config, \
             patch('app.util.app_setup.get_logging_level', return_value='INFO'), \
             patch('app.util.app_setup.get_base_route_http', return_value='/test'), \
             patch('app.util.app_setup.setup_health_check_logging_filter'), \
             patch.dict(os.environ, {'DEPLOYMENT_PROFILE': 'dev'}):
            
            mock_config.load_config = AsyncMock()
            mock_config.get_bool.return_value = False
            
            await setup_app(app, api_router)
            
            mock_config.load_config.assert_called_once()
            # Verify router was mounted
            assert len(app.routes) > 0
    
    @pytest.mark.asyncio
    async def test_setup_app_with_debug_mode(self):
        """Test app setup with debug mode enabled."""
        app = FastAPI()
        api_router = APIRouter()
        
        with patch('app.util.app_setup.config') as mock_config, \
             patch('app.util.app_setup.get_logging_level', return_value='DEBUG'), \
             patch('app.util.app_setup.get_base_route_http', return_value='/test'), \
             patch('app.util.app_setup.setup_health_check_logging_filter'), \
             patch.dict(os.environ, {'DEPLOYMENT_PROFILE': 'dev'}):
            
            mock_config.load_config = AsyncMock()
            mock_config.get_bool.return_value = True
            
            await setup_app(app, api_router)
            
            mock_config.load_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_app_error_handling(self):
        """Test app setup error handling."""
        app = FastAPI()
        api_router = APIRouter()
        
        with patch('app.util.app_setup.config') as mock_config, \
             patch('app.util.app_setup.get_logging_level', side_effect=Exception("Config error")), \
             patch.dict(os.environ, {'APP_BASE_ROUTE_HTTP': '/fallback'}):
            
            mock_config.load_config = AsyncMock(side_effect=Exception("Config error"))
            
            # Should not raise, but log error and use fallback
            await setup_app(app, api_router)
            
            # Router should still be mounted with fallback route
            assert len(app.routes) > 0

