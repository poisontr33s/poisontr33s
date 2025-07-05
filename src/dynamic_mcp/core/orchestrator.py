"""
Dynamic MCP Server Orchestrator - Main orchestration engine
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from ..core.schemas import (
    TriggerContext,
    MCPServerConfig,
    RoutingResult,
    MCPResponse,
    OrchestrationResult,
    SystemConfig,
)
from ..core.router import ContextAwareRouter
from ..rag.retriever import RAGRetriever
from ..rag.generator import ContextAwareGenerator
from ..utils.config import ConfigManager
from ..utils.mcp_client import MCPClient


class DynamicMCPOrchestrator:
    """
    Main orchestration engine that coordinates dynamic MCP server selection,
    RAG/CAG processing, and response generation.
    """
    
    def __init__(self, config_path: str = "config/system_config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.router = ContextAwareRouter(self.config_manager)
        self.rag_retriever = RAGRetriever(self.config_manager)
        self.context_generator = ContextAwareGenerator(self.config_manager)
        self.mcp_client = MCPClient()
        self.logger = logging.getLogger(__name__)
        
        # Internal state
        self._active_requests: Dict[str, asyncio.Task] = {}
        self._request_counter = 0
        
    async def initialize(self):
        """Initialize the orchestrator and all its components"""
        self.logger.info("Initializing Dynamic MCP Orchestrator")
        
        try:
            # Load configuration
            await self.config_manager.load_config()
            
            # Initialize RAG system
            await self.rag_retriever.initialize()
            await self.context_generator.initialize()
            
            # Initialize MCP client connections
            await self.mcp_client.initialize()
            
            self.logger.info("Dynamic MCP Orchestrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {str(e)}")
            raise
    
    async def process_trigger(self, context: TriggerContext) -> OrchestrationResult:
        """
        Process a trigger through the complete orchestration pipeline.
        
        Args:
            context: The trigger context containing all relevant information
            
        Returns:
            OrchestrationResult containing the complete processing result
        """
        start_time = time.time()
        request_id = self._generate_request_id()
        
        self.logger.info(f"Processing trigger {request_id}: {context.trigger_type}")
        
        try:
            # Step 1: Route the trigger to appropriate MCP servers
            routing_result = await self.router.route_trigger(context)
            
            if not routing_result.selected_servers:
                self.logger.warning(f"No servers selected for trigger {request_id}")
                return OrchestrationResult(
                    trigger_context=context,
                    routing_result=routing_result,
                    server_responses=[],
                    success=False,
                    total_processing_time=time.time() - start_time,
                )
            
            # Step 2: Enhance context with RAG if content is available
            enhanced_context = await self._enhance_context_with_rag(context)
            
            # Step 3: Execute requests on selected MCP servers
            server_responses = await self._execute_on_servers(
                enhanced_context, routing_result.selected_servers
            )
            
            # Step 4: Generate final response using CAG
            final_response = await self._generate_contextual_response(
                enhanced_context, server_responses
            )
            
            # Step 5: Create orchestration result
            result = OrchestrationResult(
                trigger_context=context,
                routing_result=routing_result,
                server_responses=server_responses,
                final_response=final_response,
                success=any(response.success for response in server_responses),
                total_processing_time=time.time() - start_time,
            )
            
            self.logger.info(
                f"Completed trigger {request_id} in {result.total_processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing trigger {request_id}: {str(e)}")
            return OrchestrationResult(
                trigger_context=context,
                routing_result=RoutingResult(
                    selected_servers=[],
                    confidence_scores={},
                    routing_reason=f"Processing error: {str(e)}",
                    fallback_used=True,
                    processing_time=0.0,
                ),
                server_responses=[],
                success=False,
                total_processing_time=time.time() - start_time,
            )
    
    async def _enhance_context_with_rag(self, context: TriggerContext) -> TriggerContext:
        """Enhance trigger context with relevant information from RAG system"""
        if not context.content:
            return context
        
        try:
            # Retrieve relevant documents/context
            relevant_docs = await self.rag_retriever.retrieve_relevant_context(
                context.content, context.trigger_type
            )
            
            # Add retrieved context to metadata
            enhanced_context = context.model_copy()
            enhanced_context.metadata["rag_context"] = relevant_docs
            enhanced_context.metadata["rag_enhanced"] = True
            
            return enhanced_context
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance context with RAG: {str(e)}")
            return context
    
    async def _execute_on_servers(
        self, context: TriggerContext, server_names: List[str]
    ) -> List[MCPResponse]:
        """Execute the trigger on selected MCP servers"""
        config = await self.config_manager.get_config()
        server_configs = {server.name: server for server in config.servers}
        
        # Create tasks for parallel execution
        tasks = []
        for server_name in server_names:
            if server_name in server_configs:
                task = self._execute_on_single_server(
                    context, server_configs[server_name]
                )
                tasks.append(task)
        
        # Execute tasks with timeout
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=config.request_timeout
            )
            
            # Convert exceptions to error responses
            mcp_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    mcp_responses.append(MCPResponse(
                        server_name=server_names[i],
                        success=False,
                        error=str(response),
                        processing_time=0.0,
                    ))
                else:
                    mcp_responses.append(response)
            
            return mcp_responses
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Server execution timed out after {config.request_timeout}s")
            return [
                MCPResponse(
                    server_name=server_name,
                    success=False,
                    error="Request timeout",
                    processing_time=config.request_timeout,
                )
                for server_name in server_names
            ]
    
    async def _execute_on_single_server(
        self, context: TriggerContext, server_config: MCPServerConfig
    ) -> MCPResponse:
        """Execute the trigger on a single MCP server"""
        start_time = time.time()
        
        try:
            # Prepare request data based on trigger type and server capabilities
            request_data = self._prepare_server_request(context, server_config)
            
            # Execute request on MCP server
            response_data = await self.mcp_client.execute_request(
                server_config, request_data
            )
            
            return MCPResponse(
                server_name=server_config.name,
                success=True,
                data=response_data,
                processing_time=time.time() - start_time,
            )
            
        except Exception as e:
            self.logger.error(
                f"Error executing on server {server_config.name}: {str(e)}"
            )
            return MCPResponse(
                server_name=server_config.name,
                success=False,
                error=str(e),
                processing_time=time.time() - start_time,
            )
    
    def _prepare_server_request(
        self, context: TriggerContext, server_config: MCPServerConfig
    ) -> Dict[str, Any]:
        """Prepare request data for a specific MCP server"""
        request_data = {
            "trigger_type": context.trigger_type,
            "timestamp": context.timestamp.isoformat(),
            "source": context.source,
            "metadata": context.metadata,
        }
        
        # Add content if available
        if context.content:
            request_data["content"] = context.content
        
        # Add repository information if available
        if context.repository:
            request_data["repository"] = context.repository
        
        if context.branch:
            request_data["branch"] = context.branch
        
        if context.commit_sha:
            request_data["commit_sha"] = context.commit_sha
        
        # Add issue/PR information if available
        if context.issue_number:
            request_data["issue_number"] = context.issue_number
        
        if context.pr_number:
            request_data["pr_number"] = context.pr_number
        
        # Add user information if available
        if context.user_id:
            request_data["user_id"] = context.user_id
        
        return request_data
    
    async def _generate_contextual_response(
        self, context: TriggerContext, server_responses: List[MCPResponse]
    ) -> Optional[Dict[str, Any]]:
        """Generate a contextual response using CAG based on server responses"""
        try:
            # Filter successful responses
            successful_responses = [
                response for response in server_responses if response.success
            ]
            
            if not successful_responses:
                return None
            
            # Generate contextual response
            final_response = await self.context_generator.generate_response(
                context, successful_responses
            )
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error generating contextual response: {str(e)}")
            return None
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID"""
        self._request_counter += 1
        return f"req_{int(time.time())}_{self._request_counter}"
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and health information"""
        try:
            config = await self.config_manager.get_config()
            
            # Check server health
            server_health = {}
            for server in config.servers:
                is_healthy = await self.router._check_server_health(server)
                server_health[server.name] = {
                    "healthy": is_healthy,
                    "enabled": server.enabled,
                    "capabilities": [cap.value for cap in server.capabilities],
                    "priority": server.priority,
                }
            
            # Get system metrics
            status = {
                "timestamp": datetime.now().isoformat(),
                "total_servers": len(config.servers),
                "enabled_servers": len([s for s in config.servers if s.enabled]),
                "healthy_servers": len([s for s in server_health.values() if s["healthy"]]),
                "active_requests": len(self._active_requests),
                "server_health": server_health,
                "rag_status": {
                    "initialized": self.rag_retriever.is_initialized(),
                    "vector_store_size": await self.rag_retriever.get_vector_store_size(),
                },
                "routing_rules": len(config.routing_rules),
                "enabled_routing_rules": len([r for r in config.routing_rules if r.enabled]),
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {str(e)}")
            return {"error": str(e)}
    
    async def reload_configuration(self):
        """Reload system configuration"""
        try:
            await self.config_manager.reload_config()
            await self.router.clear_cache()
            self.logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {str(e)}")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        self.logger.info("Shutting down Dynamic MCP Orchestrator")
        
        try:
            # Cancel active requests
            for request_id, task in self._active_requests.items():
                if not task.done():
                    task.cancel()
                    self.logger.info(f"Cancelled active request {request_id}")
            
            # Wait for all tasks to complete
            if self._active_requests:
                await asyncio.gather(*self._active_requests.values(), return_exceptions=True)
            
            # Shutdown components
            await self.mcp_client.shutdown()
            await self.rag_retriever.shutdown()
            await self.context_generator.shutdown()
            
            self.logger.info("Dynamic MCP Orchestrator shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            raise