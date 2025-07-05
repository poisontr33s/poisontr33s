#!/usr/bin/env python3
"""
Meta-Automata Core System
Recursive AI-powered learning and adaptation engine
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

# Import core modules
from src.core.meta_automata import MetaAutomataEngine
from src.core.config_manager import ConfigManager
from src.vulkan.renderer import VulkanRenderer
from src.ai_integrations.orchestrator import AIOrchestrator
from src.web.server import WebServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FoundationSystem:
    """Core system orchestrating all components"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.meta_automata = None
        self.vulkan_renderer = None
        self.ai_orchestrator = None
        self.web_server = None
        
    async def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing Foundation System...")
        
        # Load configuration
        await self.config_manager.load_config()
        
        # Initialize AI orchestrator
        self.ai_orchestrator = AIOrchestrator(self.config_manager)
        await self.ai_orchestrator.initialize()
        
        # Initialize Vulkan renderer if GPU available
        try:
            self.vulkan_renderer = VulkanRenderer()
            await self.vulkan_renderer.initialize()
            logger.info("Vulkan renderer initialized")
        except Exception as e:
            logger.warning(f"Vulkan initialization failed: {e}")
            
        # Initialize meta-automata engine
        self.meta_automata = MetaAutomataEngine(
            config_manager=self.config_manager,
            ai_orchestrator=self.ai_orchestrator,
            vulkan_renderer=self.vulkan_renderer
        )
        await self.meta_automata.initialize()
        
        # Initialize web server
        self.web_server = WebServer(
            meta_automata=self.meta_automata,
            config_manager=self.config_manager
        )
        
        logger.info("Foundation System initialization complete")
        
    async def run(self):
        """Run the main system loop"""
        try:
            # Start web server
            server_task = asyncio.create_task(
                self.web_server.start()
            )
            
            # Start meta-automata processing
            automata_task = asyncio.create_task(
                self.meta_automata.run()
            )
            
            # Wait for tasks
            await asyncio.gather(server_task, automata_task)
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("Shutting down Foundation System...")
        
        if self.web_server:
            await self.web_server.stop()
            
        if self.meta_automata:
            await self.meta_automata.shutdown()
            
        if self.vulkan_renderer:
            await self.vulkan_renderer.cleanup()
            
        logger.info("Foundation System shutdown complete")

async def main():
    """Application entry point"""
    system = FoundationSystem()
    
    try:
        await system.initialize()
        await system.run()
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure Python 3.13+ compatibility
    if sys.version_info < (3, 13):
        print("Python 3.13+ required")
        sys.exit(1)
        
    # Run the main system
    asyncio.run(main())
