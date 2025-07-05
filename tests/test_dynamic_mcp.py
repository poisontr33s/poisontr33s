"""
Tests for the Dynamic MCP system
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.dynamic_mcp.core.schemas import (
    TriggerContext,
    TriggerType,
    MCPServerConfig,
    ServerCapability,
    RoutingRule,
    SystemConfig,
    RAGConfig,
)
from src.dynamic_mcp.core.router import ContextAwareRouter
from src.dynamic_mcp.core.orchestrator import DynamicMCPOrchestrator
from src.dynamic_mcp.utils.config import ConfigManager


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager"""
    config_manager = Mock(spec=ConfigManager)
    
    # Mock system config
    system_config = SystemConfig(
        servers=[
            MCPServerConfig(
                name="test-server",
                endpoint="http://localhost:8001",
                capabilities=[ServerCapability.CODE_ANALYSIS],
                priority=5,
                enabled=True,
            )
        ],
        routing_rules=[
            RoutingRule(
                name="test-rule",
                trigger_types=[TriggerType.ISSUE],
                target_servers=["test-server"],
                priority=5,
                enabled=True,
            )
        ],
        rag_config=RAGConfig(),
    )
    
    config_manager.get_config = AsyncMock(return_value=system_config)
    config_manager.load_config = AsyncMock(return_value=system_config)
    
    return config_manager


@pytest.fixture
def sample_trigger_context():
    """Create a sample trigger context"""
    return TriggerContext(
        trigger_type=TriggerType.ISSUE,
        source="test",
        content="This is a test issue about a bug in the code",
        repository="test/repo",
        issue_number=123,
        user_id="testuser",
    )


class TestContextAwareRouter:
    """Tests for the ContextAwareRouter"""
    
    @pytest.mark.asyncio
    async def test_route_trigger_basic(self, mock_config_manager, sample_trigger_context):
        """Test basic trigger routing"""
        router = ContextAwareRouter(mock_config_manager)
        
        result = await router.route_trigger(sample_trigger_context)
        
        assert result is not None
        assert isinstance(result.selected_servers, list)
        assert isinstance(result.confidence_scores, dict)
        assert isinstance(result.routing_reason, str)
        assert isinstance(result.processing_time, float)
    
    @pytest.mark.asyncio
    async def test_route_trigger_with_content_analysis(self, mock_config_manager):
        """Test routing with content analysis"""
        router = ContextAwareRouter(mock_config_manager)
        
        context = TriggerContext(
            trigger_type=TriggerType.ISSUE,
            source="test",
            content="Code analysis needed for syntax error and bug fix",
            repository="test/repo",
        )
        
        result = await router.route_trigger(context)
        
        assert result is not None
        assert len(result.selected_servers) > 0 or result.fallback_used
    
    @pytest.mark.asyncio
    async def test_route_trigger_empty_content(self, mock_config_manager):
        """Test routing with empty content"""
        router = ContextAwareRouter(mock_config_manager)
        
        context = TriggerContext(
            trigger_type=TriggerType.USER_PROMPT,
            source="test",
            content="",
        )
        
        result = await router.route_trigger(context)
        
        assert result is not None
        # Should still work even with empty content


class TestTriggerContext:
    """Tests for TriggerContext schema"""
    
    def test_trigger_context_creation(self):
        """Test creating a trigger context"""
        context = TriggerContext(
            trigger_type=TriggerType.ISSUE,
            source="test",
            content="Test content",
        )
        
        assert context.trigger_type == TriggerType.ISSUE
        assert context.source == "test"
        assert context.content == "Test content"
        assert isinstance(context.timestamp, datetime)
        assert isinstance(context.metadata, dict)
    
    def test_trigger_context_with_github_data(self):
        """Test creating a trigger context with GitHub data"""
        context = TriggerContext(
            trigger_type=TriggerType.PULL_REQUEST,
            source="github_pr",
            content="PR content",
            repository="owner/repo",
            branch="feature-branch",
            commit_sha="abc123",
            pr_number=456,
            user_id="contributor",
        )
        
        assert context.repository == "owner/repo"
        assert context.branch == "feature-branch"
        assert context.commit_sha == "abc123"
        assert context.pr_number == 456
        assert context.user_id == "contributor"


class TestSystemConfig:
    """Tests for SystemConfig schema"""
    
    def test_system_config_creation(self):
        """Test creating a system configuration"""
        config = SystemConfig(
            servers=[
                MCPServerConfig(
                    name="test-server",
                    endpoint="http://localhost:8001",
                    capabilities=[ServerCapability.CODE_ANALYSIS],
                )
            ],
            routing_rules=[
                RoutingRule(
                    name="test-rule",
                    trigger_types=[TriggerType.ISSUE],
                    target_servers=["test-server"],
                )
            ],
            rag_config=RAGConfig(),
        )
        
        assert len(config.servers) == 1
        assert len(config.routing_rules) == 1
        assert config.rag_config is not None
    
    def test_server_config_validation(self):
        """Test server configuration validation"""
        server = MCPServerConfig(
            name="test-server",
            endpoint="http://localhost:8001",
            capabilities=[ServerCapability.CODE_ANALYSIS],
            priority=5,
            timeout=30,
        )
        
        assert server.name == "test-server"
        assert server.priority == 5
        assert server.timeout == 30
        assert ServerCapability.CODE_ANALYSIS in server.capabilities


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, tmp_path):
        """Test orchestrator initialization"""
        # Create a temporary config file
        config_path = tmp_path / "test_config.yaml"
        config_content = """
servers:
  - name: "test-server"
    endpoint: "http://localhost:8001"
    capabilities: ["code_analysis"]
    
routing_rules:
  - name: "test-rule"
    trigger_types: ["issue"]
    target_servers: ["test-server"]
    
rag_config:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  vector_store_path: "./test_vector_store"
"""
        config_path.write_text(config_content)
        
        # Test orchestrator initialization
        with patch('src.dynamic_mcp.rag.retriever.RAGRetriever.initialize'), \
             patch('src.dynamic_mcp.rag.generator.ContextAwareGenerator.initialize'), \
             patch('src.dynamic_mcp.utils.mcp_client.MCPClient.initialize'):
            
            orchestrator = DynamicMCPOrchestrator(str(config_path))
            await orchestrator.initialize()
            
            # Test status retrieval
            status = await orchestrator.get_system_status()
            assert isinstance(status, dict)
            assert "total_servers" in status
            
            await orchestrator.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])