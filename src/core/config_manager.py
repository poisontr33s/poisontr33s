"""
Configuration Manager for Meta-Automata System
Handles AI API keys, system settings, and dynamic configuration
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class AIConfig:
    """AI service configuration"""
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    github_token: Optional[str] = None
    microsoft_copilot_key: Optional[str] = None
    
@dataclass
class SystemConfig:
    """System-level configuration"""
    vulkan_enabled: bool = True
    cuda_enabled: bool = True
    max_workers: int = 8
    log_level: str = "INFO"
    port: int = 3000
    
@dataclass
class LearningConfig:
    """Recursive learning configuration"""
    adaptation_rate: float = 0.1
    memory_depth: int = 1000
    pattern_threshold: float = 0.8
    evolution_cycles: int = 100

class ConfigManager:
    """Dynamic configuration management with live reloading"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        self.ai_config = AIConfig()
        self.system_config = SystemConfig()
        self.learning_config = LearningConfig()
        
        # Config file paths
        self.ai_config_path = self.config_dir / "ai_config.yaml"
        self.system_config_path = self.config_dir / "system_config.yaml"
        self.learning_config_path = self.config_dir / "learning_config.yaml"
        
    async def load_config(self):
        """Load configuration from files and environment"""
        logger.info("Loading configuration...")
        
        # Load from environment variables
        self._load_from_env()
        
        # Load from config files
        await self._load_config_files()
        
        # Validate configuration
        self._validate_config()
        
        logger.info("Configuration loaded successfully")
        
    def _load_from_env(self):
        """Load configuration from environment variables"""
        
        # AI Configuration
        self.ai_config.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.ai_config.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ai_config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.ai_config.github_token = os.getenv("GITHUB_TOKEN")
        self.ai_config.microsoft_copilot_key = os.getenv("MICROSOFT_COPILOT_KEY")
        
        # System Configuration
        if os.getenv("VULKAN_ENABLED"):
            self.system_config.vulkan_enabled = os.getenv("VULKAN_ENABLED").lower() == "true"
        if os.getenv("CUDA_ENABLED"):
            self.system_config.cuda_enabled = os.getenv("CUDA_ENABLED").lower() == "true"
        if os.getenv("MAX_WORKERS"):
            self.system_config.max_workers = int(os.getenv("MAX_WORKERS"))
        if os.getenv("PORT"):
            self.system_config.port = int(os.getenv("PORT"))
            
    async def _load_config_files(self):
        """Load configuration from YAML files"""
        
        # Load AI config
        if self.ai_config_path.exists():
            with open(self.ai_config_path, 'r') as f:
                ai_data = yaml.safe_load(f)
                for key, value in ai_data.items():
                    if hasattr(self.ai_config, key):
                        setattr(self.ai_config, key, value)
                        
        # Load system config
        if self.system_config_path.exists():
            with open(self.system_config_path, 'r') as f:
                system_data = yaml.safe_load(f)
                for key, value in system_data.items():
                    if hasattr(self.system_config, key):
                        setattr(self.system_config, key, value)
                        
        # Load learning config
        if self.learning_config_path.exists():
            with open(self.learning_config_path, 'r') as f:
                learning_data = yaml.safe_load(f)
                for key, value in learning_data.items():
                    if hasattr(self.learning_config, key):
                        setattr(self.learning_config, key, value)
                        
    def _validate_config(self):
        """Validate configuration settings"""
        
        # Check for required AI keys
        if not any([
            self.ai_config.gemini_api_key,
            self.ai_config.openai_api_key,
            self.ai_config.anthropic_api_key
        ]):
            logger.warning("No AI API keys configured - AI features will be limited")
            
        # Validate system settings
        if self.system_config.max_workers < 1:
            self.system_config.max_workers = 1
        if self.system_config.port < 1000 or self.system_config.port > 65535:
            self.system_config.port = 3000
            
    async def save_config(self):
        """Save current configuration to files"""
        
        # Save AI config
        with open(self.ai_config_path, 'w') as f:
            yaml.dump(asdict(self.ai_config), f, default_flow_style=False)
            
        # Save system config
        with open(self.system_config_path, 'w') as f:
            yaml.dump(asdict(self.system_config), f, default_flow_style=False)
            
        # Save learning config
        with open(self.learning_config_path, 'w') as f:
            yaml.dump(asdict(self.learning_config), f, default_flow_style=False)
            
        logger.info("Configuration saved")
        
    def get_ai_config(self) -> AIConfig:
        """Get AI configuration"""
        return self.ai_config
        
    def get_system_config(self) -> SystemConfig:
        """Get system configuration"""
        return self.system_config
        
    def get_learning_config(self) -> LearningConfig:
        """Get learning configuration"""
        return self.learning_config
        
    def update_config(self, section: str, key: str, value: Any):
        """Dynamically update configuration"""
        
        if section == "ai":
            if hasattr(self.ai_config, key):
                setattr(self.ai_config, key, value)
        elif section == "system":
            if hasattr(self.system_config, key):
                setattr(self.system_config, key, value)
        elif section == "learning":
            if hasattr(self.learning_config, key):
                setattr(self.learning_config, key, value)
                
        logger.info(f"Updated {section}.{key} = {value}")
