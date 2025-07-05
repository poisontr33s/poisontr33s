"""
MCP Client for communicating with MCP servers
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import json
import aiohttp
import time

from ..core.schemas import MCPServerConfig


class MCPClient:
    """
    Client for communicating with MCP servers.
    Handles connection management, request execution, and error handling.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        self._connections: Dict[str, aiohttp.ClientSession] = {}
        
    async def initialize(self):
        """Initialize the MCP client"""
        try:
            # Create main session
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
            
            self.logger.info("MCP Client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP Client: {str(e)}")
            raise
    
    async def execute_request(
        self, 
        server_config: MCPServerConfig, 
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a request on an MCP server.
        
        Args:
            server_config: Configuration for the target MCP server
            request_data: Data to send to the server
            
        Returns:
            Response data from the server
        """
        if not self._session:
            raise RuntimeError("MCP Client not initialized")
        
        try:
            # Prepare request
            url = self._build_request_url(server_config, request_data)
            headers = self._build_request_headers(server_config)
            payload = self._build_request_payload(server_config, request_data)
            
            # Execute request with retry logic
            for attempt in range(server_config.retry_count + 1):
                try:
                    async with self._session.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=server_config.timeout)
                    ) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            return self._process_response(response_data)
                        else:
                            response_text = await response.text()
                            raise aiohttp.ClientError(
                                f"HTTP {response.status}: {response_text}"
                            )
                            
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < server_config.retry_count:
                        wait_time = 2 ** attempt  # Exponential backoff
                        self.logger.warning(
                            f"Request to {server_config.name} failed (attempt {attempt + 1}), "
                            f"retrying in {wait_time}s: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise
            
            # This should not be reached
            raise RuntimeError("Request execution failed after all retries")
            
        except Exception as e:
            self.logger.error(f"Error executing request to {server_config.name}: {str(e)}")
            raise
    
    def _build_request_url(self, server_config: MCPServerConfig, request_data: Dict[str, Any]) -> str:
        """Build the request URL for the MCP server"""
        base_url = server_config.endpoint.rstrip('/')
        
        # Determine endpoint based on trigger type
        trigger_type = request_data.get('trigger_type')
        
        if trigger_type == 'issue':
            endpoint = '/analyze/issue'
        elif trigger_type == 'pull_request':
            endpoint = '/analyze/pull_request'
        elif trigger_type == 'push':
            endpoint = '/analyze/push'
        elif trigger_type == 'user_prompt':
            endpoint = '/analyze/prompt'
        else:
            endpoint = '/analyze/generic'
        
        return f"{base_url}{endpoint}"
    
    def _build_request_headers(self, server_config: MCPServerConfig) -> Dict[str, str]:
        """Build request headers for the MCP server"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'DynamicMCP/1.0',
        }
        
        # Add authentication headers if configured
        if server_config.auth_config:
            auth_type = server_config.auth_config.get('type')
            
            if auth_type == 'bearer':
                token = server_config.auth_config.get('token')
                if token:
                    headers['Authorization'] = f'Bearer {token}'
            elif auth_type == 'api_key':
                api_key = server_config.auth_config.get('api_key')
                key_header = server_config.auth_config.get('header', 'X-API-Key')
                if api_key:
                    headers[key_header] = api_key
        
        return headers
    
    def _build_request_payload(self, server_config: MCPServerConfig, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the request payload for the MCP server"""
        payload = {
            'server_name': server_config.name,
            'capabilities': [cap.value for cap in server_config.capabilities],
            'request_id': f"{int(time.time())}_{server_config.name}",
            'timestamp': time.time(),
            'data': request_data,
        }
        
        # Add server-specific metadata
        if server_config.tags:
            payload['tags'] = server_config.tags
        
        return payload
    
    def _process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate response from MCP server"""
        try:
            # Basic response validation
            if 'status' not in response_data:
                response_data['status'] = 'success'
            
            if 'data' not in response_data:
                response_data['data'] = {}
            
            # Extract relevant data
            processed_response = {
                'status': response_data.get('status', 'success'),
                'data': response_data.get('data', {}),
                'metadata': response_data.get('metadata', {}),
                'processing_time': response_data.get('processing_time', 0.0),
                'server_version': response_data.get('server_version', 'unknown'),
            }
            
            return processed_response
            
        except Exception as e:
            self.logger.error(f"Error processing response: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'data': {},
                'metadata': {},
                'processing_time': 0.0,
            }
    
    async def health_check(self, server_config: MCPServerConfig) -> bool:
        """
        Perform a health check on an MCP server.
        
        Args:
            server_config: Configuration for the target MCP server
            
        Returns:
            True if server is healthy, False otherwise
        """
        if not self._session:
            return False
        
        try:
            url = f"{server_config.endpoint.rstrip('/')}/health"
            headers = self._build_request_headers(server_config)
            
            async with self._session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.debug(f"Health check failed for {server_config.name}: {str(e)}")
            return False
    
    async def get_server_info(self, server_config: MCPServerConfig) -> Optional[Dict[str, Any]]:
        """
        Get information about an MCP server.
        
        Args:
            server_config: Configuration for the target MCP server
            
        Returns:
            Server information or None if unavailable
        """
        if not self._session:
            return None
        
        try:
            url = f"{server_config.endpoint.rstrip('/')}/info"
            headers = self._build_request_headers(server_config)
            
            async with self._session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
                    
        except Exception as e:
            self.logger.debug(f"Failed to get server info for {server_config.name}: {str(e)}")
            return None
    
    async def list_server_capabilities(self, server_config: MCPServerConfig) -> List[str]:
        """
        List the capabilities of an MCP server.
        
        Args:
            server_config: Configuration for the target MCP server
            
        Returns:
            List of server capabilities
        """
        server_info = await self.get_server_info(server_config)
        if server_info:
            return server_info.get('capabilities', [])
        else:
            # Return configured capabilities as fallback
            return [cap.value for cap in server_config.capabilities]
    
    async def test_server_connection(self, server_config: MCPServerConfig) -> Dict[str, Any]:
        """
        Test connection to an MCP server.
        
        Args:
            server_config: Configuration for the target MCP server
            
        Returns:
            Test results
        """
        start_time = time.time()
        
        try:
            # Test health check
            is_healthy = await self.health_check(server_config)
            
            # Get server info
            server_info = await self.get_server_info(server_config)
            
            # Test basic request
            test_data = {
                'trigger_type': 'user_prompt',
                'content': 'test connection',
                'source': 'connection_test',
            }
            
            try:
                response = await self.execute_request(server_config, test_data)
                request_successful = True
                request_error = None
            except Exception as e:
                request_successful = False
                request_error = str(e)
            
            return {
                'server_name': server_config.name,
                'endpoint': server_config.endpoint,
                'healthy': is_healthy,
                'server_info': server_info,
                'request_successful': request_successful,
                'request_error': request_error,
                'response_time': time.time() - start_time,
                'timestamp': time.time(),
            }
            
        except Exception as e:
            return {
                'server_name': server_config.name,
                'endpoint': server_config.endpoint,
                'healthy': False,
                'server_info': None,
                'request_successful': False,
                'request_error': str(e),
                'response_time': time.time() - start_time,
                'timestamp': time.time(),
            }
    
    async def shutdown(self):
        """Shutdown the MCP client"""
        self.logger.info("Shutting down MCP Client")
        
        try:
            # Close all connections
            if self._session:
                await self._session.close()
            
            for session in self._connections.values():
                await session.close()
            
            self._connections.clear()
            self.logger.info("MCP Client shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during MCP Client shutdown: {str(e)}")
            raise