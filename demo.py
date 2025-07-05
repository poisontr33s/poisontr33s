#!/usr/bin/env python3
"""
Demo script showing the Dynamic MCP system capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dynamic_mcp.core.schemas import (
    TriggerContext,
    TriggerType,
    MCPServerConfig,
    ServerCapability,
    RoutingRule,
    RAGConfig,
    SystemConfig,
)

def demo_trigger_types():
    """Demonstrate different trigger types"""
    print("🔄 Dynamic MCP Server - Trigger Type Demo")
    print("=" * 50)
    
    # Issue trigger
    issue_context = TriggerContext(
        trigger_type=TriggerType.ISSUE,
        source="github_issue",
        content="Bug in authentication system - users cannot login",
        repository="poisontr33s/app",
        issue_number=123,
        user_id="developer123"
    )
    print(f"📋 Issue Trigger: {issue_context.trigger_type}")
    print(f"   Content: {issue_context.content}")
    print(f"   Repository: {issue_context.repository}")
    print()
    
    # Pull Request trigger
    pr_context = TriggerContext(
        trigger_type=TriggerType.PULL_REQUEST,
        source="github_pr",
        content="Add new authentication middleware with OAuth2 support",
        repository="poisontr33s/app",
        branch="feature/oauth2-auth",
        pr_number=456,
        user_id="contributor456"
    )
    print(f"🔀 Pull Request Trigger: {pr_context.trigger_type}")
    print(f"   Content: {pr_context.content}")
    print(f"   Branch: {pr_context.branch}")
    print()
    
    # Push trigger
    push_context = TriggerContext(
        trigger_type=TriggerType.PUSH,
        source="github_push",
        content="Push to main: Fix critical security vulnerability in auth",
        repository="poisontr33s/app",
        branch="main",
        commit_sha="abc123def456",
        user_id="maintainer789"
    )
    print(f"📤 Push Trigger: {push_context.trigger_type}")
    print(f"   Content: {push_context.content}")
    print(f"   Commit: {push_context.commit_sha}")
    print()

def demo_server_configurations():
    """Demonstrate server configurations"""
    print("🖥️  MCP Server Configuration Demo")
    print("=" * 50)
    
    # Code analysis server
    code_server = MCPServerConfig(
        name="code-analysis-server",
        endpoint="http://localhost:8001",
        capabilities=[ServerCapability.CODE_ANALYSIS, ServerCapability.SECURITY, ServerCapability.TESTING],
        priority=8,
        enabled=True,
        tags=["development", "quality", "security"]
    )
    print(f"🔍 {code_server.name}")
    print(f"   Endpoint: {code_server.endpoint}")
    print(f"   Capabilities: {[c.value for c in code_server.capabilities]}")
    print(f"   Priority: {code_server.priority}")
    print()
    
    # Documentation server
    doc_server = MCPServerConfig(
        name="documentation-server",
        endpoint="http://localhost:8002",
        capabilities=[ServerCapability.DOCUMENTATION, ServerCapability.AI_INFERENCE],
        priority=6,
        enabled=True,
        tags=["documentation", "help", "ai"]
    )
    print(f"📚 {doc_server.name}")
    print(f"   Endpoint: {doc_server.endpoint}")
    print(f"   Capabilities: {[c.value for c in doc_server.capabilities]}")
    print(f"   Priority: {doc_server.priority}")
    print()
    
    # Deployment server
    deploy_server = MCPServerConfig(
        name="deployment-server",
        endpoint="http://localhost:8003",
        capabilities=[ServerCapability.DEPLOYMENT, ServerCapability.MONITORING, ServerCapability.WORKFLOW_AUTOMATION],
        priority=7,
        enabled=True,
        tags=["deployment", "ops", "automation"]
    )
    print(f"🚀 {deploy_server.name}")
    print(f"   Endpoint: {deploy_server.endpoint}")
    print(f"   Capabilities: {[c.value for c in deploy_server.capabilities]}")
    print(f"   Priority: {deploy_server.priority}")
    print()
    
    return [code_server, doc_server, deploy_server]

def demo_routing_rules():
    """Demonstrate routing rules"""
    print("🎯 Routing Rules Demo")
    print("=" * 50)
    
    # Issue to code analysis rule
    issue_rule = RoutingRule(
        name="issue-code-analysis",
        trigger_types=[TriggerType.ISSUE],
        conditions={
            "keywords": ["bug", "error", "fix", "broken", "failing"],
            "repository": ".*"
        },
        target_servers=["code-analysis-server"],
        priority=9,
        enabled=True
    )
    print(f"🐛 {issue_rule.name}")
    print(f"   Triggers: {[t.value for t in issue_rule.trigger_types]}")
    print(f"   Keywords: {issue_rule.conditions.get('keywords', [])}")
    print(f"   Targets: {issue_rule.target_servers}")
    print()
    
    # PR to code review rule
    pr_rule = RoutingRule(
        name="pr-code-review",
        trigger_types=[TriggerType.PULL_REQUEST],
        conditions={},
        target_servers=["code-analysis-server"],
        priority=8,
        enabled=True
    )
    print(f"🔀 {pr_rule.name}")
    print(f"   Triggers: {[t.value for t in pr_rule.trigger_types]}")
    print(f"   Targets: {pr_rule.target_servers}")
    print()
    
    # Main branch deployment rule
    deploy_rule = RoutingRule(
        name="main-branch-deployment",
        trigger_types=[TriggerType.PUSH],
        conditions={
            "branch": "^(main|master)$"
        },
        target_servers=["deployment-server", "code-analysis-server"],
        priority=9,
        enabled=True
    )
    print(f"📤 {deploy_rule.name}")
    print(f"   Triggers: {[t.value for t in deploy_rule.trigger_types]}")
    print(f"   Branch Pattern: {deploy_rule.conditions.get('branch', '')}")
    print(f"   Targets: {deploy_rule.target_servers}")
    print()
    
    return [issue_rule, pr_rule, deploy_rule]

def demo_system_configuration():
    """Demonstrate complete system configuration"""
    print("⚙️  Complete System Configuration Demo")
    print("=" * 50)
    
    # Get components
    servers = demo_server_configurations()
    rules = demo_routing_rules()
    
    # RAG configuration
    rag_config = RAGConfig(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        vector_store_path="./vector_store",
        chunk_size=1000,
        chunk_overlap=200,
        top_k=5,
        similarity_threshold=0.7,
        enable_reranking=True,
        max_context_length=4000
    )
    print(f"🧠 RAG Configuration:")
    print(f"   Model: {rag_config.embedding_model}")
    print(f"   Vector Store: {rag_config.vector_store_path}")
    print(f"   Top K: {rag_config.top_k}")
    print(f"   Similarity Threshold: {rag_config.similarity_threshold}")
    print()
    
    # Complete system config
    system_config = SystemConfig(
        servers=servers,
        routing_rules=rules,
        rag_config=rag_config,
        log_level="INFO",
        max_concurrent_requests=10,
        request_timeout=60
    )
    print(f"🏗️  System Configuration:")
    print(f"   Total Servers: {len(system_config.servers)}")
    print(f"   Total Rules: {len(system_config.routing_rules)}")
    print(f"   Log Level: {system_config.log_level}")
    print(f"   Max Concurrent: {system_config.max_concurrent_requests}")
    print()
    
    return system_config

def demo_github_automation_scenarios():
    """Demonstrate GitHub automation scenarios"""
    print("🐙 GitHub Automation Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Bug Report Issue",
            "trigger": TriggerContext(
                trigger_type=TriggerType.ISSUE,
                source="github_issue",
                content="Critical bug: Application crashes when processing large files",
                repository="poisontr33s/file-processor",
                issue_number=789,
            ),
            "expected_servers": ["code-analysis-server"],
            "description": "Routes to code analysis for bug investigation"
        },
        {
            "name": "Feature PR Review",
            "trigger": TriggerContext(
                trigger_type=TriggerType.PULL_REQUEST,
                source="github_pr",
                content="Add new file compression algorithm with benchmarks",
                repository="poisontr33s/file-processor",
                branch="feature/compression-v2",
                pr_number=101,
            ),
            "expected_servers": ["code-analysis-server"],
            "description": "Automatic code review and quality analysis"
        },
        {
            "name": "Production Deployment",
            "trigger": TriggerContext(
                trigger_type=TriggerType.PUSH,
                source="github_push",
                content="Release v2.1.0: Performance improvements and bug fixes",
                repository="poisontr33s/file-processor",
                branch="main",
                commit_sha="def789abc123",
            ),
            "expected_servers": ["deployment-server", "code-analysis-server"],
            "description": "Deployment readiness check and final analysis"
        },
        {
            "name": "Documentation Request",
            "trigger": TriggerContext(
                trigger_type=TriggerType.ISSUE,
                source="github_issue",
                content="Please add documentation for the new API endpoints",
                repository="poisontr33s/api-service",
                issue_number=456,
            ),
            "expected_servers": ["documentation-server"],
            "description": "Routes to documentation server for help generation"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   Trigger: {scenario['trigger'].trigger_type.value}")
        print(f"   Content: {scenario['trigger'].content}")
        print(f"   Expected Servers: {scenario['expected_servers']}")
        print(f"   Description: {scenario['description']}")
        print()

def main():
    """Main demo function"""
    print("🚀 Dynamic MCP Server Orchestration Demo")
    print("=========================================")
    print()
    
    try:
        # Demonstrate trigger types
        demo_trigger_types()
        print()
        
        # Demonstrate server configurations
        demo_server_configurations()
        print()
        
        # Demonstrate routing rules
        demo_routing_rules()
        print()
        
        # Demonstrate complete system configuration
        system_config = demo_system_configuration()
        print()
        
        # Demonstrate GitHub automation scenarios
        demo_github_automation_scenarios()
        print()
        
        print("✅ Demo completed successfully!")
        print()
        print("🎯 Key Features Demonstrated:")
        print("   • Dynamic trigger processing (Issues, PRs, Pushes)")
        print("   • Intelligent server routing based on content")
        print("   • Configurable MCP server capabilities")
        print("   • Advanced routing rules with conditions")
        print("   • RAG/CAG integration for context-aware responses")
        print("   • GitHub automation workflows")
        print()
        print("🚀 Ready for production deployment!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())