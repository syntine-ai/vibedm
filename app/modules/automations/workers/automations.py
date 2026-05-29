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

        trigger_config = automation.get("trigger_config") or {}
        db_trace = run.get("step_trace") or []
        if isinstance(db_trace, str):
            import json
            try:
                db_trace = json.loads(db_trace)
            except Exception:
                db_trace = []
        elif not isinstance(db_trace, list):
            db_trace = []
            
        step_trace = list(db_trace)
        opening_sent = any(s.get("step_id") == "opening_message" and s.get("status") == "succeeded" for s in step_trace)
        
        final_status = "succeeded"
        final_error = None
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 5. Deliver Opening Message or Follow-up Message
            initial_payload = run.get("payload") or {}
            is_followup = bool(initial_payload.get("is_followup"))
            
            if is_followup:
                msg_text = trigger_config.get("follow_up_message") or "Hey! Just wanted to follow up and see if you had any questions."
                step_entry = {
                    "step_id": "followup_message",
                    "action_type": "send_dm",
                    "status": "queued",
                    "response": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    if is_mock:
                        step_entry["response"] = {"message_id": f"mock-followup-{automation_run_id}"}
                        step_entry["status"] = "succeeded"
                    else:
                        recipient = {"comment_id": comment_id} if comment_id else {"id": sender_id}
                        res = await client.post(
                            "https://graph.instagram.com/v25.0/me/messages",
                            params={"access_token": token},
                            json={
                                "recipient": recipient,
                                "message": {"text": msg_text},
                            }
                        )
                        if res.status_code != 200:
                            raise ValueError(f"Meta Follow-up DM API failed: {res.text}")
                        step_entry["response"] = res.json()
                        step_entry["status"] = "succeeded"
                except Exception as e:
                    step_entry["status"] = "failed"
                    step_entry["response"] = {"error": str(e)}
                    final_status = "failed"
                    final_error = f"Follow-up message failed: {str(e)}"
                    step_trace.append(step_entry)
                    
                step_trace.append(step_entry)
            
            elif trigger_config.get("opening_message_enabled") and not opening_sent:
                open_msg = trigger_config.get("opening_message") or {}
                msg_text = open_msg.get("text") or "Hey there!"
                btn_text = open_msg.get("buttonText") or ""
                
                # Check if this is a comment trigger reply. Private comment replies can ONLY be text-only!
                # If there's a comment_id, we strip out any buttons/quick replies to avoid Meta errors.
                # If there's no comment_id (e.g. triggered via DM directly), we can include the button as a quick reply.
                has_comment_recipient = bool(comment_id)
                
                message_payload = {"text": msg_text}
                if btn_text and not has_comment_recipient:
                    message_payload = {
                        "text": msg_text,
                        "quick_replies": [
                            {
                                "content_type": "text",
                                "title": btn_text[:20],
                                "payload": f"opening_click_{automation_run_id}"
                            }
                        ]
                    }
                
                step_entry = {
                    "step_id": "opening_message",
                    "action_type": "send_dm",
                    "status": "queued",
                    "response": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                
                try:
                    if is_mock:
                        step_entry["response"] = {"message_id": f"mock-opening-{automation_run_id}"}
                        step_entry["status"] = "succeeded"
                    else:
                        recipient = {"comment_id": comment_id} if comment_id else {"id": sender_id}
                        res = await client.post(
                            "https://graph.instagram.com/v25.0/me/messages",
                            params={"access_token": token},
                            json={
                                "recipient": recipient,
                                "message": message_payload,
                            }
                        )
                        if res.status_code != 200:
                            raise ValueError(f"Meta Opening DM API failed: {res.text}")
                        step_entry["response"] = res.json()
                        step_entry["status"] = "succeeded"
                        
                    # Stop flow here and wait for user reply/interaction!
                    final_status = "awaiting_interaction"
                    
                except Exception as e:
                    step_entry["status"] = "failed"
                    step_entry["response"] = {"error": str(e)}
                    final_status = "failed"
                    final_error = f"Opening message failed: {str(e)}"
                    
                step_trace.append(step_entry)

            # 6. Execute steps sequentially (skip if this is a follow-up or if opening message failed)
            if final_status == "succeeded" and not is_followup:
                steps = automation.get("steps") or []
                for step in steps:
                    action_type = step.get("action_type")
                    config = step.get("config") or {}
                    
                    # Skip if this step has already executed successfully in a previous run
                    if any(s.get("step_id") == str(step["id"]) and s.get("status") == "succeeded" for s in step_trace):
                        continue
                        
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
                            step_type = config.get("type") or "text"
                            
                            # Construct rich template layouts
                            if step_type == "card":
                                title = config.get("title") or "Card Message"
                                subtitle = config.get("subtitle") or ""
                                image_url = config.get("image_url") or ""
                                buttons = config.get("buttons") or []
                                
                                buttons_payload = []
                                for btn in buttons[:3]:
                                    btn_text = btn.get("text") or "Click"
                                    btn_act = btn.get("action_type") or "open_url"
                                    if btn_act == "open_url" and btn.get("url"):
                                        buttons_payload.append({
                                            "type": "web_url",
                                            "url": btn.get("url"),
                                            "title": btn_text[:20]
                                        })
                                    else:
                                        buttons_payload.append({
                                            "type": "postback",
                                            "title": btn_text[:20],
                                            "payload": f"step_click_{step['id']}"
                                        })
                                        
                                message_payload = {
                                    "attachment": {
                                        "type": "template",
                                        "payload": {
                                            "template_type": "generic",
                                            "elements": [{
                                                "title": title[:80],
                                                "subtitle": subtitle[:80],
                                                **({"image_url": image_url} if image_url else {}),
                                                **({"buttons": buttons_payload} if buttons_payload else {})
                                            }]
                                        }
                                    }
                                }
                            elif step_type == "image" and config.get("image_url"):
                                message_payload = {
                                    "attachment": {
                                        "type": "image",
                                        "payload": {
                                            "url": config.get("image_url")
                                        }
                                    }
                                }
                            elif step_type == "text" and config.get("buttons"):
                                buttons = config.get("buttons") or []
                                quick_replies = []
                                for btn in buttons[:3]:
                                    btn_text = btn.get("text") or "Click"
                                    quick_replies.append({
                                        "content_type": "text",
                                        "title": btn_text[:20],
                                        "payload": f"step_click_{step['id']}"
                                    })
                                message_payload = {
                                    "text": message_text,
                                    "quick_replies": quick_replies
                                }
                            else:
                                message_payload = {"text": message_text}

                            if is_mock:
                                step_entry["response"] = {"message_id": f"mock-dm-{automation_run_id}"}
                                step_entry["status"] = "succeeded"
                            else:
                                recipient = {"id": sender_id}
                                res = await client.post(
                                    "https://graph.instagram.com/v25.0/me/messages",
                                    params={"access_token": token},
                                    json={
                                        "recipient": recipient,
                                        "message": message_payload,
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
                            # Stubs for ask_for_email, ask_for_phone, tag_contact / ask_follow
                            prompt_text = config.get("prompt") or config.get("message") or f"Stub prompt for {action_type}"
                            if action_type in {"ask_for_email", "ask_for_phone"}:
                                if is_mock:
                                    step_entry["response"] = {"message_id": f"mock-prompt-{automation_run_id}"}
                                    step_entry["status"] = "succeeded"
                                else:
                                    recipient = {"id": sender_id}
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
                                    
                                # Pause the sequential execution and wait for user's lead submission!
                                final_status = "awaiting_interaction"
                            elif action_type == "tag_contact":
                                prompt_text = config.get("message") or "To get access to the download link, please make sure you're following our account! Click follow, then reply with 'Done' to continue! 😊"
                                if is_mock:
                                    step_entry["response"] = {"status": "succeeded", "reason": "Follow verified successfully"}
                                    step_entry["status"] = "succeeded"
                                else:
                                    recipient = {"id": sender_id}
                                    res = await client.post(
                                        "https://graph.instagram.com/v25.0/me/messages",
                                        params={"access_token": token},
                                        json={
                                            "recipient": recipient,
                                            "message": {"text": prompt_text},
                                        }
                                    )
                                    if res.status_code != 200:
                                        raise ValueError(f"Meta Follow Prompt API failed: {res.text}")
                                    step_entry["response"] = res.json()
                                    step_entry["status"] = "succeeded"
                                    
                                # Pause the sequential execution and wait for user's follow action!
                                final_status = "awaiting_interaction"
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
                    if final_status == "awaiting_interaction":
                        break
                    
        # 7. Update the run record status and trace
        await repo.update_run(
            run_id=automation_run_id,
            status=final_status,
            step_trace=step_trace,
            error=final_error,
        )
        
        # 8. Schedule deferred Follow-up Sequence (if initial run succeeded and follow-up is enabled)
        if final_status == "succeeded" and trigger_config.get("follow_up_enabled"):
            try:
                initial_payload = run.get("payload") or {}
                if not initial_payload.get("is_followup"):
                    from datetime import timedelta
                    from app.core.jobs import PostgresJobQueue, JobCreate
                    
                    delay_mins = trigger_config.get("follow_up_delay") or 10
                    run_at = datetime.now(timezone.utc) + timedelta(minutes=delay_mins)
                    
                    follow_up_run_id = await repo.create_automation_run(
                        workspace_id=run["workspace_id"],
                        automation_id=run["automation_id"],
                        contact_id=run.get("contact_id"),
                        trigger_event={
                            **(run.get("trigger_event") or {}),
                            "comment_id": comment_id,
                            "is_followup": True
                        }
                    )
                    
                    queue = PostgresJobQueue(session)
                    await queue.enqueue(
                        JobCreate(
                            job_type="automation.run",
                            workspace_id=run["workspace_id"],
                            payload={
                                "automation_run_id": str(follow_up_run_id),
                                "is_followup": True
                            },
                            run_at=run_at
                        )
                    )
            except Exception as sched_err:
                import logging
                logging.getLogger("app.worker").error(f"❌ Failed to schedule follow-up job: {sched_err}")
                
        return {"status": final_status, "error": final_error}
