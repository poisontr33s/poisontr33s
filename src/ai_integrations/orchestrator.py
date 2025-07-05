"""
AI Orchestrator
Manages integration with multiple AI services
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import json

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Standardized AI response format"""
    service: str
    response_id: str
    content: str
    confidence: float
    metadata: Dict[str, Any]
    timestamp: float

class AIService:
    """Base class for AI service integrations"""
    
    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key
        self.session = None
        
    async def initialize(self):
        """Initialize the AI service"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> AIResponse:
        """Generate response from AI service"""
        raise NotImplementedError

class GeminiService(AIService):
    """Google Gemini AI service integration"""
    
    def __init__(self, api_key: str):
        super().__init__("gemini", api_key)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> AIResponse:
        """Generate response using Gemini"""
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
            
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1024
                }
            }
            
            url = f"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}"
            
            async with self.session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return AIResponse(
                        service="gemini",
                        response_id=f"gemini_{asyncio.get_event_loop().time()}",
                        content=content,
                        confidence=0.8,
                        metadata=result,
                        timestamp=asyncio.get_event_loop().time()
                    )
                else:
                    raise Exception(f"Gemini API error: {result}")
                    
        except Exception as e:
            logger.error(f"Gemini service error: {e}")
            raise

class OpenAIService(AIService):
    """OpenAI service integration"""
    
    def __init__(self, api_key: str):
        super().__init__("openai", api_key)
        self.base_url = "https://api.openai.com/v1"
        
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> AIResponse:
        """Generate response using OpenAI"""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            url = f"{self.base_url}/chat/completions"
            
            async with self.session.post(url, headers=headers, json=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    content = result["choices"][0]["message"]["content"]
                    return AIResponse(
                        service="openai",
                        response_id=f"openai_{asyncio.get_event_loop().time()}",
                        content=content,
                        confidence=0.9,
                        metadata=result,
                        timestamp=asyncio.get_event_loop().time()
                    )
                else:
                    raise Exception(f"OpenAI API error: {result}")
                    
        except Exception as e:
            logger.error(f"OpenAI service error: {e}")
            raise

class GitHubCopilotService(AIService):
    """GitHub Copilot integration"""
    
    def __init__(self, token: str):
        super().__init__("github_copilot", token)
        self.base_url = "https://api.github.com"
        
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> AIResponse:
        """Generate response using GitHub Copilot"""
        # Note: This is a simplified implementation
        # Real GitHub Copilot integration requires more complex authentication
        
        try:
            # Placeholder implementation
            return AIResponse(
                service="github_copilot",
                response_id=f"copilot_{asyncio.get_event_loop().time()}",
                content=f"GitHub Copilot suggestion for: {prompt[:50]}...",
                confidence=0.7,
                metadata={"status": "placeholder"},
                timestamp=asyncio.get_event_loop().time()
            )
            
        except Exception as e:
            logger.error(f"GitHub Copilot service error: {e}")
            raise

class AIOrchestrator:
    """
    Orchestrates multiple AI services for enhanced capabilities
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.services = {}
        self.response_cache = {}
        
    async def initialize(self):
        """Initialize all configured AI services"""
        logger.info("Initializing AI Orchestrator...")
        
        ai_config = self.config_manager.get_ai_config()
        
        # Initialize Gemini
        if ai_config.gemini_api_key:
            self.services["gemini"] = GeminiService(ai_config.gemini_api_key)
            await self.services["gemini"].initialize()
            logger.info("Gemini service initialized")
            
        # Initialize OpenAI
        if ai_config.openai_api_key:
            self.services["openai"] = OpenAIService(ai_config.openai_api_key)
            await self.services["openai"].initialize()
            logger.info("OpenAI service initialized")
            
        # Initialize GitHub Copilot
        if ai_config.github_token:
            self.services["github_copilot"] = GitHubCopilotService(ai_config.github_token)
            await self.services["github_copilot"].initialize()
            logger.info("GitHub Copilot service initialized")
            
        logger.info(f"AI Orchestrator initialized with {len(self.services)} services")
        
    async def generate_multi_response(self, prompt: str, context: Dict[str, Any] = None) -> List[AIResponse]:
        """Generate responses from multiple AI services"""
        responses = []
        
        # Create tasks for parallel execution
        tasks = []
        for service_name, service in self.services.items():
            task = asyncio.create_task(
                self._safe_generate_response(service, prompt, context)
            )
            tasks.append((service_name, task))
            
        # Wait for all responses
        for service_name, task in tasks:
            try:
                response = await task
                if response:
                    responses.append(response)
            except Exception as e:
                logger.error(f"Error from {service_name}: {e}")
                
        return responses
        
    async def _safe_generate_response(self, service: AIService, prompt: str, context: Dict[str, Any] = None) -> Optional[AIResponse]:
        """Safely generate response with error handling"""
        try:
            return await service.generate_response(prompt, context)
        except Exception as e:
            logger.error(f"Service {service.name} failed: {e}")
            return None
            
    async def generate_consensus_response(self, prompt: str, context: Dict[str, Any] = None) -> AIResponse:
        """Generate consensus response from multiple services"""
        responses = await self.generate_multi_response(prompt, context)
        
        if not responses:
            raise Exception("No AI services available")
            
        # Simple consensus: return response with highest confidence
        best_response = max(responses, key=lambda r: r.confidence)
        
        # Enhance with metadata from all responses
        best_response.metadata["all_responses"] = [
            {"service": r.service, "confidence": r.confidence, "content_preview": r.content[:100]}
            for r in responses
        ]
        
        return best_response
        
    async def generate_predictions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions for meta-automata"""
        
        prompt = f"Based on the following patterns and context, predict the next system state: {json.dumps(input_data, indent=2)}"
        
        try:
            response = await self.generate_consensus_response(prompt)
            
            # Parse response into structured predictions
            predictions = {
                "next_state": response.content,
                "confidence": response.confidence,
                "reasoning": response.metadata.get("reasoning", ""),
                "service_used": response.service
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction generation failed: {e}")
            return {"error": str(e)}
            
    async def get_system_feedback(self) -> Dict[str, Any]:
        """Get feedback about current system state"""
        
        feedback = {
            "active_services": list(self.services.keys()),
            "service_count": len(self.services),
            "cache_size": len(self.response_cache),
            "status": "operational"
        }
        
        return feedback
        
    async def cleanup(self):
        """Cleanup all services"""
        for service in self.services.values():
            await service.cleanup()
        logger.info("AI Orchestrator cleanup complete")
