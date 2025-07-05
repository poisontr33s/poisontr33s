"""
Dynamic MCP Server Orchestration System
"""

# Import only core schemas by default to avoid dependency issues
from .core.schemas import (
    TriggerType,
    TriggerContext,
    MCPServerConfig,
    ServerCapability,
    RoutingRule,
    RAGConfig,
    SystemConfig,
    RoutingResult,
    MCPResponse,
    OrchestrationResult,
)

__all__ = [
    "TriggerType",
    "TriggerContext",
    "MCPServerConfig", 
    "ServerCapability",
    "RoutingRule",
    "RAGConfig",
    "SystemConfig",
    "RoutingResult",
    "MCPResponse",
    "OrchestrationResult",
]

# Lazy imports for heavy components
def get_orchestrator():
    from .core.orchestrator import DynamicMCPOrchestrator
    return DynamicMCPOrchestrator

def get_router():
    from .core.router import ContextAwareRouter
    return ContextAwareRouter

def get_rag_retriever():
    from .rag.retriever import RAGRetriever
    return RAGRetriever

def get_context_generator():
    from .rag.generator import ContextAwareGenerator
    return ContextAwareGenerator

def get_github_handler():
    from .automation.github_handler import GitHubEventHandler
    return GitHubEventHandler

def get_trigger_processor():
    from .automation.trigger_processor import TriggerProcessor
    return TriggerProcessor