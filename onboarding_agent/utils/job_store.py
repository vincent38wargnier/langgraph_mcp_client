from datetime import datetime
import logging
from typing import Dict, Any, Optional, List
from croniter import croniter

from app.crud.job import (
    get_or_create_notification_job,
    update_job,
    get_job_by_id,
    get_jobs_by_user_agent,
    get_active_jobs,
    get_jobs_by_recipient,
    get_jobs_by_type,
    delete_job,
    update_job_run_status,
    add_recipients,
    remove_recipients
)
from app.models.job import Job
from app.utils.magic_print import magic_print

logger = logging.getLogger(__name__)

class NotificationJobStore:
    def __init__(self, job: Optional[Job], user_id: str, agent_id: str, agent_config: Optional[Dict[str, Any]] = None):
        self.job = job
        self.user_id = user_id
        self.agent_id = agent_id
        self.agent_config = agent_config or {}

    @classmethod
    async def create(cls, user_id: str, agent_id: str, agent_config: Optional[Dict[str, Any]] = None):
        """Create a new NotificationJobStore instance."""
        return cls(None, user_id, agent_id, agent_config)

    def _validate_cron(self, cron_expression: str) -> bool:
        """Validate a cron expression."""
        try:
            croniter(cron_expression)
            return True
        except ValueError as e:
            magic_print(f"Invalid cron expression: {str(e)}", "red")
            return False

    def _calculate_next_run(self, cron_expression: str, is_one_time: bool = False) -> Optional[datetime]:
        """
        Calculate the next run time based on a cron expression.
        For one-time jobs, validates that the time hasn't passed.
        """
        try:
            magic_print("\n=== Calculating Next Run Time ===", "cyan")
            magic_print(f"Cron expression: {cron_expression}", "yellow")
            magic_print(f"Is one-time: {is_one_time}", "yellow")
            
            now = datetime.utcnow()
            cron = croniter(cron_expression, now)
            next_run = cron.get_next(datetime)
            
            magic_print(f"Current time (UTC): {now}", "yellow")
            magic_print(f"Next run (UTC): {next_run}", "yellow")
            magic_print(f"Time until execution: {(next_run - now).total_seconds() / 3600:.2f} hours", "yellow")
            
            if is_one_time:
                # For one-time jobs, simply check if the next run is in the future
                if next_run <= now:
                    magic_print("❌ Scheduled time has already passed", "red")
                    return None
                magic_print("✅ Scheduled time is in the future", "green")
            
            return next_run
            
        except Exception as e:
            magic_print(f"❌ Error calculating next run time: {e}", "red")
            return None

    async def schedule_notification(
        self,
        name: str,
        cron_expression: str,
        message_content: str,
        message_type: str,
        recipients: List[str],
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Schedule a new notification job or update an existing one."""
        try:
            # Validate cron expression
            if not self._validate_cron(cron_expression):
                return {"success": False, "message": "Invalid cron expression"}

            # Validate message type
            if message_type not in ["telegram"]:
                return {"success": False, "message": "Invalid message type"}

            # Check if this is a one-time job
            is_one_time = params and params.get("one_time", False)

            # Calculate next run time
            next_run = self._calculate_next_run(cron_expression, is_one_time)
            
            # For one-time jobs, if next_run is None, it means the scheduled time has passed
            if is_one_time and next_run is None:
                return {
                    "success": False,
                    "message": "Scheduled time has already passed"
                }

            # Create or update job
            job = await get_or_create_notification_job(
                name=name,
                cron_expression=cron_expression,
                message_content=message_content,
                message_type=message_type,
                recipients=recipients,
                user_id=self.user_id,
                agent_id=self.agent_id,
                params=params
            )

            # Update next run time
            await update_job(job, {"next_run": next_run})
            
            job_type = "one-time" if is_one_time else "recurring"
            magic_print(f"Scheduled {job_type} notification job '{name}' to run at {next_run}", "green")
            
            return {
                "success": True,
                "message": f"{job_type.title()} notification job scheduled successfully",
                "job_id": str(job.id),
                "next_run": next_run.isoformat(),
                "is_one_time": is_one_time
            }
        except Exception as e:
            magic_print(f"Error scheduling notification job: {str(e)}", "red")
            return {"success": False, "message": str(e)}

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by its ID."""
        try:
            job = await get_job_by_id(job_id)
            if job:
                magic_print(f"Retrieved notification job '{job.name}'", "yellow")
            return job
        except Exception as e:
            magic_print(f"Error getting job: {str(e)}", "red")
            return None

    async def list_jobs(self) -> List[Job]:
        """List all jobs for the current user and agent."""
        try:
            jobs = await get_jobs_by_user_agent(self.user_id, self.agent_id)
            magic_print(f"Retrieved {len(jobs)} notification jobs", "yellow")
            return jobs
        except Exception as e:
            magic_print(f"Error listing jobs: {str(e)}", "red")
            return []

    async def get_jobs_for_recipient(self, recipient_id: str) -> List[Job]:
        """Get all jobs targeting a specific recipient."""
        try:
            jobs = await get_jobs_by_recipient(recipient_id)
            magic_print(f"Retrieved {len(jobs)} jobs for recipient {recipient_id}", "yellow")
            return jobs
        except Exception as e:
            magic_print(f"Error getting jobs for recipient: {str(e)}", "red")
            return []

    async def get_jobs_by_type(self, message_type: str) -> List[Job]:
        """Get all jobs of a specific type."""
        try:
            jobs = await get_jobs_by_type(message_type)
            magic_print(f"Retrieved {len(jobs)} jobs of type {message_type}", "yellow")
            return jobs
        except Exception as e:
            magic_print(f"Error getting jobs by type: {str(e)}", "red")
            return []

    async def delete_job(self, job_id: str) -> Dict[str, Any]:
        """Delete a job."""
        try:
            job = await get_job_by_id(job_id)
            if not job:
                return {"success": False, "message": "Job not found"}

            if await delete_job(job):
                return {"success": True, "message": f"Job {job_id} deleted"}
            return {"success": False, "message": "Failed to delete job"}
        except Exception as e:
            magic_print(f"Error deleting job: {str(e)}", "red")
            return {"success": False, "message": str(e)}

    async def update_job_status(self, job_id: str, success: bool = True, error_message: Optional[str] = None) -> Dict[str, Any]:
        """Update a job's status after execution."""
        try:
            job = await get_job_by_id(job_id)
            if not job:
                return {"success": False, "message": "Job not found"}

            # Check if this is a one-time job
            is_one_time = job.params and job.params.get("one_time", False)

            # Update run status
            job = await update_job_run_status(job, success, error_message)

            updates = {}
            if is_one_time:
                # Deactivate one-time jobs after execution
                updates["is_active"] = False
                updates["next_run"] = None
                magic_print(f"Deactivating one-time job '{job.name}' after execution", "yellow")
            else:
                # Calculate next run for recurring jobs
                next_run = self._calculate_next_run(job.cron_expression)
                updates["next_run"] = next_run

            # Apply updates
            job = await update_job(job, updates)

            return {
                "success": True,
                "message": "Job status updated",
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "success_count": job.success_count,
                "failure_count": job.failure_count,
                "last_error": job.last_error,
                "is_active": job.is_active
            }
        except Exception as e:
            magic_print(f"Error updating job status: {str(e)}", "red")
            return {"success": False, "message": str(e)}

    async def add_recipients(self, job_id: str, recipient_ids: List[str]) -> Dict[str, Any]:
        """Add recipients to a job."""
        try:
            job = await get_job_by_id(job_id)
            if not job:
                return {"success": False, "message": "Job not found"}

            job = await add_recipients(job, recipient_ids)
            return {
                "success": True,
                "message": f"Added {len(recipient_ids)} recipients",
                "total_recipients": len(job.recipients)
            }
        except Exception as e:
            magic_print(f"Error adding recipients: {str(e)}", "red")
            return {"success": False, "message": str(e)}

    async def remove_recipients(self, job_id: str, recipient_ids: List[str]) -> Dict[str, Any]:
        """Remove recipients from a job."""
        try:
            job = await get_job_by_id(job_id)
            if not job:
                return {"success": False, "message": "Job not found"}

            job = await remove_recipients(job, recipient_ids)
            return {
                "success": True,
                "message": f"Removed {len(recipient_ids)} recipients",
                "total_recipients": len(job.recipients)
            }
        except Exception as e:
            magic_print(f"Error removing recipients: {str(e)}", "red")
            return {"success": False, "message": str(e)} 