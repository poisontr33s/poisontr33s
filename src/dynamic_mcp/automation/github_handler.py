"""
GitHub Event Handler for processing GitHub webhooks and events
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib
import hmac

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import git

from ..core.schemas import TriggerContext, TriggerType
from ..core.orchestrator import DynamicMCPOrchestrator
from ..utils.config import ConfigManager


class GitHubEventHandler:
    """
    Handler for GitHub events and webhooks that triggers dynamic MCP orchestration.
    """
    
    def __init__(self, orchestrator: DynamicMCPOrchestrator, config_manager: ConfigManager):
        self.orchestrator = orchestrator
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Event processing queue
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        
        # Supported event types
        self.supported_events = {
            "issues": self._handle_issue_event,
            "pull_request": self._handle_pull_request_event,
            "push": self._handle_push_event,
            "pull_request_review": self._handle_pr_review_event,
            "commit_comment": self._handle_commit_comment_event,
            "workflow_run": self._handle_workflow_run_event,
        }
    
    async def start_processing(self):
        """Start the event processing task"""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_events())
            self.logger.info("Started GitHub event processing")
    
    async def stop_processing(self):
        """Stop the event processing task"""
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Stopped GitHub event processing")
    
    async def handle_webhook(self, request: Request) -> JSONResponse:
        """
        Handle incoming GitHub webhook requests.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JSONResponse with processing status
        """
        try:
            # Verify webhook signature
            if not await self._verify_webhook_signature(request):
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
            
            # Get event type
            event_type = request.headers.get("X-GitHub-Event")
            if not event_type:
                raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")
            
            # Get payload
            payload = await request.json()
            
            # Queue event for processing
            await self._queue_event(event_type, payload)
            
            return JSONResponse({"status": "accepted", "event_type": event_type})
            
        except Exception as e:
            self.logger.error(f"Error handling webhook: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _verify_webhook_signature(self, request: Request) -> bool:
        """Verify GitHub webhook signature"""
        try:
            config = await self.config_manager.get_config()
            webhook_secret = config.github_webhook_secret
            
            if not webhook_secret:
                # If no secret configured, skip verification
                return True
            
            # Get signature from headers
            signature = request.headers.get("X-Hub-Signature-256")
            if not signature:
                return False
            
            # Get request body
            body = await request.body()
            
            # Calculate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            expected_signature = f"sha256={expected_signature}"
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def _queue_event(self, event_type: str, payload: Dict[str, Any]):
        """Queue an event for processing"""
        try:
            await self._event_queue.put({
                "event_type": event_type,
                "payload": payload,
                "timestamp": datetime.now(),
            })
            
            self.logger.info(f"Queued GitHub event: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Error queuing event: {str(e)}")
    
    async def _process_events(self):
        """Process events from the queue"""
        while True:
            try:
                # Get event from queue
                event = await self._event_queue.get()
                
                # Process the event
                await self._process_single_event(event)
                
                # Mark task as done
                self._event_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")
    
    async def _process_single_event(self, event: Dict[str, Any]):
        """Process a single GitHub event"""
        try:
            event_type = event["event_type"]
            payload = event["payload"]
            
            # Check if we support this event type
            if event_type not in self.supported_events:
                self.logger.info(f"Unsupported event type: {event_type}")
                return
            
            # Handle the event
            handler = self.supported_events[event_type]
            await handler(payload)
            
        except Exception as e:
            self.logger.error(f"Error processing single event: {str(e)}")
    
    async def _handle_issue_event(self, payload: Dict[str, Any]):
        """Handle GitHub issue events"""
        try:
            action = payload.get("action")
            issue = payload.get("issue", {})
            repository = payload.get("repository", {})
            
            # Only process certain actions
            if action not in ["opened", "edited", "reopened", "closed"]:
                return
            
            # Create trigger context
            context = TriggerContext(
                trigger_type=TriggerType.ISSUE,
                source=f"github_issue_{action}",
                content=f"Issue #{issue.get('number', 'unknown')}: {issue.get('title', '')}\\n\\n{issue.get('body', '')}",
                repository=repository.get("full_name"),
                issue_number=issue.get("number"),
                user_id=issue.get("user", {}).get("login"),
                metadata={
                    "action": action,
                    "issue_url": issue.get("html_url"),
                    "repository_url": repository.get("html_url"),
                    "labels": [label.get("name") for label in issue.get("labels", [])],
                    "state": issue.get("state"),
                }
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            self.logger.info(f"Processed issue event: {action} - Success: {result.success}")
            
        except Exception as e:
            self.logger.error(f"Error handling issue event: {str(e)}")
    
    async def _handle_pull_request_event(self, payload: Dict[str, Any]):
        """Handle GitHub pull request events"""
        try:
            action = payload.get("action")
            pull_request = payload.get("pull_request", {})
            repository = payload.get("repository", {})
            
            # Only process certain actions
            if action not in ["opened", "edited", "reopened", "closed", "ready_for_review"]:
                return
            
            # Create trigger context
            context = TriggerContext(
                trigger_type=TriggerType.PULL_REQUEST,
                source=f"github_pr_{action}",
                content=f"PR #{pull_request.get('number', 'unknown')}: {pull_request.get('title', '')}\\n\\n{pull_request.get('body', '')}",
                repository=repository.get("full_name"),
                branch=pull_request.get("head", {}).get("ref"),
                commit_sha=pull_request.get("head", {}).get("sha"),
                pr_number=pull_request.get("number"),
                user_id=pull_request.get("user", {}).get("login"),
                metadata={
                    "action": action,
                    "pr_url": pull_request.get("html_url"),
                    "repository_url": repository.get("html_url"),
                    "base_branch": pull_request.get("base", {}).get("ref"),
                    "head_branch": pull_request.get("head", {}).get("ref"),
                    "state": pull_request.get("state"),
                    "draft": pull_request.get("draft", False),
                    "mergeable": pull_request.get("mergeable"),
                    "changed_files": pull_request.get("changed_files", 0),
                    "additions": pull_request.get("additions", 0),
                    "deletions": pull_request.get("deletions", 0),
                }
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            self.logger.info(f"Processed PR event: {action} - Success: {result.success}")
            
        except Exception as e:
            self.logger.error(f"Error handling PR event: {str(e)}")
    
    async def _handle_push_event(self, payload: Dict[str, Any]):
        """Handle GitHub push events"""
        try:
            repository = payload.get("repository", {})
            commits = payload.get("commits", [])
            
            # Skip if no commits
            if not commits:
                return
            
            # Get branch name
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
            
            # Create commit summary
            commit_messages = [commit.get("message", "") for commit in commits]
            content = f"Push to {branch}\\n\\nCommits:\\n" + "\\n".join(f"- {msg}" for msg in commit_messages)
            
            # Create trigger context
            context = TriggerContext(
                trigger_type=TriggerType.PUSH,
                source="github_push",
                content=content,
                repository=repository.get("full_name"),
                branch=branch,
                commit_sha=payload.get("after"),
                user_id=payload.get("pusher", {}).get("name"),
                metadata={
                    "repository_url": repository.get("html_url"),
                    "compare_url": payload.get("compare"),
                    "commits_count": len(commits),
                    "forced": payload.get("forced", False),
                    "commits": commits,
                    "head_commit": payload.get("head_commit"),
                }
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            self.logger.info(f"Processed push event: {len(commits)} commits - Success: {result.success}")
            
        except Exception as e:
            self.logger.error(f"Error handling push event: {str(e)}")
    
    async def _handle_pr_review_event(self, payload: Dict[str, Any]):
        """Handle GitHub pull request review events"""
        try:
            action = payload.get("action")
            review = payload.get("review", {})
            pull_request = payload.get("pull_request", {})
            repository = payload.get("repository", {})
            
            # Only process submitted reviews
            if action != "submitted":
                return
            
            # Create trigger context
            context = TriggerContext(
                trigger_type=TriggerType.PULL_REQUEST,
                source=f"github_pr_review_{review.get('state', 'unknown')}",
                content=f"PR Review #{pull_request.get('number', 'unknown')}: {review.get('body', '')}",
                repository=repository.get("full_name"),
                branch=pull_request.get("head", {}).get("ref"),
                pr_number=pull_request.get("number"),
                user_id=review.get("user", {}).get("login"),
                metadata={
                    "action": action,
                    "review_state": review.get("state"),
                    "review_url": review.get("html_url"),
                    "pr_url": pull_request.get("html_url"),
                    "repository_url": repository.get("html_url"),
                }
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            self.logger.info(f"Processed PR review event: {review.get('state')} - Success: {result.success}")
            
        except Exception as e:
            self.logger.error(f"Error handling PR review event: {str(e)}")
    
    async def _handle_commit_comment_event(self, payload: Dict[str, Any]):
        """Handle GitHub commit comment events"""
        try:
            action = payload.get("action")
            comment = payload.get("comment", {})
            repository = payload.get("repository", {})
            
            # Only process created comments
            if action != "created":
                return
            
            # Create trigger context
            context = TriggerContext(
                trigger_type=TriggerType.COMMIT,
                source="github_commit_comment",
                content=f"Commit Comment: {comment.get('body', '')}",
                repository=repository.get("full_name"),
                commit_sha=comment.get("commit_id"),
                user_id=comment.get("user", {}).get("login"),
                metadata={
                    "action": action,
                    "comment_url": comment.get("html_url"),
                    "repository_url": repository.get("html_url"),
                    "commit_url": comment.get("html_url"),
                }
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            self.logger.info(f"Processed commit comment event - Success: {result.success}")
            
        except Exception as e:
            self.logger.error(f"Error handling commit comment event: {str(e)}")
    
    async def _handle_workflow_run_event(self, payload: Dict[str, Any]):
        """Handle GitHub workflow run events"""
        try:
            action = payload.get("action")
            workflow_run = payload.get("workflow_run", {})
            repository = payload.get("repository", {})
            
            # Only process completed workflows
            if action != "completed":
                return
            
            # Create trigger context
            context = TriggerContext(
                trigger_type=TriggerType.PUSH,  # Workflows are usually triggered by pushes
                source=f"github_workflow_{workflow_run.get('conclusion', 'unknown')}",
                content=f"Workflow '{workflow_run.get('name', 'unknown')}' {workflow_run.get('conclusion', 'unknown')}",
                repository=repository.get("full_name"),
                branch=workflow_run.get("head_branch"),
                commit_sha=workflow_run.get("head_sha"),
                user_id=workflow_run.get("actor", {}).get("login"),
                metadata={
                    "action": action,
                    "workflow_name": workflow_run.get("name"),
                    "workflow_id": workflow_run.get("id"),
                    "conclusion": workflow_run.get("conclusion"),
                    "workflow_url": workflow_run.get("html_url"),
                    "repository_url": repository.get("html_url"),
                    "run_number": workflow_run.get("run_number"),
                    "run_attempt": workflow_run.get("run_attempt"),
                }
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            self.logger.info(f"Processed workflow run event: {workflow_run.get('conclusion')} - Success: {result.success}")
            
        except Exception as e:
            self.logger.error(f"Error handling workflow run event: {str(e)}")
    
    async def process_manual_trigger(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a manual trigger (e.g., from CLI or API)"""
        try:
            # Create trigger context from manual input
            context = TriggerContext(
                trigger_type=TriggerType(trigger_data.get("trigger_type", "user_prompt")),
                source=trigger_data.get("source", "manual"),
                content=trigger_data.get("content", ""),
                repository=trigger_data.get("repository"),
                branch=trigger_data.get("branch"),
                commit_sha=trigger_data.get("commit_sha"),
                issue_number=trigger_data.get("issue_number"),
                pr_number=trigger_data.get("pr_number"),
                user_id=trigger_data.get("user_id"),
                metadata=trigger_data.get("metadata", {}),
            )
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            return {
                "success": result.success,
                "processing_time": result.total_processing_time,
                "selected_servers": result.routing_result.selected_servers,
                "response": result.final_response,
            }
            
        except Exception as e:
            self.logger.error(f"Error processing manual trigger: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def shutdown(self):
        """Shutdown the GitHub event handler"""
        self.logger.info("Shutting down GitHub Event Handler")
        
        try:
            # Stop event processing
            await self.stop_processing()
            
            # Clear event queue
            while not self._event_queue.empty():
                try:
                    self._event_queue.get_nowait()
                    self._event_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            self.logger.info("GitHub Event Handler shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during GitHub Event Handler shutdown: {str(e)}")
            raise