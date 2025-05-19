"""
Automatic follow-up management system for coaching agents.
Ensures conversations have appropriate follow-ups following these rules:
1. No automatic short-term follow-ups (only agent-created short-term allowed)
2. Only one long-term follow-up per conversation (24h+)
3. Non-automatic jobs always take priority over automatic ones
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.utils.magic_print import magic_print
from app.models.conversation import Conversation
from app.models.job import JobType
from app.agents.coach.utils.job_store import NotificationJobStore
from app.crud.job import update_job
from app.utils.message_formatting import format_message_history_for_gpt4o, analyze_followup_status

# Configuration for follow-ups
FOLLOW_UP_CONFIG = {
    "long_term": {
        "delay": timedelta(hours=24),
        "keywords": ["long-term", "24 hours"],
        "message": (
            "Automatic follow-up: It's been 24 hours with no response. "
            "Remind the user of their progress and invite them to continue their coaching journey."
        ),
    },
    "extended_long_term": {
        "delay": timedelta(days=3),
        "keywords": ["extended-long-term", "3 days"],
        "message": (
            "Automatic follow-up: It's been 3 days with no response. "
            "Remind the user of their progress and invite them to continue their coaching journey."
        ),
    },
}
SHORT_TERM_THRESHOLD = 6 * 3600  # seconds

async def update_auto_jobs(
    structured_jobs: List[Dict[str, Any]],
    user_id: str,
    agent_id: str,
    conversation_id: str,
    user_timezone: str,
    messages=None,
) -> Dict[str, Any]:
    """
    Manage follow-up jobs for a conversation based on simplified rules:
    1. ONLY long-term automatic follow-ups (24h+) are allowed
    2. Non-automatic jobs always take priority over automatic ones
    3. Only one long-term job at a time (the longest one wins)
    4. Only non-automatic short-term jobs are allowed
    """
    magic_print("\n" + "🔄" * 25, "blue")
    magic_print("🔄 Managing follow-ups - SIMPLIFIED RULES", "blue")
    magic_print("🔄" * 25, "blue")

    try:
        # Initialize job store and conversation
        job_store = await NotificationJobStore.create(user_id=user_id, agent_id=agent_id)
        conversation = Conversation.objects(id=conversation_id).first()
        if not conversation:
            magic_print(f"Conversation {conversation_id} not found", "red")
            return {"success": False, "message": "Conversation not found"}

        # Check follow-up status if messages are provided
        was_last_followup_long_term = False
        
        if messages:
            formatted_history, structured_messages = format_message_history_for_gpt4o(messages, user_timezone)
            followup_status = analyze_followup_status(structured_messages)
            
            magic_print(f"Follow-up status analysis:", "cyan")
            magic_print(f"Last message is from user: {followup_status.get('last_message_is_user', False)}", "cyan")
            magic_print(f"Last messages are follow-up sequence: {followup_status.get('last_messages_are_followup', False)}", "cyan")
            
            # Determine if the last follow-up was long-term
            if followup_status.get('last_messages_are_followup', False) and len(structured_messages) >= 2:
                second_last_msg = structured_messages[-2]  # The system message
                was_last_followup_long_term = second_last_msg.get("is_long_term", False)
                magic_print(f"Last follow-up was long-term: {was_last_followup_long_term}", "cyan")
        
        # Split jobs into automatic and non-automatic
        auto_jobs = [j for j in structured_jobs if j.get("is_automatic")]
        user_jobs = [j for j in structured_jobs if not j.get("is_automatic")]
        
        magic_print(f"Found {len(auto_jobs)} automatic and {len(user_jobs)} user-created jobs", "cyan")

        # Classify jobs as short-term or long-term
        def classify(jobs):
            short, long = [], []
            for j in jobs:
                tr = j.get("time_remaining_seconds", 0)
                (short if tr <= SHORT_TERM_THRESHOLD else long).append(j)
            return short, long

        # Split jobs by time remaining
        agent_short, agent_long = classify(user_jobs)
        auto_short, auto_long = classify(auto_jobs)
        
        magic_print(f"User jobs: {len(agent_short)} short-term, {len(agent_long)} long-term", "cyan")
        magic_print(f"Auto jobs: {len(auto_short)} short-term, {len(auto_long)} long-term", "cyan")

        # RULE: Delete any automatic short-term jobs (not allowed)
        for j in auto_short:
            magic_print(f"Deleting automatic short-term job {j['id']} (no longer allowed by policy)", "yellow")
            await job_store.delete_job(j["id"])
        
        # RULE: Process long-term jobs - only keep one (priority: agent-created, then longest)
        long_term_job = None
        
        # RULE: Agent-created long-term jobs take priority over automatic ones
        if agent_long:
            # If multiple agent-created long jobs, keep the one with longest time remaining
            if len(agent_long) > 1:
                agent_long.sort(key=lambda j: j.get("time_remaining_seconds", 0), reverse=True)
                for j in agent_long[1:]:
                    magic_print(f"Deleting redundant agent long-term job {j['id']} (keeping only the longest)", "yellow")
                    await job_store.delete_job(j["id"])
            
            # Keep the best agent-created long job
            long_term_job = agent_long[0]
            
            # Delete all automatic long jobs since an agent job exists
            for j in auto_long:
                magic_print(f"Deleting automatic long-term job {j['id']} (agent job takes priority)", "yellow")
                await job_store.delete_job(j["id"])
        
        # RULE: If no agent-created long job, process automatic long jobs
        elif auto_long:
            # If multiple automatic long jobs, keep the one with longest time remaining
            if len(auto_long) > 1:
                auto_long.sort(key=lambda j: j.get("time_remaining_seconds", 0), reverse=True)
                for j in auto_long[1:]:
                    magic_print(f"Deleting redundant automatic long-term job {j['id']} (keeping only the longest)", "yellow")
                    await job_store.delete_job(j["id"])
            
            # Keep the best automatic long job
            long_term_job = auto_long[0]
        
        # RULE: If no long-term job exists and we need one, create automatic long-term
        if not long_term_job and not was_last_followup_long_term:
            # Create a new long-term follow-up
            now = datetime.now(ZoneInfo("UTC"))
            next_run = now + FOLLOW_UP_CONFIG['long_term']["delay"]
            cron = f"{next_run.minute} {next_run.hour} {next_run.day} {next_run.month} *"
            
            name = f"auto_long_term_{now.strftime('%Y%m%d_%H%M%S')}"
            job_result = await job_store.schedule_notification(
                name=name,
                cron_expression=cron,
                message_content=FOLLOW_UP_CONFIG['long_term']["message"],
                message_type="telegram",
                recipients=[user_id],
                params={
                    "one_time": True,
                    "original_time": f"+{int(FOLLOW_UP_CONFIG['long_term']['delay'].total_seconds()/3600)}h",
                    "original_timezone": user_timezone,
                    "scheduled_date": next_run.date().isoformat(),
                    "next_run": next_run.isoformat(),
                },
                job_type=JobType.AGENT_FOLLOW_UP,
                conversation=conversation,
            )
            
            if job_result.get("success"):
                await update_job(
                    await job_store.get_job(job_result["job_id"]),
                    {"automatic": True},
                )
                magic_print(f"✅ Created automatic long-term job: {job_result['job_id']}", "green")
                long_term_job = {"id": job_result["job_id"], "is_automatic": True}
            else:
                magic_print(f"❌ Failed to create long-term job: {job_result.get('message')}", "red")
        
        # RULE: If the last follow-up was long-term, replace with an extended one
        elif long_term_job and was_last_followup_long_term and long_term_job.get("is_automatic"):
            magic_print("Last follow-up was long-term, replacing with an extended 3-day follow-up", "yellow")
            
            # Delete existing long-term job
            await job_store.delete_job(long_term_job["id"])
            
            # Create extended long-term follow-up (3 days)
            now = datetime.now(ZoneInfo("UTC"))
            next_run = now + FOLLOW_UP_CONFIG['extended_long_term']["delay"]
            cron = f"{next_run.minute} {next_run.hour} {next_run.day} {next_run.month} *"
            
            name = f"auto_extended_long_term_{now.strftime('%Y%m%d_%H%M%S')}"
            job_result = await job_store.schedule_notification(
                name=name,
                cron_expression=cron,
                message_content=FOLLOW_UP_CONFIG['extended_long_term']["message"],
                message_type="telegram",
                recipients=[user_id],
                params={
                    "one_time": True,
                    "original_time": f"+{int(FOLLOW_UP_CONFIG['extended_long_term']['delay'].total_seconds()/3600)}h",
                    "original_timezone": user_timezone,
                    "scheduled_date": next_run.date().isoformat(),
                    "next_run": next_run.isoformat(),
                },
                job_type=JobType.AGENT_FOLLOW_UP,
                conversation=conversation,
            )
            
            if job_result.get("success"):
                await update_job(
                    await job_store.get_job(job_result["job_id"]),
                    {"automatic": True},
                )
                magic_print(f"✅ Created extended long-term job: {job_result['job_id']}", "green")
                long_term_job = {"id": job_result["job_id"], "is_automatic": True}
            else:
                magic_print(f"❌ Failed to create extended long-term job: {job_result.get('message')}", "red")
        
        # Display summary
        magic_print("\n📋 FOLLOW-UP SUMMARY:", "green")
        
        # Summary for short-term jobs
        if agent_short:
            magic_print(f"✅ User-created short-term jobs: {len(agent_short)}", "green")
            for job in agent_short:
                magic_print(f"  - {job['id']}", "green")
        else:
            magic_print("ℹ️ No short-term jobs (automatic short-term jobs not allowed)", "yellow")
        
        # Summary for long-term job
        if long_term_job:
            job_type = "agent-created" if not long_term_job.get("is_automatic") else "automatic"
            magic_print(f"✅ Active long-term job: {long_term_job['id']} ({job_type})", "green")
        else:
            magic_print("❌ No long-term job available", "yellow")
                
        magic_print("✅ Follow-ups managed successfully according to simplified rules", "green")
        magic_print("🔄" * 25 + "\n", "blue")

        return {
            "success": True, 
            "message": "Follow-ups managed successfully",
            "results": {
                "short_term": {"agent_jobs": agent_short},
                "long_term": long_term_job
            }
        }
        
    except Exception as e:
        magic_print(f"❌ Error managing follow-ups: {e}", "red")
        import traceback
        magic_print(traceback.format_exc(), "yellow")
        magic_print("🔄" * 25 + "\n", "blue")
        
        return {
            "success": False,
            "message": f"Error managing follow-ups: {str(e)}"
        } 