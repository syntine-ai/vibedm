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
                        recipient = {"id": sender_id}
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
            
            elif trigger_config.get("opening_message_enabled") and not opening_sent:
                open_msg = trigger_config.get("opening_message") or {}
                msg_text = open_msg.get("text") or "Hey there!"
                btn_text = open_msg.get("buttonText") or ""
                
                message_payload = {"text": msg_text}
                if btn_text:
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
                    
                    # Defensive override: sync action_type with config["type"] if mismatch exists
                    config_type = config.get("type")
                    if config_type == "ask_follow" and action_type != "tag_contact":
                        action_type = "tag_contact"
                    elif config_type == "lead_form":
                        field_type = config.get("field_type") or "email"
                        expected_action = "ask_for_email" if field_type == "email" else "ask_for_phone"
                        if action_type != expected_action:
                            action_type = expected_action
                    
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
                                
                            # Stubs for ask_for_email, ask_for_phone, tag_contact / ask_follow
                            default_prompts = {
                                "ask_for_email": "Please reply with your email address to continue...",
                                "ask_for_phone": "Please reply with your phone number to continue...",
                                "tag_contact": "To get access to the download link, please make sure you're following our account! Click follow, then reply with 'Done' to continue! 😊"
                            }
                            prompt_text = config.get("prompt") or config.get("message") or default_prompts.get(action_type, f"Stub prompt for {action_type}")
                            
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
                                # Check if we already have a pending trace entry for this step
                                existing_entry = next((s for s in step_trace if s.get("step_id") == str(step["id"])), None)
                                
                                # Perform Live Instagram API follow check
                                is_following = False
                                if not is_mock:
                                    try:
                                        res_follow = await client.get(
                                            f"https://graph.instagram.com/v25.0/{sender_id}",
                                            params={
                                                "fields": "is_user_follow_business",
                                                "access_token": token
                                            }
                                        )
                                        if res_follow.status_code == 200:
                                            is_following = bool(res_follow.json().get("is_user_follow_business", False))
                                    except Exception:
                                        is_following = False
                                else:
                                    is_following = True
                                    
                                if existing_entry:
                                    # Post-Check: We are resuming a paused follow-up step
                                    if is_following:
                                        # User has followed successfully! Mark step succeeded and advance.
                                        existing_entry["status"] = "succeeded"
                                        existing_entry["response"] = {"status": "verified", "reason": "Follow verified successfully via live API check"}
                                        existing_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
                                        continue  # Let the loop proceed to the next step!
                                    else:
                                        # User claimed they followed but API says they are not following.
                                        # Send a gentle warning message asking them to follow and try again.
                                        warning_text = "We checked, but you aren't following yet! Please make sure to follow us, then click 'Done' or reply 'Done' to continue! 😊"
                                        if not is_mock:
                                            recipient = {"id": sender_id}
                                            await client.post(
                                                "https://graph.instagram.com/v25.0/me/messages",
                                                params={"access_token": token},
                                                json={
                                                    "recipient": recipient,
                                                    "message": {"text": warning_text},
                                                }
                                            )
                                        # Pause sequential execution again
                                        final_status = "awaiting_interaction"
                                        break  # Pause and exit the steps execution loop
                                else:
                                    # First-time execution (Pre-Check):
                                    if is_following:
                                        # User is already following! Silently skip this step and advance directly.
                                        step_entry["status"] = "succeeded"
                                        step_entry["response"] = {"status": "skipped", "reason": "User already following (pre-check passed)"}
                                    else:
                                        # User is not following. Send the premium follow prompt and pause.
                                        if is_mock:
                                            step_entry["response"] = {"status": "pending", "reason": "Follow prompt sent (mock)"}
                                            step_entry["status"] = "pending"
                                        else:
                                            recipient = {"id": sender_id}
                                            username = await repo.get_workspace_username(run["workspace_id"])
                                            if username:
                                                follow_url = f"https://instagram.com/{username}"
                                                message_payload = {
                                                    "attachment": {
                                                        "type": "template",
                                                        "payload": {
                                                            "template_type": "button",
                                                            "text": prompt_text[:640],
                                                            "buttons": [
                                                                {
                                                                    "type": "web_url",
                                                                    "url": follow_url,
                                                                    "title": "Follow Us 👤"
                                                                },
                                                                {
                                                                    "type": "postback",
                                                                    "title": "Done! 👍",
                                                                    "payload": f"step_click_{step['id']}"
                                                                }
                                                            ]
                                                        }
                                                    }
                                                }
                                            else:
                                                message_payload = {
                                                    "text": prompt_text,
                                                    "quick_replies": [
                                                        {
                                                            "content_type": "text",
                                                            "title": "Done! 👍",
                                                            "payload": f"step_click_{step['id']}"
                                                        }
                                                    ]
                                                }
                                            res = await client.post(
                                                "https://graph.instagram.com/v25.0/me/messages",
                                                params={"access_token": token},
                                                json={
                                                    "recipient": recipient,
                                                    "message": message_payload,
                                                }
                                            )
                                            if res.status_code != 200:
                                                raise ValueError(f"Meta Follow Prompt API failed: {res.text}")
                                            step_entry["response"] = res.json()
                                            step_entry["status"] = "pending"
                                            
                                        final_status = "awaiting_interaction"
                                        step_trace.append(step_entry)
                                        break
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
                    
        # 7. Update the run record status and trace. Map 'awaiting_interaction' in-memory status
        # to the database-compatible 'succeeded' enum status to prevent database failures.
        db_status = "succeeded" if final_status == "awaiting_interaction" else final_status
        await repo.update_run(
            run_id=automation_run_id,
            status=db_status,
            step_trace=step_trace,
            error=final_error,
        )
        
        if final_status in {"succeeded", "awaiting_interaction"} and trigger_config.get("follow_up_enabled"):
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
