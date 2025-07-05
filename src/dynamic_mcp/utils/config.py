"""
Configuration management utilities
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
import json

from ..core.schemas import SystemConfig


class ConfigManager:
    """
    Configuration manager for the dynamic MCP system.
    Handles loading, validation, and reloading of configuration.
    """
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._config: Optional[SystemConfig] = None
        self._config_cache: Dict[str, Any] = {}
        
    async def load_config(self) -> SystemConfig:
        """Load configuration from file"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Config file not found: {self.config_path}")
                return self._create_default_config()
            
            # Load config based on file extension
            if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                config_data = await self._load_yaml_config()
            elif self.config_path.suffix.lower() == '.json':
                config_data = await self._load_json_config()
            else:
                raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")
            
            # Validate and create config object
            self._config = SystemConfig(**config_data)
            
            # Cache environment variables
            self._load_environment_variables()
            
            self.logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self._config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    async def _load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Error loading YAML config: {str(e)}")
            raise
    
    async def _load_json_config(self) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading JSON config: {str(e)}")
            raise
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        try:
            # Override config with environment variables
            env_vars = {
                'GITHUB_WEBHOOK_SECRET': 'github_webhook_secret',
                'GITHUB_TOKEN': 'github_token',
                'OPENAI_API_KEY': 'openai_api_key',
                'LOG_LEVEL': 'log_level',
            }
            
            for env_var, config_key in env_vars.items():
                env_value = os.getenv(env_var)
                if env_value and self._config:
                    setattr(self._config, config_key, env_value)
                    self.logger.info(f"Loaded {config_key} from environment variable")
                    
        except Exception as e:
            self.logger.warning(f"Error loading environment variables: {str(e)}")
    
    def _create_default_config(self) -> SystemConfig:
        """Create a default configuration"""
        self.logger.info("Creating default configuration")
        
        default_config = {
            "servers": [
                {
                    "name": "code-analysis-server",
                    "endpoint": "http://localhost:8001",
                    "capabilities": ["code_analysis", "testing"],
                    "priority": 8,
                    "enabled": True,
                    "tags": ["development", "quality"]
                },
                {
                    "name": "documentation-server",
                    "endpoint": "http://localhost:8002",
                    "capabilities": ["documentation"],
                    "priority": 6,
                    "enabled": True,
                    "tags": ["documentation", "help"]
                },
                {
                    "name": "deployment-server",
                    "endpoint": "http://localhost:8003",
                    "capabilities": ["deployment", "monitoring"],
                    "priority": 7,
                    "enabled": True,
                    "tags": ["deployment", "ops"]
                }
            ],
            "routing_rules": [
                {
                    "name": "issue-to-code-analysis",
                    "trigger_types": ["issue"],
                    "conditions": {
                        "keywords": ["bug", "error", "fix", "code"]
                    },
                    "target_servers": ["code-analysis-server"],
                    "priority": 8,
                    "enabled": True
                },
                {
                    "name": "pr-to-code-analysis",
                    "trigger_types": ["pull_request"],
                    "conditions": {},
                    "target_servers": ["code-analysis-server"],
                    "priority": 9,
                    "enabled": True
                },
                {
                    "name": "push-to-deployment",
                    "trigger_types": ["push"],
                    "conditions": {
                        "branch": "main|master"
                    },
                    "target_servers": ["deployment-server"],
                    "priority": 7,
                    "enabled": True
                }
            ],
            "rag_config": {
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "vector_store_path": "./vector_store",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5,
                "similarity_threshold": 0.7,
                "enable_reranking": True,
                "max_context_length": 4000
            },
            "log_level": "INFO",
            "max_concurrent_requests": 10,
            "request_timeout": 60
        }
        
        return SystemConfig(**default_config)
    
    async def get_config(self) -> SystemConfig:
        """Get current configuration"""
        if self._config is None:
            await self.load_config()
        return self._config
    
    async def reload_config(self):
        """Reload configuration from file"""
        self.logger.info("Reloading configuration")
        await self.load_config()
    
    async def save_config(self, config: SystemConfig):
        """Save configuration to file"""
        try:
            # Convert to dict
            config_dict = config.model_dump()
            
            # Save based on file extension
            if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                await self._save_yaml_config(config_dict)
            elif self.config_path.suffix.lower() == '.json':
                await self._save_json_config(config_dict)
            else:
                raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")
            
            self._config = config
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            raise
    
    async def _save_yaml_config(self, config_dict: Dict[str, Any]):
        """Save YAML configuration file"""
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving YAML config: {str(e)}")
            raise
    
    async def _save_json_config(self, config_dict: Dict[str, Any]):
        """Save JSON configuration file"""
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving JSON config: {str(e)}")
            raise
    
    def get_cache_value(self, key: str) -> Any:
        """Get a cached value"""
        return self._config_cache.get(key)
    
    def set_cache_value(self, key: str, value: Any):
        """Set a cached value"""
        self._config_cache[key] = value
    
    def clear_cache(self):
        """Clear configuration cache"""
        self._config_cache.clear()
        self.logger.info("Configuration cache cleared")