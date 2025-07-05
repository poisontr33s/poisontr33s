"""
Trigger processor for handling various automation triggers
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import schedule
import time

from ..core.schemas import TriggerContext, TriggerType
from ..core.orchestrator import DynamicMCPOrchestrator
from ..utils.config import ConfigManager


class TriggerProcessor:
    """
    Processor for handling various types of automation triggers including
    scheduled tasks, webhook events, and manual triggers.
    """
    
    def __init__(self, orchestrator: DynamicMCPOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
        
        # Trigger queue and processing
        self._trigger_queue: asyncio.Queue = asyncio.Queue()
        self._processing_tasks: List[asyncio.Task] = []
        self._running = False
        
        # Scheduled jobs
        self._scheduled_jobs = []
        
    async def start(self):
        """Start the trigger processor"""
        if self._running:
            return
        
        self._running = True
        
        # Start processing tasks
        for i in range(3):  # 3 concurrent processors
            task = asyncio.create_task(self._process_triggers())
            self._processing_tasks.append(task)
        
        # Start scheduler task
        scheduler_task = asyncio.create_task(self._run_scheduler())
        self._processing_tasks.append(scheduler_task)
        
        self.logger.info("Trigger processor started")
    
    async def stop(self):
        """Stop the trigger processor"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel all processing tasks
        for task in self._processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
        
        self._processing_tasks.clear()
        self.logger.info("Trigger processor stopped")
    
    async def add_trigger(self, context: TriggerContext, priority: int = 5):
        """
        Add a trigger to the processing queue.
        
        Args:
            context: Trigger context
            priority: Priority level (1-10, higher is more important)
        """
        try:
            trigger_item = {
                "context": context,
                "priority": priority,
                "timestamp": datetime.now(),
            }
            
            await self._trigger_queue.put(trigger_item)
            self.logger.info(f"Added trigger: {context.trigger_type} (priority: {priority})")
            
        except Exception as e:
            self.logger.error(f"Error adding trigger: {str(e)}")
    
    async def _process_triggers(self):
        """Process triggers from the queue"""
        while self._running:
            try:
                # Get trigger from queue with timeout
                trigger_item = await asyncio.wait_for(
                    self._trigger_queue.get(), timeout=1.0
                )
                
                # Process the trigger
                await self._process_single_trigger(trigger_item)
                
                # Mark task as done
                self._trigger_queue.task_done()
                
            except asyncio.TimeoutError:
                # No triggers in queue, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing trigger: {str(e)}")
    
    async def _process_single_trigger(self, trigger_item: Dict[str, Any]):
        """Process a single trigger"""
        try:
            context = trigger_item["context"]
            priority = trigger_item["priority"]
            
            self.logger.info(f"Processing trigger: {context.trigger_type}")
            
            # Process through orchestrator
            result = await self.orchestrator.process_trigger(context)
            
            # Log result
            if result.success:
                self.logger.info(
                    f"Successfully processed {context.trigger_type} "
                    f"in {result.total_processing_time:.2f}s"
                )
            else:
                self.logger.warning(
                    f"Failed to process {context.trigger_type}: "
                    f"{result.routing_result.routing_reason}"
                )
            
            # Handle post-processing based on trigger type
            await self._handle_post_processing(context, result, priority)
            
        except Exception as e:
            self.logger.error(f"Error processing single trigger: {str(e)}")
    
    async def _handle_post_processing(self, context: TriggerContext, result: Any, priority: int):
        """Handle post-processing tasks after trigger execution"""
        try:
            # Save processing history
            await self._save_processing_history(context, result)
            
            # Handle high-priority failures
            if priority >= 8 and not result.success:
                await self._handle_high_priority_failure(context, result)
            
            # Update metrics
            await self._update_metrics(context, result)
            
        except Exception as e:
            self.logger.error(f"Error in post-processing: {str(e)}")
    
    async def _save_processing_history(self, context: TriggerContext, result: Any):
        """Save processing history for analytics"""
        try:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "trigger_type": context.trigger_type,
                "source": context.source,
                "repository": context.repository,
                "success": result.success,
                "processing_time": result.total_processing_time,
                "selected_servers": result.routing_result.selected_servers,
                "routing_reason": result.routing_result.routing_reason,
            }
            
            # In a real implementation, save to database or file
            self.logger.debug(f"Saved processing history: {history_entry}")
            
        except Exception as e:
            self.logger.error(f"Error saving processing history: {str(e)}")
    
    async def _handle_high_priority_failure(self, context: TriggerContext, result: Any):
        """Handle failures of high-priority triggers"""
        try:
            self.logger.error(
                f"High-priority trigger failed: {context.trigger_type} - {result.routing_result.routing_reason}"
            )
            
            # In a real implementation, you might:
            # - Send alerts
            # - Create GitHub issues
            # - Retry with different servers
            # - Escalate to human operators
            
        except Exception as e:
            self.logger.error(f"Error handling high-priority failure: {str(e)}")
    
    async def _update_metrics(self, context: TriggerContext, result: Any):
        """Update system metrics"""
        try:
            # In a real implementation, update metrics like:
            # - Success rates by trigger type
            # - Processing times
            # - Server utilization
            # - Error rates
            
            pass
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}")
    
    def schedule_periodic_trigger(self, 
                                 trigger_type: TriggerType,
                                 interval_minutes: int,
                                 content: str = "",
                                 metadata: Optional[Dict[str, Any]] = None):
        """
        Schedule a periodic trigger.
        
        Args:
            trigger_type: Type of trigger
            interval_minutes: Interval in minutes
            content: Trigger content
            metadata: Additional metadata
        """
        try:
            def create_scheduled_trigger():
                context = TriggerContext(
                    trigger_type=trigger_type,
                    source="scheduled",
                    content=content,
                    metadata=metadata or {},
                )
                
                # Add to queue asynchronously
                asyncio.create_task(self.add_trigger(context, priority=3))
            
            # Schedule the job
            schedule.every(interval_minutes).minutes.do(create_scheduled_trigger)
            self._scheduled_jobs.append(create_scheduled_trigger)
            
            self.logger.info(f"Scheduled periodic trigger: {trigger_type} every {interval_minutes} minutes")
            
        except Exception as e:
            self.logger.error(f"Error scheduling periodic trigger: {str(e)}")
    
    async def _run_scheduler(self):
        """Run the scheduled jobs"""
        while self._running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler: {str(e)}")
                await asyncio.sleep(60)
    
    async def process_webhook_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Process a webhook event.
        
        Args:
            event_type: Type of webhook event
            payload: Event payload
            
        Returns:
            True if processed successfully
        """
        try:
            # Create trigger context from webhook
            context = self._create_webhook_context(event_type, payload)
            
            # Add to processing queue with high priority
            await self.add_trigger(context, priority=7)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing webhook event: {str(e)}")
            return False
    
    def _create_webhook_context(self, event_type: str, payload: Dict[str, Any]) -> TriggerContext:
        """Create trigger context from webhook payload"""
        # This is a simplified implementation
        # In a real system, you'd parse different webhook formats
        
        return TriggerContext(
            trigger_type=TriggerType.WEBHOOK,
            source=f"webhook_{event_type}",
            content=json.dumps(payload, indent=2),
            metadata={
                "webhook_type": event_type,
                "payload": payload,
            }
        )
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_size": self._trigger_queue.qsize(),
            "running": self._running,
            "processing_tasks": len(self._processing_tasks),
            "scheduled_jobs": len(self._scheduled_jobs),
        }
    
    async def clear_queue(self):
        """Clear the trigger queue"""
        while not self._trigger_queue.empty():
            try:
                self._trigger_queue.get_nowait()
                self._trigger_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        self.logger.info("Trigger queue cleared")