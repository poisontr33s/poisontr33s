"""
Core schemas and data models for dynamic MCP orchestration
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class TriggerType(str, Enum):
    """Types of triggers that can activate dynamic MCP routing"""
    USER_PROMPT = "user_prompt"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    PUSH = "push"
    COMMIT = "commit"
    META_PROMPT = "meta_prompt"
    QUERY = "query"
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"


class ServerCapability(str, Enum):
    """Capabilities that MCP servers can provide"""
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"
    DATA_PROCESSING = "data_processing"
    AI_INFERENCE = "ai_inference"
    WORKFLOW_AUTOMATION = "workflow_automation"
    INTEGRATION = "integration"


class TriggerContext(BaseModel):
    """Context information for a trigger event"""
    trigger_type: TriggerType
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(description="Source of the trigger")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content: Optional[str] = None
    user_id: Optional[str] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    issue_number: Optional[int] = None
    pr_number: Optional[int] = None


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    name: str
    endpoint: str
    capabilities: List[ServerCapability]
    priority: int = Field(default=1, ge=1, le=10)
    enabled: bool = True
    timeout: int = Field(default=30, ge=1, le=300)
    retry_count: int = Field(default=3, ge=0, le=10)
    health_check_interval: int = Field(default=60, ge=10, le=3600)
    tags: List[str] = Field(default_factory=list)
    auth_config: Optional[Dict[str, str]] = None
    environment: Optional[Dict[str, str]] = None


class RoutingRule(BaseModel):
    """Rules for routing triggers to specific MCP servers"""
    name: str
    trigger_types: List[TriggerType]
    conditions: Dict[str, Any] = Field(default_factory=dict)
    target_servers: List[str]
    priority: int = Field(default=1, ge=1, le=10)
    enabled: bool = True


class RAGConfig(BaseModel):
    """Configuration for RAG/CAG functionality"""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_path: str = "./vector_store"
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    enable_reranking: bool = True
    max_context_length: int = Field(default=4000, ge=500, le=32000)


class SystemConfig(BaseModel):
    """Main system configuration"""
    servers: List[MCPServerConfig]
    routing_rules: List[RoutingRule]
    rag_config: RAGConfig
    github_webhook_secret: Optional[str] = None
    github_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    log_level: str = "INFO"
    max_concurrent_requests: int = Field(default=10, ge=1, le=100)
    request_timeout: int = Field(default=60, ge=1, le=600)


class RoutingResult(BaseModel):
    """Result of routing a trigger to MCP servers"""
    selected_servers: List[str]
    confidence_scores: Dict[str, float]
    routing_reason: str
    fallback_used: bool = False
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class MCPResponse(BaseModel):
    """Response from an MCP server"""
    server_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class OrchestrationResult(BaseModel):
    """Final result of orchestrating a trigger across multiple MCP servers"""
    trigger_context: TriggerContext
    routing_result: RoutingResult
    server_responses: List[MCPResponse]
    final_response: Optional[Dict[str, Any]] = None
    success: bool
    total_processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)