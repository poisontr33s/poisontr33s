"""
Main application entry point for the Dynamic MCP system
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import argparse

from .core.orchestrator import DynamicMCPOrchestrator
from .automation.github_handler import GitHubEventHandler
from .utils.config import ConfigManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dynamic_mcp.log')
    ]
)

logger = logging.getLogger(__name__)


class DynamicMCPApp:
    """Main application class for the Dynamic MCP system"""
    
    def __init__(self, config_path: str = "config/system_config.yaml"):
        self.config_path = config_path
        self.orchestrator: Optional[DynamicMCPOrchestrator] = None
        self.github_handler: Optional[GitHubEventHandler] = None
        self.app: Optional[FastAPI] = None
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self):
        """Initialize the application"""
        logger.info("Initializing Dynamic MCP Application")
        
        try:
            # Initialize orchestrator
            self.orchestrator = DynamicMCPOrchestrator(self.config_path)
            await self.orchestrator.initialize()
            
            # Initialize GitHub handler
            config_manager = self.orchestrator.config_manager
            self.github_handler = GitHubEventHandler(self.orchestrator, config_manager)
            
            # Initialize FastAPI app
            self.app = self._create_fastapi_app()
            
            logger.info("Dynamic MCP Application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            raise
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(
            title="Dynamic MCP Server",
            description="Dynamic MCP server orchestration with RAG/CAG capabilities",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add API routes to the FastAPI app"""
        
        @app.get("/")
        async def root():
            """Root endpoint"""
            return {"message": "Dynamic MCP Server", "status": "running"}
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                status = await self.orchestrator.get_system_status()
                return {"status": "healthy", "system": status}
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                raise HTTPException(status_code=500, detail="System unhealthy")
        
        @app.post("/webhook/github")
        async def github_webhook(request: Request):
            """GitHub webhook endpoint"""
            try:
                return await self.github_handler.handle_webhook(request)
            except Exception as e:
                logger.error(f"GitHub webhook error: {str(e)}")
                raise HTTPException(status_code=500, detail="Webhook processing failed")
        
        @app.post("/trigger/manual")
        async def manual_trigger(request: Request):
            """Manual trigger endpoint"""
            try:
                trigger_data = await request.json()
                result = await self.github_handler.process_manual_trigger(trigger_data)
                return result
            except Exception as e:
                logger.error(f"Manual trigger error: {str(e)}")
                raise HTTPException(status_code=500, detail="Manual trigger failed")
        
        @app.get("/status")
        async def system_status():
            """Get detailed system status"""
            try:
                status = await self.orchestrator.get_system_status()
                return status
            except Exception as e:
                logger.error(f"Status check failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Status check failed")
        
        @app.post("/config/reload")
        async def reload_config():
            """Reload system configuration"""
            try:
                await self.orchestrator.reload_configuration()
                return {"status": "configuration reloaded"}
            except Exception as e:
                logger.error(f"Config reload failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Config reload failed")
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the server"""
        if not self.app:
            raise RuntimeError("Application not initialized")
        
        try:
            # Start GitHub event processing
            await self.github_handler.start_processing()
            
            # Create server configuration
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
            # Start server
            server = uvicorn.Server(config)
            logger.info(f"Starting server on {host}:{port}")
            
            # Set up signal handlers
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, shutting down...")
                self._shutdown_event.set()
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Run server with graceful shutdown
            await server.serve()
            
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise
    
    async def shutdown(self):
        """Shutdown the application"""
        logger.info("Shutting down Dynamic MCP Application")
        
        try:
            # Stop GitHub event processing
            if self.github_handler:
                await self.github_handler.shutdown()
            
            # Shutdown orchestrator
            if self.orchestrator:
                await self.orchestrator.shutdown()
            
            logger.info("Dynamic MCP Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            raise


async def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="Dynamic MCP Server")
    parser.add_argument("--config", default="config/system_config.yaml", help="Configuration file path")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Create and initialize app
    app = DynamicMCPApp(args.config)
    
    try:
        await app.initialize()
        await app.start_server(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())