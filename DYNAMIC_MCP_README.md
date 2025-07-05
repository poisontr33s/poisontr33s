# Dynamic MCP Server - Automated README

This README demonstrates the automated dynamic MCP server orchestration system that adapts to various GitHub triggers.

## Overview

The Dynamic MCP Server system automatically:
- Routes GitHub events (issues, PRs, pushes, etc.) to appropriate MCP servers
- Uses RAG/CAG for intelligent context-aware responses  
- Dynamically switches between servers based on content analysis
- Provides seamless automation without manual intervention

## Architecture

```
GitHub Events → Dynamic Router → MCP Servers → RAG/CAG → Response
     ↓              ↓              ↓           ↓         ↓
   Issues      Content        Code         Context   Intelligent
     PRs       Analysis     Analysis      Retrieval  Generation
   Pushes      Capability   Testing       Vector     OpenAI/Local
   Comments    Matching     Deploy        Store      Templates
```

## Key Features

### 🔄 Dynamic Server Switching
- **Content Analysis**: Automatically analyzes trigger content to determine required capabilities
- **Server Matching**: Routes to servers with appropriate capabilities (code analysis, documentation, deployment, etc.)
- **Fallback Logic**: Graceful handling when primary servers are unavailable
- **Priority-based Routing**: High-priority events get routed to premium servers

### 🧠 RAG/CAG Integration  
- **Retrieval-Augmented Generation**: Uses vector store to find relevant context
- **Context-Aware Generation**: Generates responses based on trigger type and server analysis
- **Knowledge Base**: Automatically indexes documentation, patterns, and examples
- **Intelligent Responses**: Combines multiple server outputs into coherent recommendations

### ⚡ GitHub Automation
- **Webhook Processing**: Real-time processing of GitHub webhooks
- **Event Types Supported**:
  - Issues (opened, edited, closed)
  - Pull Requests (opened, reviewed, merged)
  - Pushes (all branches, with branch-specific routing)
  - Comments (issue, PR, commit comments)
  - Workflow runs (success/failure analysis)

### 🎯 Trigger-Based Routing
- **Issue Analysis**: Routes bug reports to code analysis servers
- **PR Reviews**: Automatically triggers code quality and security analysis  
- **Deployment Events**: Main branch pushes trigger deployment readiness checks
- **Documentation Requests**: Routes doc-related issues to documentation servers

## Configuration

The system uses `config/system_config.yaml` for configuration:

```yaml
servers:
  - name: "code-analysis-server"
    endpoint: "http://localhost:8001"
    capabilities: ["code_analysis", "testing", "security"]
    priority: 8

routing_rules:
  - name: "issue-code-analysis"
    trigger_types: ["issue"]
    conditions:
      keywords: ["bug", "error", "fix", "code"]
    target_servers: ["code-analysis-server"]
```

## Usage Examples

### 1. Issue Processing
When an issue is created with content "Bug in authentication code":
1. System analyzes content → detects "bug" and "code" keywords
2. Routes to code-analysis-server based on capabilities
3. RAG system retrieves relevant auth documentation
4. Generates comprehensive response with debugging steps

### 2. Pull Request Analysis  
When a PR is opened:
1. Automatically routes to code-analysis-server
2. Performs code quality, security, and test coverage analysis
3. Generates detailed review with recommendations
4. Posts review comment with findings

### 3. Deployment Automation
When code is pushed to main branch:
1. Routes to deployment-server and code-analysis-server
2. Checks deployment readiness and runs final analysis
3. Generates deployment report
4. Can trigger automated deployment if conditions are met

## Installation & Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
export GITHUB_WEBHOOK_SECRET="your_webhook_secret"
export GITHUB_TOKEN="your_github_token"  
export OPENAI_API_KEY="your_openai_key"
```

3. **Set up MCP servers**: Configure your MCP servers in `config/system_config.yaml`

4. **Start the system**:
```bash
python -m src.dynamic_mcp.main --config config/system_config.yaml
```

## GitHub Actions Integration

The system includes automated GitHub Actions workflows that:
- Process events in real-time
- Run health checks on MCP servers  
- Perform deployment analysis
- Generate automated responses

See `.github/workflows/dynamic-mcp-automation.yml` for the complete workflow.

## API Endpoints

- `POST /webhook/github` - GitHub webhook endpoint
- `POST /trigger/manual` - Manual trigger processing
- `GET /status` - System status and metrics
- `GET /health` - Health check
- `POST /config/reload` - Reload configuration

## Monitoring & Metrics

The system provides comprehensive monitoring:
- **Server Health**: Real-time health checks of all MCP servers
- **Processing Metrics**: Success rates, response times, error rates
- **Queue Status**: Trigger queue size and processing backlog
- **Usage Analytics**: Most used servers, trigger types, patterns

## Security

- **Webhook Verification**: Cryptographic verification of GitHub webhooks
- **API Authentication**: Support for various auth methods (API keys, Bearer tokens)
- **Rate Limiting**: Built-in protection against abuse
- **Input Sanitization**: Safe handling of user-generated content

## Extensibility

The system is designed for easy extension:
- **Custom Triggers**: Add new trigger types and processors
- **Server Plugins**: Integrate new MCP servers with minimal configuration
- **RAG Sources**: Add custom knowledge sources to the vector store
- **Response Templates**: Create custom response templates for different scenarios

This automated system eliminates the need for manual server selection and provides intelligent, context-aware responses to all GitHub activities.