"""
Context-Aware Generator for intelligent response generation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from openai import AsyncOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from ..core.schemas import TriggerContext, MCPResponse, TriggerType
from ..utils.config import ConfigManager


class ContextAwareGenerator:
    """
    Context-Aware Generation (CAG) system that generates intelligent responses
    based on trigger context and MCP server responses.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # OpenAI client
        self.openai_client: Optional[AsyncOpenAI] = None
        self._initialized = False
        
        # Response templates
        self.response_templates = self._load_response_templates()
        
    async def initialize(self):
        """Initialize the context-aware generator"""
        self.logger.info("Initializing Context-Aware Generator")
        
        try:
            config = await self.config_manager.get_config()
            
            # Initialize OpenAI client if API key is provided
            if config.openai_api_key:
                self.openai_client = AsyncOpenAI(
                    api_key=config.openai_api_key
                )
            
            self._initialized = True
            self.logger.info("Context-Aware Generator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Context-Aware Generator: {str(e)}")
            raise
    
    def _load_response_templates(self) -> Dict[str, PromptTemplate]:
        """Load response templates for different trigger types"""
        templates = {
            TriggerType.ISSUE: PromptTemplate(
                input_variables=["context", "server_responses", "rag_context"],
                template="""
Based on the GitHub issue and analysis from MCP servers, provide a comprehensive response.

Issue Context:
{context}

Server Analysis:
{server_responses}

Additional Context:
{rag_context}

Please provide:
1. Summary of the issue
2. Analysis from available tools
3. Recommended actions
4. Next steps

Response:
"""
            ),
            TriggerType.PULL_REQUEST: PromptTemplate(
                input_variables=["context", "server_responses", "rag_context"],
                template="""
Based on the Pull Request and analysis from MCP servers, provide a comprehensive review.

PR Context:
{context}

Server Analysis:
{server_responses}

Additional Context:
{rag_context}

Please provide:
1. Code review summary
2. Quality assessment
3. Security considerations
4. Recommendations

Response:
"""
            ),
            TriggerType.PUSH: PromptTemplate(
                input_variables=["context", "server_responses", "rag_context"],
                template="""
Based on the repository push and analysis from MCP servers, provide deployment insights.

Push Context:
{context}

Server Analysis:
{server_responses}

Additional Context:
{rag_context}

Please provide:
1. Changes summary
2. Deployment readiness
3. Testing recommendations
4. Monitoring suggestions

Response:
"""
            ),
            TriggerType.USER_PROMPT: PromptTemplate(
                input_variables=["context", "server_responses", "rag_context"],
                template="""
Based on the user prompt and analysis from MCP servers, provide a helpful response.

User Prompt:
{context}

Server Analysis:
{server_responses}

Additional Context:
{rag_context}

Please provide a comprehensive and actionable response addressing the user's needs.

Response:
"""
            ),
            TriggerType.QUERY: PromptTemplate(
                input_variables=["context", "server_responses", "rag_context"],
                template="""
Based on the query and analysis from MCP servers, provide relevant information.

Query:
{context}

Server Analysis:
{server_responses}

Additional Context:
{rag_context}

Please provide:
1. Direct answer to the query
2. Supporting evidence
3. Additional resources
4. Related information

Response:
"""
            ),
        }
        
        return templates
    
    async def generate_response(
        self, 
        context: TriggerContext, 
        server_responses: List[MCPResponse]
    ) -> Dict[str, Any]:
        """
        Generate a context-aware response based on trigger context and server responses.
        
        Args:
            context: The trigger context
            server_responses: List of responses from MCP servers
            
        Returns:
            Generated response with metadata
        """
        if not self._initialized:
            raise RuntimeError("Context-Aware Generator not initialized")
        
        try:
            # Prepare context for generation
            generation_context = await self._prepare_generation_context(
                context, server_responses
            )
            
            # Generate response using appropriate method
            if self.openai_client:
                response = await self._generate_with_openai(generation_context)
            else:
                response = await self._generate_with_template(generation_context)
            
            # Add metadata
            response_data = {
                "response": response,
                "metadata": {
                    "trigger_type": context.trigger_type,
                    "server_count": len(server_responses),
                    "successful_servers": len([r for r in server_responses if r.success]),
                    "generation_method": "openai" if self.openai_client else "template",
                    "generated_at": datetime.now().isoformat(),
                    "context_enhanced": context.metadata.get("rag_enhanced", False),
                }
            }
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return {
                "response": "An error occurred while generating the response.",
                "error": str(e),
                "metadata": {
                    "generation_method": "error",
                    "generated_at": datetime.now().isoformat(),
                }
            }
    
    async def _prepare_generation_context(
        self, context: TriggerContext, server_responses: List[MCPResponse]
    ) -> Dict[str, Any]:
        """Prepare context for response generation"""
        # Format context information
        context_info = {
            "trigger_type": context.trigger_type,
            "timestamp": context.timestamp.isoformat(),
            "source": context.source,
            "content": context.content or "",
            "repository": context.repository or "",
            "branch": context.branch or "",
            "user": context.user_id or "",
        }
        
        # Add trigger-specific information
        if context.issue_number:
            context_info["issue_number"] = context.issue_number
        if context.pr_number:
            context_info["pr_number"] = context.pr_number
        if context.commit_sha:
            context_info["commit_sha"] = context.commit_sha
        
        # Format server responses
        server_analysis = []
        for response in server_responses:
            if response.success and response.data:
                server_analysis.append({
                    "server": response.server_name,
                    "analysis": response.data,
                    "processing_time": response.processing_time,
                })
            elif not response.success:
                server_analysis.append({
                    "server": response.server_name,
                    "error": response.error,
                    "processing_time": response.processing_time,
                })
        
        # Get RAG context if available
        rag_context = context.metadata.get("rag_context", [])
        
        return {
            "context": context_info,
            "server_responses": server_analysis,
            "rag_context": rag_context,
        }
    
    async def _generate_with_openai(self, generation_context: Dict[str, Any]) -> str:
        """Generate response using OpenAI API"""
        try:
            # Create system message
            system_message = self._create_system_message(generation_context)
            
            # Create user message
            user_message = self._create_user_message(generation_context)
            
            # Generate response
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generating with OpenAI: {str(e)}")
            # Fallback to template generation
            return await self._generate_with_template(generation_context)
    
    def _create_system_message(self, generation_context: Dict[str, Any]) -> str:
        """Create system message for OpenAI"""
        return """
You are an intelligent assistant for a dynamic MCP (Model Context Protocol) server orchestration system.
Your role is to analyze information from multiple MCP servers and provide comprehensive, actionable responses.

Key responsibilities:
1. Synthesize information from multiple sources
2. Provide clear, actionable recommendations
3. Highlight important security or quality concerns
4. Suggest next steps and follow-up actions
5. Maintain context awareness across different trigger types

Be concise but comprehensive, focusing on practical value for the user.
"""
    
    def _create_user_message(self, generation_context: Dict[str, Any]) -> str:
        """Create user message for OpenAI"""
        context_info = generation_context["context"]
        server_responses = generation_context["server_responses"]
        rag_context = generation_context["rag_context"]
        
        # Format the message
        message_parts = [
            f"Trigger Type: {context_info['trigger_type']}",
            f"Source: {context_info['source']}",
        ]
        
        if context_info.get("content"):
            message_parts.append(f"Content: {context_info['content']}")
        
        if context_info.get("repository"):
            message_parts.append(f"Repository: {context_info['repository']}")
        
        if context_info.get("branch"):
            message_parts.append(f"Branch: {context_info['branch']}")
        
        # Add server analysis
        if server_responses:
            message_parts.append("\nServer Analysis:")
            for response in server_responses:
                if "analysis" in response:
                    message_parts.append(f"- {response['server']}: {json.dumps(response['analysis'], indent=2)}")
                elif "error" in response:
                    message_parts.append(f"- {response['server']}: Error - {response['error']}")
        
        # Add RAG context
        if rag_context:
            message_parts.append("\nAdditional Context:")
            for doc in rag_context[:3]:  # Limit to top 3 documents
                message_parts.append(f"- {doc.get('source', 'Unknown')}: {doc.get('content', '')[:200]}...")
        
        return "\n".join(message_parts)
    
    async def _generate_with_template(self, generation_context: Dict[str, Any]) -> str:
        """Generate response using templates (fallback method)"""
        try:
            context_info = generation_context["context"]
            trigger_type = TriggerType(context_info["trigger_type"])
            
            # Get appropriate template
            template = self.response_templates.get(trigger_type)
            if not template:
                template = self.response_templates[TriggerType.USER_PROMPT]
            
            # Format template variables
            template_vars = {
                "context": json.dumps(context_info, indent=2),
                "server_responses": json.dumps(generation_context["server_responses"], indent=2),
                "rag_context": json.dumps(generation_context["rag_context"], indent=2),
            }
            
            # Generate response
            response = template.format(**template_vars)
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating with template: {str(e)}")
            return "Unable to generate response due to processing error."
    
    async def generate_summary(self, orchestration_results: List[Dict[str, Any]]) -> str:
        """Generate a summary of multiple orchestration results"""
        try:
            if not orchestration_results:
                return "No results to summarize."
            
            # Prepare summary context
            summary_context = {
                "total_requests": len(orchestration_results),
                "successful_requests": len([r for r in orchestration_results if r.get("success", False)]),
                "trigger_types": list(set(r.get("trigger_context", {}).get("trigger_type") for r in orchestration_results)),
                "servers_used": list(set(
                    server for r in orchestration_results 
                    for server in r.get("routing_result", {}).get("selected_servers", [])
                )),
                "average_processing_time": sum(
                    r.get("total_processing_time", 0) for r in orchestration_results
                ) / len(orchestration_results),
            }
            
            # Generate summary
            summary = f"""
System Activity Summary:
- Total requests processed: {summary_context['total_requests']}
- Successful requests: {summary_context['successful_requests']}
- Trigger types: {', '.join(summary_context['trigger_types'])}
- Servers utilized: {', '.join(summary_context['servers_used'])}
- Average processing time: {summary_context['average_processing_time']:.2f}s

The system is operating effectively with a success rate of {(summary_context['successful_requests'] / summary_context['total_requests'] * 100):.1f}%.
"""
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return "Unable to generate summary due to processing error."
    
    def is_initialized(self) -> bool:
        """Check if the generator is initialized"""
        return self._initialized
    
    async def shutdown(self):
        """Shutdown the context-aware generator"""
        self.logger.info("Shutting down Context-Aware Generator")
        
        try:
            # Close OpenAI client if needed
            if self.openai_client:
                await self.openai_client.close()
            
            self._initialized = False
            self.logger.info("Context-Aware Generator shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during Context-Aware Generator shutdown: {str(e)}")
            raise