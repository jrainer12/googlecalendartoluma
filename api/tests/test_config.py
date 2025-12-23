#!/usr/bin/env python3
"""
Tests for config module.
"""
import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
from pathlib import Path
from app.util.config import (
    deep_merge,
    get_jwt_token,
    get_basic_auth_credentials,
    load_from_file,
    load_from_spring_cloud_config,
    AppConfig
)


class TestDeepMerge:
    """Tests for deep_merge function."""
    
    def test_simple_merge(self):
        """Test simple dictionary merge."""
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 3, "c": 4}
        result = deep_merge(d1, d2)
        assert result["a"] == 1
        assert result["b"] == 3  # d2 takes precedence
        assert result["c"] == 4
    
    def test_nested_merge(self):
        """Test nested dictionary merge."""
        d1 = {"a": {"x": 1, "y": 2}}
        d2 = {"a": {"y": 3, "z": 4}}
        result = deep_merge(d1, d2)
        assert result["a"]["x"] == 1
        assert result["a"]["y"] == 3  # d2 takes precedence
        assert result["a"]["z"] == 4


class TestGetJwtToken:
    """Tests for get_jwt_token function."""
    
    @pytest.mark.asyncio
    async def test_get_jwt_token_success(self):
        """Test successful JWT token retrieval."""
        with patch.dict(os.environ, {
            'SPRING_TENANT': 'test-tenant',
            'SPRING_CLIENT_ID': 'test-client-id',
            'SPRING_CLIENT_SECRET': 'test-secret',
            'SPRING_SCOPE': 'test-scope'
        }):
            mock_response = MagicMock()
            mock_response.json.return_value = {'access_token': 'test-token'}
            mock_response.raise_for_status = MagicMock()
            
            with patch('app.util.config.httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client_instance.post = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_client_instance
                
                token = await get_jwt_token()
                assert token == 'test-token'
    
    @pytest.mark.asyncio
    async def test_get_jwt_token_missing_credentials(self):
        """Test JWT token retrieval with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Spring Cloud Config JWT credentials"):
                await get_jwt_token()


class TestGetBasicAuthCredentials:
    """Tests for get_basic_auth_credentials function."""
    
    def test_get_basic_auth_credentials_success(self):
        """Test successful basic auth credentials retrieval."""
        with patch.dict(os.environ, {
            'SPRING_CONFIG_USERNAME': 'testuser',
            'SPRING_CONFIG_PASSWORD': 'testpass'
        }):
            username, password = get_basic_auth_credentials()
            assert username == 'testuser'
            assert password == 'testpass'
    
    def test_get_basic_auth_credentials_missing(self):
        """Test basic auth with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Spring Cloud Config basic auth credentials"):
                get_basic_auth_credentials()


class TestLoadFromFile:
    """Tests for load_from_file function."""
    
    @pytest.mark.asyncio
    async def test_load_from_file_base_config(self):
        """Test loading base configuration file."""
        config = {}
        mock_yaml_content = "app:\n  base_route_http: '/test'"
        
        # Create a proper async file mock
        mock_file = AsyncMock()
        mock_file.read = AsyncMock(return_value=mock_yaml_content)
        mock_file.__aenter__ = AsyncMock(return_value=mock_file)
        mock_file.__aexit__ = AsyncMock(return_value=None)
        
        # Mock Path(__file__) to return a path that leads to resources
        with patch('app.util.config.Path') as mock_path_class:
            # Create the path chain properly: Path(__file__).parent.parent.parent / "resources" / "application.yaml"
            mock_path_instance = MagicMock()
            mock_base_dir = MagicMock()
            mock_resources_dir = MagicMock()
            mock_config_path = MagicMock()
            
            mock_config_path.exists.return_value = True
            # When resources_dir / "application.yaml" is called, return mock_config_path
            def truediv_side_effect(path_str):
                if path_str == "application.yaml":
                    return mock_config_path
                return MagicMock()
            mock_resources_dir.__truediv__ = MagicMock(side_effect=truediv_side_effect)
            # When base_dir / "resources" is called, return mock_resources_dir
            mock_base_dir.__truediv__ = MagicMock(return_value=mock_resources_dir)
            mock_path_instance.parent.parent.parent = mock_base_dir
            mock_path_class.return_value = mock_path_instance
            
            with patch('aiofiles.open', return_value=mock_file):
                result = await load_from_file(config)
                assert 'app' in config
                assert config['app']['base_route_http'] == '/test'
    
    @pytest.mark.asyncio
    async def test_load_from_file_with_profile(self):
        """Test loading configuration with profile."""
        config = {}
        mock_yaml_content = "app:\n  debug: true"
        
        # Create async file mock
        mock_file = AsyncMock()
        mock_file.read = AsyncMock(return_value=mock_yaml_content)
        mock_file.__aenter__ = AsyncMock(return_value=mock_file)
        mock_file.__aexit__ = AsyncMock(return_value=None)
        
        with patch.dict(os.environ, {'DEPLOYMENT_PROFILE': 'prod'}):
            with patch('app.util.config.Path') as mock_path_class:
                mock_path_instance = MagicMock()
                mock_base_dir = MagicMock()
                mock_resources_dir = MagicMock()
                mock_base_path = MagicMock()
                mock_profile_path = MagicMock()
                
                mock_base_path.exists.return_value = True
                mock_profile_path.exists.return_value = True
                
                # Setup path chain
                # Setup path chain properly
                def side_effect_truediv(path_str):
                    if path_str == "resources":
                        return mock_resources_dir
                    elif path_str == "application.yaml":
                        return mock_base_path
                    elif path_str == "application-prod.yaml":
                        return mock_profile_path
                    return MagicMock()
                
                mock_resources_dir.__truediv__ = MagicMock(side_effect=side_effect_truediv)
                mock_base_dir.__truediv__.return_value = mock_resources_dir
                mock_path_instance.parent.parent.parent = mock_base_dir
                mock_path_class.return_value = mock_path_instance
                
                with patch('aiofiles.open', return_value=mock_file):
                    await load_from_file(config)
                    # Should have loaded both base and profile configs
                    assert 'app' in config


class TestLoadFromSpringCloudConfig:
    """Tests for load_from_spring_cloud_config function."""
    
    @pytest.mark.asyncio
    async def test_load_from_spring_cloud_config_disabled(self):
        """Test that Spring Cloud Config is skipped when disabled."""
        config = {'app': {'enable_spring_config': False}}
        result = await load_from_spring_cloud_config(config)
        assert result == config
    
    @pytest.mark.asyncio
    async def test_load_from_spring_cloud_config_jwt(self):
        """Test loading from Spring Cloud Config with JWT auth."""
        config = {
            'app': {
                'enable_spring_config': True,
                'spring_cloud_config_name': 'test-app',
                'spring_cloud_config_auth_type': 'jwt',
                'spring_cloud_config_service_url': 'http://test-server:8888/config'
            }
        }
        
        with patch.dict(os.environ, {
            'DEPLOYMENT_PROFILE': 'dev',
            'SPRING_TENANT': 'test-tenant',
            'SPRING_CLIENT_ID': 'test-client',
            'SPRING_CLIENT_SECRET': 'test-secret',
            'SPRING_SCOPE': 'test-scope'
        }):
            with patch('app.util.config.get_jwt_token', new_callable=AsyncMock, return_value='test-token'):
                mock_response = MagicMock()
                mock_response.text = "test:\n  value: 123"
                mock_response.raise_for_status = MagicMock()
                
                with patch('app.util.config.httpx.AsyncClient') as mock_client:
                    mock_client_instance = AsyncMock()
                    mock_client_instance.__aenter__.return_value = mock_client_instance
                    mock_client_instance.__aexit__.return_value = None
                    mock_client_instance.get = AsyncMock(return_value=mock_response)
                    mock_client.return_value = mock_client_instance
                    
                    result = await load_from_spring_cloud_config(config)
                    assert 'test' in result
    
    @pytest.mark.asyncio
    async def test_load_from_spring_cloud_config_basic(self):
        """Test loading from Spring Cloud Config with basic auth."""
        config = {
            'app': {
                'enable_spring_config': True,
                'spring_cloud_config_name': 'test-app',
                'spring_cloud_config_auth_type': 'basic',
                'spring_cloud_config_service_url': 'http://test-server:8888/config'
            }
        }
        
        with patch.dict(os.environ, {
            'DEPLOYMENT_PROFILE': 'dev',
            'SPRING_CONFIG_USERNAME': 'testuser',
            'SPRING_CONFIG_PASSWORD': 'testpass'
        }):
            mock_response = MagicMock()
            mock_response.text = "test:\n  value: 123"
            mock_response.raise_for_status = MagicMock()
            
            with patch('app.util.config.httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client_instance.get = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_client_instance
                
                result = await load_from_spring_cloud_config(config)
                assert 'test' in result
    
    @pytest.mark.asyncio
    async def test_load_from_spring_cloud_config_invalid_auth_type(self):
        """Test loading with invalid auth type (should log error, not raise)."""
        config = {
            'app': {
                'enable_spring_config': True,
                'spring_cloud_config_auth_type': 'invalid',
                'spring_cloud_config_name': 'test-app',
                'spring_cloud_config_service_url': 'http://test-server:8888/config'
            }
        }
        
        with patch.dict(os.environ, {'DEPLOYMENT_PROFILE': 'dev'}):
            # The function catches the ValueError and logs it, doesn't raise
            # It returns the config unchanged when an error occurs
            result = await load_from_spring_cloud_config(config)
            # Should return config unchanged since error was caught and logged
            assert result == config
            assert 'app' in result


class TestAppConfig:
    """Tests for AppConfig class."""
    
    def test_app_config_initialization(self):
        """Test AppConfig initialization."""
        config = AppConfig()
        assert config._config == {}
    
    def test_app_config_getitem(self):
        """Test dictionary-style access."""
        config = AppConfig()
        config._config = {'test': 'value'}
        assert config['test'] == 'value'
    
    def test_app_config_contains(self):
        """Test 'in' operator."""
        config = AppConfig()
        config._config = {'test': 'value'}
        assert 'test' in config
        assert 'missing' not in config
    
    def test_app_config_get(self):
        """Test get method."""
        config = AppConfig()
        config._config = {'test': 'value'}
        assert config.get('test') == 'value'
        assert config.get('missing', 'default') == 'default'
    
    def test_app_config_keys(self):
        """Test keys method."""
        config = AppConfig()
        config._config = {'a': 1, 'b': 2}
        assert set(config.keys()) == {'a', 'b'}
    
    @pytest.mark.asyncio
    async def test_load_config(self):
        """Test loading configuration."""
        config = AppConfig()
        
        with patch('app.util.config.load_from_file') as mock_load_file, \
             patch('app.util.config.load_from_spring_cloud_config') as mock_load_scc:
            mock_load_file.return_value = {}
            mock_load_scc.return_value = {}
            
            await config.load_config()
            
            mock_load_file.assert_called_once()
            mock_load_scc.assert_called_once()
    
    def test_get_bool(self):
        """Test get_bool method."""
        config = AppConfig()
        config._config = {'flag': True, 'str_flag': 'true'}
        assert config.get_bool('flag') is True
        assert config.get_bool('str_flag') is True
        assert config.get_bool('missing', False) is False
    
    def test_get_int(self):
        """Test get_int method."""
        config = AppConfig()
        config._config = {'number': 42, 'str_number': '100'}
        assert config.get_int('number') == 42
        assert config.get_int('str_number') == 100
        assert config.get_int('missing', 0) == 0
    
    def test_get_str(self):
        """Test get_str method."""
        config = AppConfig()
        config._config = {'text': 'hello', 'number': 123}
        assert config.get_str('text') == 'hello'
        assert config.get_str('number') == '123'
        assert config.get_str('missing', '') == ''

