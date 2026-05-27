from __future__ import annotations

import httpx
from datetime import datetime, timezone
from uuid import UUID

from app.db import get_sessionmaker
from app.modules.automations.repositories.automations import AutomationRepository


async def run_automation(automation_run_id: UUID) -> dict[str, str]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        repo = AutomationRepository(session)
        
        # 1. Fetch the run record
        run = await repo.get_run(automation_run_id)
        if not run:
            return {"status": "failed", "error": f"Run {automation_run_id} not found"}
            
        # 2. Fetch the automation detail (including steps)
        automation = await repo.get_detail(
            workspace_id=run["workspace_id"],
            automation_id=run["automation_id"]
        )
        if not automation:
            await repo.update_run(
                run_id=automation_run_id,
                status="failed",
                step_trace=[],
                error="Automation not found",
            )
            return {"status": "failed", "error": "Automation not found"}
            
        # 3. Fetch the Page Access Token for this workspace
        token = await repo.get_workspace_token(run["workspace_id"])
        is_mock = not token or token.startswith("dev-token") or token == "dev"
        
        # 4. Extract sender ID and comment ID (if present) from trigger event
        trigger_event = run["trigger_event"] or {}
        
        # Determine sender_id (could be direct DM sender or comment sender)
        sender_id = str(
            trigger_event.get("sender", {}).get("id") or 
            trigger_event.get("sender_id") or 
            ""
        )
        comment_id = str(trigger_event.get("comment_id") or "")
        
        if not sender_id:
            await repo.update_run(
                run_id=automation_run_id,
                status="failed",
                step_trace=[],
                error="Recipient sender_id not found in trigger event",
            )
            return {"status": "failed", "error": "No sender_id"}

        step_trace = []
        final_status = "succeeded"
        final_error = None
        
        # 5. Execute steps sequentially
        steps = automation.get("steps") or []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for step in steps:
                action_type = step.get("action_type")
                config = step.get("config") or {}
                
                step_entry = {
                    "step_id": str(step["id"]),
                    "action_type": action_type,
                    "status": "queued",
                    "response": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                
                try:
                    if action_type == "send_dm":
                        message_text = config.get("message") or "Hello!"
                        if is_mock:
                            step_entry["response"] = {"message_id": f"mock-dm-{automation_run_id}"}
                            step_entry["status"] = "succeeded"
                        else:
                            # v25.0 Messages API call: if comment_id is present, send as a private reply to comment
                            recipient = {"comment_id": comment_id} if comment_id else {"id": sender_id}
                            res = await client.post(
                                "https://graph.instagram.com/v25.0/me/messages",
                                params={"access_token": token},
                                json={
                                    "recipient": recipient,
                                    "message": {"text": message_text},
                                }
                            )
                            if res.status_code != 200:
                                raise ValueError(f"Meta DM API failed: {res.text}")
                            step_entry["response"] = res.json()
                            step_entry["status"] = "succeeded"
                            
                    elif action_type == "send_comment_reply":
                        reply_text = config.get("message") or "Thanks!"
                        if not comment_id:
                            raise ValueError("Cannot reply to comment: comment_id missing from trigger event")
                            
                        if is_mock:
                            step_entry["response"] = {"id": f"mock-reply-{automation_run_id}"}
                            step_entry["status"] = "succeeded"
                        else:
                            # v25.0 Comment Reply API call
                            res = await client.post(
                                f"https://graph.instagram.com/v25.0/{comment_id}/replies",
                                params={"access_token": token},
                                json={"message": reply_text}
                            )
                            if res.status_code != 200:
                                raise ValueError(f"Meta Comment Reply API failed: {res.text}")
                            step_entry["response"] = res.json()
                            step_entry["status"] = "succeeded"
                            
                    else:
                        # Stub response for other action types (e.g. ask_for_email, ask_for_phone, tag_contact)
                        # Typically these also send a DM prompt, so let's mock/stub successfully
                        prompt_text = config.get("prompt") or config.get("message") or f"Stub prompt for {action_type}"
                        if action_type in {"ask_for_email", "ask_for_phone"}:
                            if is_mock:
                                step_entry["response"] = {"message_id": f"mock-prompt-{automation_run_id}"}
                                step_entry["status"] = "succeeded"
                            else:
                                recipient = {"comment_id": comment_id} if comment_id else {"id": sender_id}
                                res = await client.post(
                                    "https://graph.instagram.com/v25.0/me/messages",
                                    params={"access_token": token},
                                    json={
                                        "recipient": recipient,
                                        "message": {"text": prompt_text},
                                    }
                                )
                                if res.status_code != 200:
                                    raise ValueError(f"Meta DM Prompt API failed: {res.text}")
                                step_entry["response"] = res.json()
                                step_entry["status"] = "succeeded"
                        else:
                            step_entry["response"] = {"status": "skipped", "reason": "No-op stub"}
                            step_entry["status"] = "succeeded"
                            
                except Exception as e:
                    step_entry["status"] = "failed"
                    step_entry["response"] = {"error": str(e)}
                    final_status = "failed"
                    final_error = str(e)
                    step_trace.append(step_entry)
                    break
                    
                step_trace.append(step_entry)
                
        # 6. Update the run record status and trace
        await repo.update_run(
            run_id=automation_run_id,
            status=final_status,
            step_trace=step_trace,
            error=final_error,
        )
        
        return {"status": final_status, "error": final_error}
