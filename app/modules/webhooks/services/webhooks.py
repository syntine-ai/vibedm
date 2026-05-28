from __future__ import annotations

import json

from app.config import Settings
from app.core.errors import ApiError
from app.modules.webhooks.repositories.webhooks import WebhookRepository
from app.security import verify_hmac_hex, verify_stripe_signature


from uuid import UUID

class WebhookService:
    def __init__(self, repository: WebhookRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def handle_instagram(self, body: bytes, signature: str | None) -> dict[str, bool]:
        if self.settings.instagram_webhook_secret:
            if not signature:
                import logging
                logging.getLogger("app.webhooks").warning(
                    "Instagram webhook signature validation failed: X-Hub-Signature-256 header is missing!"
                )
                raise ApiError(
                    status_code=401, code="invalid_signature", message="Missing signature"
                )
            expected = signature.removeprefix("sha256=") if signature.startswith("sha256=") else signature
            if not verify_hmac_hex(body, expected, self.settings.instagram_webhook_secret):
                import logging
                import hmac
                from hashlib import sha256
                computed = hmac.new(self.settings.instagram_webhook_secret.encode("utf-8"), body, sha256).hexdigest()
                logging.getLogger("app.webhooks").warning(
                    f"Instagram webhook signature validation failed!\n"
                    f"  - Body length: {len(body)} bytes\n"
                    f"  - Signature in Header (X-Hub-Signature-256): '{signature}'\n"
                    f"  - Cleaned Header Signature: '{expected}'\n"
                    f"  - Computed Signature using Secret: '{computed}'\n"
                    f"  - Secret used: '{self.settings.instagram_webhook_secret[:4]}...{self.settings.instagram_webhook_secret[-4:]}' (len={len(self.settings.instagram_webhook_secret)})"
                )
                raise ApiError(
                    status_code=401, code="invalid_signature", message="Invalid signature"
                )
        payload = self._json_payload(body)
        
        # Extract a truly unique external_id to prevent deduplicating different messages/comments
        external_id = "unknown"
        entry = payload.get("entry", [{}])[0] if payload.get("entry") else {}
        
        # 1. Try to get DM message ID
        messagings = entry.get("messaging", [{}])
        if messagings and "message" in messagings[0]:
            external_id = messagings[0]["message"].get("mid") or "unknown"
        # 2. Try to get comment ID
        elif entry.get("changes"):
            change_val = entry["changes"][0].get("value", {})
            external_id = change_val.get("id") or "unknown"
            
        # Fallback to entry.id or payload.id if no message or comment ID is found
        if external_id == "unknown":
            external_id = str(payload.get("id") or entry.get("id") or "unknown")

        inserted = await self.repository.record_event("instagram", external_id, payload)
        if inserted:
            await self.process_instagram_event(payload)
        return {"received": True, "duplicate": not inserted}

    async def process_instagram_event(self, payload: dict) -> None:
        entries = payload.get("entry") or []
        for entry in entries:
            entry_id = str(entry.get("id") or "")
            
            # 1. Process DMs / Story replies
            messagings = entry.get("messaging") or []
            for msg_event in messagings:
                await self._process_messaging_event(entry_id, msg_event)
                
            # 2. Process Comments
            changes = entry.get("changes") or []
            for change in changes:
                field = change.get("field")
                if field == "comments":
                    await self._process_comment_event(entry_id, change.get("value") or {})

    async def _process_messaging_event(self, entry_id: str, msg_event: dict) -> None:
        sender_id = str(msg_event.get("sender", {}).get("id") or "")
        recipient_id = str(msg_event.get("recipient", {}).get("id") or "")
        
        ig_user_id = recipient_id or entry_id
        if not ig_user_id or not sender_id:
            return
            
        if sender_id == ig_user_id:
            return

        workspace_id = await self.repository.find_workspace_by_ig_user(ig_user_id)
        if not workspace_id:
            return

        message = msg_event.get("message") or {}
        postback = msg_event.get("postback") or {}
        
        text_content = ""
        is_story_reply = "reply_to" in message or "story" in message
        
        if postback:
            text_content = str(postback.get("payload") or "")
        elif message:
            text_content = str(message.get("text") or "")
            
        if not text_content:
            return

        # Automatic Lead Parsing Scanner
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_content)
        phone_match = re.search(r'(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}', text_content)
        if email_match or phone_match:
            email = email_match.group(0) if email_match else None
            phone = phone_match.group(0) if phone_match else None
            await self.repository.update_contact_leads(
                workspace_id=workspace_id,
                ig_user_id=sender_id,
                email=email,
                phone=phone,
            )

        active_automations = await self.repository.list_active_automations(workspace_id)
        for auto in active_automations:
            trigger_type = auto.get("trigger_type")
            trigger_config = auto.get("trigger_config") or {}
            
            if trigger_type == "dm" and not is_story_reply:
                keywords = trigger_config.get("keywords") or []
                match_mode = trigger_config.get("match") or "any"
                any_kw = trigger_config.get("any_keyword", False) or (not keywords and trigger_config.get("any_keyword") is None)
                if self._check_keywords(text_content, keywords, match_mode, any_kw):
                    await self._trigger_run(workspace_id, auto["id"], sender_id, None, text_content, msg_event)
            elif trigger_type == "story_reply" and is_story_reply:
                keywords = trigger_config.get("keywords") or []
                match_mode = trigger_config.get("match") or "any"
                any_kw = trigger_config.get("any_keyword", False) or (not keywords and trigger_config.get("any_keyword") is None)
                if self._check_keywords(text_content, keywords, match_mode, any_kw):
                    await self._trigger_run(workspace_id, auto["id"], sender_id, None, text_content, msg_event)

    async def _process_comment_event(self, entry_id: str, value: dict) -> None:
        comment_id = str(value.get("id") or "")
        comment_text = str(value.get("text") or "")
        media_id = str(value.get("media", {}).get("id") or "")
        sender = value.get("from") or {}
        sender_id = str(sender.get("id") or "")
        sender_username = str(sender.get("username") or "")
        
        if not comment_id or not comment_text or not sender_id:
            return
            
        ig_user_id = entry_id
        workspace_id = await self.repository.find_workspace_by_ig_user(ig_user_id)
        if not workspace_id:
            return

        active_automations = await self.repository.list_active_automations(workspace_id)
        for auto in active_automations:
            trigger_type = auto.get("trigger_type")
            trigger_config = auto.get("trigger_config") or {}
            
            if trigger_type == "comment_post":
                conf_post_id = trigger_config.get("post_id")
                if conf_post_id and str(conf_post_id) != media_id:
                    continue
                    
                keywords = trigger_config.get("keywords") or []
                match_mode = trigger_config.get("match") or "any"
                any_kw = trigger_config.get("any_keyword", False) or (not keywords and trigger_config.get("any_keyword") is None)
                if self._check_keywords(comment_text, keywords, match_mode, any_kw):
                    await self._trigger_run(
                        workspace_id=workspace_id,
                        automation_id=auto["id"],
                        sender_id=sender_id,
                        sender_username=sender_username,
                        text_content=comment_text,
                        raw_event={
                            "comment_id": comment_id,
                            "comment_text": comment_text,
                            "media_id": media_id,
                            "sender_id": sender_id,
                            "sender_username": sender_username,
                        },
                    )

    def _check_keywords(self, text: str, keywords: list[str], match_mode: str, any_keyword: bool = False) -> bool:
        if any_keyword:
            return True
        if not keywords:
            return False
        text_lower = text.lower().strip()
        if match_mode == "all":
            return all(k.lower().strip() in text_lower for k in keywords)
        else:
            return any(k.lower().strip() in text_lower for k in keywords)

    async def _trigger_run(
        self,
        workspace_id: UUID,
        automation_id: UUID,
        sender_id: str,
        sender_username: str | None,
        text_content: str,
        raw_event: dict,
    ) -> None:
        contact_id = await self.repository.upsert_contact(
            workspace_id=workspace_id,
            ig_user_id=sender_id,
            ig_username=sender_username,
            source_automation_id=automation_id,
        )
        run_id = await self.repository.create_automation_run(
            workspace_id=workspace_id,
            automation_id=automation_id,
            contact_id=contact_id,
            trigger_event=raw_event,
        )
        await self.repository.enqueue_automation_job(
            workspace_id=workspace_id,
            automation_run_id=run_id,
        )

    async def handle_stripe(self, body: bytes, signature: str | None) -> dict[str, bool]:
        if not signature or not verify_stripe_signature(
            body, signature, self.settings.stripe_webhook_secret
        ):
            raise ApiError(status_code=401, code="invalid_signature", message="Invalid signature")
        payload = self._json_payload(body)
        external_id = str(payload.get("id") or "unknown")
        inserted = await self.repository.record_event("stripe", external_id, payload)
        return {"received": True, "duplicate": not inserted}

    async def handle_razorpay(self, body: bytes, signature: str | None) -> dict[str, bool]:
        if not signature or not verify_hmac_hex(
            body, signature, self.settings.razorpay_webhook_secret
        ):
            raise ApiError(status_code=401, code="invalid_signature", message="Invalid signature")
        payload = self._json_payload(body)
        external_id = str(payload.get("event") or payload.get("id") or "unknown")
        inserted = await self.repository.record_event("razorpay", external_id, payload)
        return {"received": True, "duplicate": not inserted}

    @staticmethod
    def _json_payload(body: bytes) -> dict:
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ApiError(
                status_code=400, code="invalid_json", message="Invalid JSON body"
            ) from exc
        if not isinstance(payload, dict):
            raise ApiError(
                status_code=400, code="invalid_json", message="JSON body must be an object"
            )
        return payload
