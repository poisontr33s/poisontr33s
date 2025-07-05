"""
Context-aware router for dynamic MCP server selection
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import hashlib

from ..core.schemas import (
    TriggerContext,
    TriggerType,
    MCPServerConfig,
    RoutingRule,
    RoutingResult,
    ServerCapability,
)
from ..utils.similarity import calculate_text_similarity
from ..utils.config import ConfigManager


class ContextAwareRouter:
    """
    Intelligent router that analyzes trigger context and selects appropriate MCP servers
    based on content analysis, server capabilities, and routing rules.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self._server_health_cache: Dict[str, Tuple[bool, datetime]] = {}
        self._routing_cache: Dict[str, RoutingResult] = {}
        
    async def route_trigger(self, context: TriggerContext) -> RoutingResult:
        """
        Route a trigger to appropriate MCP servers based on context analysis.
        
        Args:
            context: The trigger context containing all relevant information
            
        Returns:
            RoutingResult containing selected servers and routing information
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = self._generate_cache_key(context)
        if cache_key in self._routing_cache:
            cached_result = self._routing_cache[cache_key]
            # Use cached result if less than 5 minutes old
            if (datetime.now() - cached_result.timestamp).seconds < 300:
                self.logger.info(f"Using cached routing result for {cache_key}")
                return cached_result
        
        try:
            # Get available servers
            available_servers = await self._get_available_servers()
            if not available_servers:
                return RoutingResult(
                    selected_servers=[],
                    confidence_scores={},
                    routing_reason="No available servers",
                    fallback_used=True,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )
            
            # Apply routing rules
            rule_matches = await self._apply_routing_rules(context, available_servers)
            
            # Analyze content for capability matching
            content_scores = await self._analyze_content_for_capabilities(context)
            
            # Calculate final server scores
            server_scores = await self._calculate_server_scores(
                available_servers, rule_matches, content_scores, context
            )
            
            # Select top servers
            selected_servers = self._select_top_servers(server_scores)
            
            # Create routing result
            result = RoutingResult(
                selected_servers=selected_servers,
                confidence_scores=server_scores,
                routing_reason=self._generate_routing_reason(
                    context, rule_matches, content_scores
                ),
                fallback_used=len(selected_servers) == 0,
                processing_time=(datetime.now() - start_time).total_seconds(),
            )
            
            # Cache the result
            self._routing_cache[cache_key] = result
            
            self.logger.info(
                f"Routed {context.trigger_type} to servers: {selected_servers}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in routing: {str(e)}")
            return RoutingResult(
                selected_servers=[],
                confidence_scores={},
                routing_reason=f"Routing error: {str(e)}",
                fallback_used=True,
                processing_time=(datetime.now() - start_time).total_seconds(),
            )
    
    async def _get_available_servers(self) -> List[MCPServerConfig]:
        """Get list of available and healthy MCP servers"""
        config = await self.config_manager.get_config()
        available_servers = []
        
        for server in config.servers:
            if not server.enabled:
                continue
                
            # Check server health
            is_healthy = await self._check_server_health(server)
            if is_healthy:
                available_servers.append(server)
                
        return available_servers
    
    async def _check_server_health(self, server: MCPServerConfig) -> bool:
        """Check if an MCP server is healthy and available"""
        cache_key = server.name
        
        # Check cache first
        if cache_key in self._server_health_cache:
            is_healthy, check_time = self._server_health_cache[cache_key]
            # Use cached result if less than health_check_interval seconds old
            if (datetime.now() - check_time).seconds < server.health_check_interval:
                return is_healthy
        
        try:
            # Simple health check - in real implementation, this would ping the server
            # For now, we'll assume servers are healthy if they're enabled
            is_healthy = True
            self._server_health_cache[cache_key] = (is_healthy, datetime.now())
            return is_healthy
            
        except Exception as e:
            self.logger.warning(f"Health check failed for server {server.name}: {str(e)}")
            self._server_health_cache[cache_key] = (False, datetime.now())
            return False
    
    async def _apply_routing_rules(
        self, context: TriggerContext, servers: List[MCPServerConfig]
    ) -> Dict[str, List[RoutingRule]]:
        """Apply routing rules to determine which servers match the context"""
        config = await self.config_manager.get_config()
        rule_matches = {}
        
        for server in servers:
            matching_rules = []
            
            for rule in config.routing_rules:
                if not rule.enabled:
                    continue
                    
                if server.name not in rule.target_servers:
                    continue
                    
                if context.trigger_type not in rule.trigger_types:
                    continue
                    
                # Check rule conditions
                if self._check_rule_conditions(rule, context):
                    matching_rules.append(rule)
            
            rule_matches[server.name] = matching_rules
            
        return rule_matches
    
    def _check_rule_conditions(self, rule: RoutingRule, context: TriggerContext) -> bool:
        """Check if rule conditions are met for the given context"""
        conditions = rule.conditions
        
        # Check repository condition
        if "repository" in conditions:
            repo_pattern = conditions["repository"]
            if not context.repository or not re.match(repo_pattern, context.repository):
                return False
        
        # Check content keywords
        if "keywords" in conditions and context.content:
            keywords = conditions["keywords"]
            if isinstance(keywords, str):
                keywords = [keywords]
            
            content_lower = context.content.lower()
            if not any(keyword.lower() in content_lower for keyword in keywords):
                return False
        
        # Check user condition
        if "user" in conditions:
            user_pattern = conditions["user"]
            if not context.user_id or not re.match(user_pattern, context.user_id):
                return False
        
        # Check branch condition
        if "branch" in conditions:
            branch_pattern = conditions["branch"]
            if not context.branch or not re.match(branch_pattern, context.branch):
                return False
        
        return True
    
    async def _analyze_content_for_capabilities(
        self, context: TriggerContext
    ) -> Dict[ServerCapability, float]:
        """Analyze trigger content to determine which server capabilities are needed"""
        if not context.content:
            return {}
        
        content = context.content.lower()
        capability_scores = {}
        
        # Define keywords for each capability
        capability_keywords = {
            ServerCapability.CODE_ANALYSIS: [
                "code", "analysis", "lint", "review", "syntax", "bug", "refactor",
                "quality", "complexity", "smell", "pattern", "ast", "parse"
            ],
            ServerCapability.DOCUMENTATION: [
                "docs", "documentation", "readme", "guide", "tutorial", "manual",
                "comment", "docstring", "explain", "describe", "wiki"
            ],
            ServerCapability.TESTING: [
                "test", "testing", "unittest", "pytest", "coverage", "mock",
                "assertion", "verify", "validate", "check", "spec"
            ],
            ServerCapability.DEPLOYMENT: [
                "deploy", "deployment", "release", "build", "ci", "cd", "pipeline",
                "docker", "kubernetes", "helm", "terraform"
            ],
            ServerCapability.MONITORING: [
                "monitor", "metrics", "logs", "alert", "performance", "health",
                "trace", "observability", "prometheus", "grafana"
            ],
            ServerCapability.SECURITY: [
                "security", "vulnerability", "auth", "permission", "encrypt",
                "secure", "threat", "scan", "audit", "compliance"
            ],
            ServerCapability.DATA_PROCESSING: [
                "data", "process", "transform", "etl", "pipeline", "batch",
                "stream", "analytics", "database", "query"
            ],
            ServerCapability.AI_INFERENCE: [
                "ai", "ml", "model", "inference", "predict", "classify",
                "neural", "deep", "learning", "tensorflow", "pytorch"
            ],
            ServerCapability.WORKFLOW_AUTOMATION: [
                "workflow", "automation", "trigger", "schedule", "job",
                "task", "orchestration", "pipeline", "action"
            ],
            ServerCapability.INTEGRATION: [
                "integration", "api", "webhook", "connect", "sync", "interface",
                "bridge", "adapter", "plugin", "extension"
            ],
        }
        
        for capability, keywords in capability_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in content:
                    score += 1.0
            
            # Normalize score
            if score > 0:
                capability_scores[capability] = min(score / len(keywords), 1.0)
        
        return capability_scores
    
    async def _calculate_server_scores(
        self,
        servers: List[MCPServerConfig],
        rule_matches: Dict[str, List[RoutingRule]],
        content_scores: Dict[ServerCapability, float],
        context: TriggerContext,
    ) -> Dict[str, float]:
        """Calculate final scores for each server"""
        server_scores = {}
        
        for server in servers:
            score = 0.0
            
            # Base score from server priority
            score += server.priority * 0.1
            
            # Score from matching routing rules
            rules = rule_matches.get(server.name, [])
            for rule in rules:
                score += rule.priority * 0.3
            
            # Score from capability matching
            for capability in server.capabilities:
                if capability in content_scores:
                    score += content_scores[capability] * 0.6
            
            # Bonus for exact trigger type matching
            if context.trigger_type == TriggerType.ISSUE and ServerCapability.CODE_ANALYSIS in server.capabilities:
                score += 0.2
            elif context.trigger_type == TriggerType.PULL_REQUEST and ServerCapability.CODE_ANALYSIS in server.capabilities:
                score += 0.2
            elif context.trigger_type == TriggerType.PUSH and ServerCapability.DEPLOYMENT in server.capabilities:
                score += 0.2
            
            server_scores[server.name] = score
        
        return server_scores
    
    def _select_top_servers(self, server_scores: Dict[str, float]) -> List[str]:
        """Select top servers based on scores"""
        if not server_scores:
            return []
        
        # Sort servers by score in descending order
        sorted_servers = sorted(
            server_scores.items(), key=lambda x: x[1], reverse=True
        )
        
        # Select top servers (minimum score threshold of 0.1)
        selected_servers = [
            server for server, score in sorted_servers if score > 0.1
        ]
        
        # Limit to maximum 3 servers
        return selected_servers[:3]
    
    def _generate_routing_reason(
        self,
        context: TriggerContext,
        rule_matches: Dict[str, List[RoutingRule]],
        content_scores: Dict[ServerCapability, float],
    ) -> str:
        """Generate a human-readable reason for the routing decision"""
        reasons = []
        
        # Add trigger type reason
        reasons.append(f"Trigger type: {context.trigger_type}")
        
        # Add rule matching reason
        total_rules = sum(len(rules) for rules in rule_matches.values())
        if total_rules > 0:
            reasons.append(f"Matched {total_rules} routing rules")
        
        # Add capability matching reason
        if content_scores:
            top_capabilities = sorted(
                content_scores.items(), key=lambda x: x[1], reverse=True
            )[:3]
            cap_names = [cap.value for cap, _ in top_capabilities]
            reasons.append(f"Content analysis suggests: {', '.join(cap_names)}")
        
        return "; ".join(reasons)
    
    def _generate_cache_key(self, context: TriggerContext) -> str:
        """Generate a cache key for the routing context"""
        # Create a hash of relevant context fields
        content_hash = hashlib.md5(
            f"{context.trigger_type}{context.source}{context.content or ''}{context.repository or ''}"
            .encode()
        ).hexdigest()
        return f"route_{content_hash}"
    
    async def clear_cache(self):
        """Clear routing and health check caches"""
        self._routing_cache.clear()
        self._server_health_cache.clear()
        self.logger.info("Routing caches cleared")