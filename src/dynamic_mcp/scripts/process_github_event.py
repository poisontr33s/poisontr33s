"""
Script to process GitHub events in GitHub Actions
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dynamic_mcp.core.orchestrator import DynamicMCPOrchestrator
from dynamic_mcp.core.schemas import TriggerContext, TriggerType


async def process_github_event(event_type: str, event_data: str, repository: str, ref: str, sha: str):
    """Process a GitHub event using the Dynamic MCP system"""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Parse event data
        event_payload = json.loads(event_data)
        
        # Initialize orchestrator
        orchestrator = DynamicMCPOrchestrator("config/system_config.yaml")
        await orchestrator.initialize()
        
        # Create trigger context based on event type
        context = create_trigger_context(event_type, event_payload, repository, ref, sha)
        
        # Process the trigger
        result = await orchestrator.process_trigger(context)
        
        # Save result to file for GitHub Actions to use
        result_data = {
            "success": result.success,
            "processing_time": result.total_processing_time,
            "selected_servers": result.routing_result.selected_servers,
            "response": result.final_response,
            "routing_reason": result.routing_result.routing_reason,
        }
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        # Save result
        with open("logs/processing_result.json", "w") as f:
            json.dump(result_data, f, indent=2)
        
        logger.info(f"Processed {event_type} event successfully: {result.success}")
        
        # Shutdown orchestrator
        await orchestrator.shutdown()
        
        return result.success
        
    except Exception as e:
        logger.error(f"Error processing GitHub event: {str(e)}")
        
        # Save error result
        error_data = {
            "success": False,
            "error": str(e),
            "processing_time": 0.0,
            "selected_servers": [],
            "response": None,
        }
        
        Path("logs").mkdir(exist_ok=True)
        with open("logs/processing_result.json", "w") as f:
            json.dump(error_data, f, indent=2)
        
        return False


def create_trigger_context(event_type: str, event_payload: dict, repository: str, ref: str, sha: str) -> TriggerContext:
    """Create a trigger context from GitHub event data"""
    
    # Map GitHub event types to trigger types
    event_mapping = {
        "issues": TriggerType.ISSUE,
        "pull_request": TriggerType.PULL_REQUEST,
        "push": TriggerType.PUSH,
        "pull_request_review": TriggerType.PULL_REQUEST,
        "commit_comment": TriggerType.COMMIT,
        "workflow_run": TriggerType.PUSH,
    }
    
    trigger_type = event_mapping.get(event_type, TriggerType.USER_PROMPT)
    
    # Extract content based on event type
    content = ""
    issue_number = None
    pr_number = None
    user_id = None
    branch = None
    
    if event_type == "issues":
        issue = event_payload.get("issue", {})
        content = f"Issue #{issue.get('number', 'unknown')}: {issue.get('title', '')}\\n\\n{issue.get('body', '')}"
        issue_number = issue.get("number")
        user_id = issue.get("user", {}).get("login")
        
    elif event_type == "pull_request":
        pull_request = event_payload.get("pull_request", {})
        content = f"PR #{pull_request.get('number', 'unknown')}: {pull_request.get('title', '')}\\n\\n{pull_request.get('body', '')}"
        pr_number = pull_request.get("number")
        user_id = pull_request.get("user", {}).get("login")
        branch = pull_request.get("head", {}).get("ref")
        
    elif event_type == "push":
        commits = event_payload.get("commits", [])
        commit_messages = [commit.get("message", "") for commit in commits]
        content = f"Push to {ref}\\n\\nCommits:\\n" + "\\n".join(f"- {msg}" for msg in commit_messages)
        user_id = event_payload.get("pusher", {}).get("name")
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
        
    elif event_type == "pull_request_review":
        review = event_payload.get("review", {})
        pull_request = event_payload.get("pull_request", {})
        content = f"PR Review #{pull_request.get('number', 'unknown')}: {review.get('body', '')}"
        pr_number = pull_request.get("number")
        user_id = review.get("user", {}).get("login")
        branch = pull_request.get("head", {}).get("ref")
        
    elif event_type == "commit_comment":
        comment = event_payload.get("comment", {})
        content = f"Commit Comment: {comment.get('body', '')}"
        user_id = comment.get("user", {}).get("login")
        
    elif event_type == "workflow_run":
        workflow_run = event_payload.get("workflow_run", {})
        content = f"Workflow '{workflow_run.get('name', 'unknown')}' {workflow_run.get('conclusion', 'unknown')}"
        user_id = workflow_run.get("actor", {}).get("login")
        branch = workflow_run.get("head_branch")
    
    # Create trigger context
    context = TriggerContext(
        trigger_type=trigger_type,
        source=f"github_{event_type}",
        content=content,
        repository=repository,
        branch=branch,
        commit_sha=sha,
        issue_number=issue_number,
        pr_number=pr_number,
        user_id=user_id,
        metadata={
            "event_type": event_type,
            "ref": ref,
            "github_event": event_payload,
        }
    )
    
    return context


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Process GitHub events with Dynamic MCP")
    parser.add_argument("--event-type", required=True, help="GitHub event type")
    parser.add_argument("--event-data", required=True, help="GitHub event data (JSON)")
    parser.add_argument("--repository", required=True, help="Repository name")
    parser.add_argument("--ref", required=True, help="Git ref")
    parser.add_argument("--sha", required=True, help="Commit SHA")
    
    args = parser.parse_args()
    
    try:
        # Run the async function
        success = asyncio.run(process_github_event(
            args.event_type,
            args.event_data,
            args.repository,
            args.ref,
            args.sha
        ))
        
        if success:
            print("GitHub event processed successfully")
            sys.exit(0)
        else:
            print("Failed to process GitHub event")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()