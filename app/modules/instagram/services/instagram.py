from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlencode
from uuid import UUID
import httpx

from app.config import Settings
from app.core.errors import ApiError
from app.deps import CurrentUser, WorkspaceContext
from app.modules.instagram.repositories.instagram import InstagramRepository
from app.modules.instagram.schemas.instagram import (
    InstagramProfile,
    InstagramWorkspaceResponse,
    OAuthStartResponse,
)
from app.security import sign_state, verify_state

# Instagram Business Login scopes (shows Instagram login screen, not Facebook)
INSTAGRAM_SCOPES = [
    "instagram_business_basic",
    "instagram_business_manage_messages",
    "instagram_business_manage_comments",
    "instagram_business_content_publish",
    "instagram_business_manage_insights",
]


class InstagramOAuthProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def exchange_code(
        self,
        code: str,
        ig_user_id: str | None = None,
        redirect_uri: str | None = None,
        connection_type: str = "instagram_direct",
    ) -> InstagramProfile:
        if (
            not self.settings.instagram_app_id
            or self.settings.instagram_app_id == "dev"
            or not self.settings.instagram_app_secret
            or self.settings.instagram_app_secret == "dev"
        ):
            # Fallback to dev profile in mock mode
            return InstagramProfile(
                ig_user_id=f"dev-{code}",
                ig_username="connected.account",
                access_token=f"dev-token-{code}",
                scopes=INSTAGRAM_SCOPES,
            )

        # 1. Configuration-based flow (Facebook Login for Business)
        if connection_type == "facebook_business" and self.settings.instagram_config_id and self.settings.instagram_config_id != "dev":
            client_id = self.settings.meta_app_id or self.settings.instagram_app_id
            client_secret = self.settings.meta_app_secret or self.settings.instagram_app_secret
            exchange_redirect_uri = redirect_uri or self.settings.instagram_redirect_uri
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Step 1: Exchange code for facebook user access token
                token_res = await client.get(
                    "https://graph.facebook.com/v25.0/oauth/access_token",
                    params={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": exchange_redirect_uri,
                        "code": code,
                    },
                )
                if token_res.status_code != 200:
                    raise ApiError(
                        status_code=400,
                        code="ig_oauth_failed",
                        message=f"Failed to exchange Facebook OAuth code: {token_res.text}",
                    )
                token_data = token_res.json()
                user_access_token = token_data.get("access_token")
                if not user_access_token:
                    raise ApiError(
                        status_code=400,
                        code="ig_oauth_failed",
                        message="Facebook OAuth exchange did not return access_token",
                    )

                # Step 2: Query user's connected Facebook Pages and linked Instagram accounts
                accounts_res = await client.get(
                    "https://graph.facebook.com/v25.0/me/accounts",
                    params={
                        "fields": "name,access_token,instagram_business_account",
                        "access_token": user_access_token,
                    },
                )
                if accounts_res.status_code != 200:
                    raise ApiError(
                        status_code=400,
                        code="ig_oauth_failed",
                        message=f"Failed to fetch connected Facebook Pages: {accounts_res.text}",
                    )
                accounts_data = accounts_res.json().get("data", [])
                
                # Identify all Pages with linked Instagram Business Accounts
                valid_accounts = []
                for page in accounts_data:
                    ig_account = page.get("instagram_business_account")
                    if ig_account and ig_account.get("id"):
                        valid_accounts.append({
                            "ig_user_id": str(ig_account["id"]),
                            "page_token": page.get("access_token"),
                            "ig_username": page.get("name") or "instagram_business"
                        })

                if not valid_accounts:
                    raise ApiError(
                        status_code=400,
                        code="ig_onboarding_failed",
                        message=(
                            "No connected Instagram Business/Creator account was found on your Facebook Pages. "
                            "Please ensure your Instagram account is linked to your Facebook Page in Settings."
                        ),
                    )

                # Resolve Instagram usernames for each detected account
                for acc in valid_accounts:
                    try:
                        profile_res = await client.get(
                            f"https://graph.facebook.com/v25.0/{acc['ig_user_id']}",
                            params={
                                "fields": "id,username,name",
                                "access_token": acc["page_token"],
                            },
                        )
                        if profile_res.status_code == 200:
                            p_data = profile_res.json()
                            acc["ig_username"] = p_data.get("username") or p_data.get("name") or acc["ig_username"]
                    except Exception:
                        pass

                # Handle multi-account selection logic
                selected_account = None
                if ig_user_id:
                    # Find the specific account the user selected
                    selected_account = next((a for a in valid_accounts if a["ig_user_id"] == ig_user_id), None)
                    if not selected_account:
                        raise ApiError(
                            status_code=400,
                            code="invalid_selection",
                            message="The selected Instagram account was not found among your authorized Facebook Pages.",
                        )
                else:
                    # If no selection is made yet:
                    if len(valid_accounts) == 1:
                        selected_account = valid_accounts[0]
                    else:
                        # Multiple accounts found! Raise selection required error
                        serialized_accounts = [
                            {"ig_user_id": a["ig_user_id"], "ig_username": a["ig_username"]}
                            for a in valid_accounts
                        ]
                        raise ApiError(
                            status_code=400,
                            code="requires_selection",
                            message="Multiple Instagram accounts found. Selection required.",
                            details={"accounts": serialized_accounts}
                        )

                # Fetch full profile details for the selected account
                ig_user_id = selected_account["ig_user_id"]
                page_token = selected_account["page_token"]
                ig_username = selected_account["ig_username"]

                return InstagramProfile(
                    ig_user_id=ig_user_id,
                    ig_username=ig_username,
                    access_token=page_token,  # We store the Page Access Token for worker automations
                    scopes=token_data.get("scopes", INSTAGRAM_SCOPES),
                )

        # 2. Legacy direct Instagram Login flow
        exchange_redirect_uri = redirect_uri or self.settings.instagram_redirect_uri
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Exchange code for short-lived token via Instagram Business Login
            token_res = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": self.settings.instagram_app_id,
                    "client_secret": self.settings.instagram_app_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": exchange_redirect_uri,
                    "code": code,
                },
            )
            if token_res.status_code != 200:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message=f"Failed to exchange OAuth code: {token_res.text}",
                )
            token_data = token_res.json()
            short_lived_token = token_data.get("access_token")
            ig_user_id = str(token_data.get("user_id", ""))

            if not short_lived_token or not ig_user_id:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message="OAuth response did not return access_token or user_id",
                )

            # Step 2: Exchange for long-lived token (60-day)
            long_token_res = await client.get(
                "https://graph.instagram.com/access_token",
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": self.settings.instagram_app_secret,
                    "access_token": short_lived_token,
                },
            )
            if long_token_res.status_code != 200:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message=f"Failed to get long-lived token: {long_token_res.text}",
                )
            long_lived_token = long_token_res.json().get("access_token", short_lived_token)

            # Step 3: Fetch Instagram Business profile (username, name)
            profile_res = await client.get(
                f"https://graph.instagram.com/v25.0/{ig_user_id}",
                params={
                    "fields": "id,username,name,profile_picture_url",
                    "access_token": long_lived_token,
                },
            )
            if profile_res.status_code != 200:
                raise ApiError(
                    status_code=400,
                    code="ig_oauth_failed",
                    message=f"Failed to fetch Instagram profile: {profile_res.text}",
                )
            profile_data = profile_res.json()
            ig_username = profile_data.get("username") or profile_data.get("name", "ig_user")

            return InstagramProfile(
                ig_user_id=ig_user_id,
                ig_username=ig_username,
                access_token=long_lived_token,
                scopes=INSTAGRAM_SCOPES,
            )


class InstagramService:
    def __init__(
        self,
        repository: InstagramRepository,
        settings: Settings,
        provider: InstagramOAuthProvider | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.provider = provider or InstagramOAuthProvider(settings)

    async def start_oauth(self, user: CurrentUser, flow: str | None = None) -> OAuthStartResponse:
        active_secret = (
            self.settings.meta_app_secret 
            if (self.settings.instagram_config_id and self.settings.instagram_config_id != "dev" and flow != "legacy")
            else self.settings.instagram_app_secret
        ) or "dev"
        connection_type = (
            "facebook_business"
            if (self.settings.instagram_config_id and self.settings.instagram_config_id != "dev" and flow != "legacy")
            else "instagram_direct"
        )
        state = sign_state({"user_id": str(user.id), "connection_type": connection_type}, active_secret)
        
        # If config_id is provided, utilize Meta's modern Facebook Login for Business dialog
        if self.settings.instagram_config_id and self.settings.instagram_config_id != "dev" and flow != "legacy":
            client_id = self.settings.meta_app_id or self.settings.instagram_app_id
            params = urlencode(
                {
                    "client_id": client_id,
                    "redirect_uri": self.settings.instagram_redirect_uri,
                    "config_id": self.settings.instagram_config_id,
                    "state": state,
                    "response_type": "code",
                    "force_reauth": "true",
                }
            )
            oauth_url = f"https://www.facebook.com/v25.0/dialog/oauth?{params}"
        else:
            # Legacy direct Instagram Login flow
            params = urlencode(
                {
                    "client_id": self.settings.instagram_app_id or "dev-instagram-app",
                    "redirect_uri": self.settings.instagram_redirect_uri,
                    "response_type": "code",
                    "scope": ",".join(INSTAGRAM_SCOPES),
                    "state": state,
                    "force_reauth": "true",
                }
            )
            oauth_url = f"https://www.instagram.com/oauth/authorize?{params}"
            
        return OAuthStartResponse(url=oauth_url, state=state)

    async def _activate_workspace(self, user_id: UUID, workspace_id: UUID) -> None:
        from sqlalchemy import text
        await self.repository.session.execute(
            text("update public.workspace_members set active = false where user_id = :user_id"),
            {"user_id": user_id},
        )
        await self.repository.session.execute(
            text(
                """
                update public.workspace_members set active = true
                where user_id = :user_id and workspace_id = :workspace_id
                """
            ),
            {"user_id": user_id, "workspace_id": workspace_id},
        )
        await self.repository.session.commit()

    async def complete_oauth(
        self, user: CurrentUser, code: str, state: str, workspace_id: UUID | None = None, ig_user_id: str | None = None, redirect_uri: str | None = None
    ) -> InstagramWorkspaceResponse:
        payload = None
        for secret in [self.settings.meta_app_secret, self.settings.instagram_app_secret, "dev"]:
            if not secret:
                continue
            try:
                payload = verify_state(state, secret)
                break
            except Exception:
                continue
        
        if not payload:
            raise ApiError(
                status_code=400, code="invalid_state", message="OAuth state signature verification failed"
            )

        if payload.get("user_id") != str(user.id):
            raise ApiError(
                status_code=400, code="invalid_state", message="OAuth state user mismatch"
            )

        connection_type = payload.get("connection_type", "instagram_direct")
        profile = await self.provider.exchange_code(
            code, ig_user_id=ig_user_id, redirect_uri=redirect_uri, connection_type=connection_type
        )

        if workspace_id is not None:
            workspace_detail = await self.repository.get_workspace_detail(workspace_id)
            if workspace_detail is None:
                raise ApiError(
                    status_code=404,
                    code="workspace_not_found",
                    message="Workspace not found",
                )

            # Clear any connection on the target workspace, and delete duplicate connection for this IG account elsewhere
            await self.repository.disconnect(workspace_id)
            await self.repository.delete_connection_by_ig_user(profile.ig_user_id)

            await self.repository.create_connection_for_workspace(
                workspace_id=workspace_id,
                ig_user_id=profile.ig_user_id,
                ig_username=profile.ig_username,
                access_token=profile.access_token,
                scopes=profile.scopes,
                connection_type=connection_type,
            )

            workspace = workspace_detail | {
                "ig_username": profile.ig_username,
                "ig_user_id": profile.ig_user_id,
                "connection_type": connection_type,
                "plan": "free",
                "active": True,
            }
            await self._activate_workspace(user.id, workspace["id"])
            return InstagramWorkspaceResponse(workspace=workspace)

        existing = await self.repository.find_connection_by_ig_user(profile.ig_user_id)
        if existing is not None:
            # Update connection in place and return existing workspace details
            await self.repository.update_connection(
                workspace_id=existing["workspace_id"],
                access_token=profile.access_token,
                scopes=profile.scopes,
                ig_username=profile.ig_username,
                connection_type=connection_type,
            )
            workspace_detail = await self.repository.get_workspace_detail(existing["workspace_id"])
            if workspace_detail is None:
                raise ApiError(
                    status_code=404,
                    code="workspace_not_found",
                    message="Workspace not found",
                )
            workspace = workspace_detail | {
                "ig_username": profile.ig_username,
                "ig_user_id": profile.ig_user_id,
                "connection_type": connection_type,
                "plan": "free",
                "active": True,
            }
            await self._activate_workspace(user.id, workspace["id"])
            return InstagramWorkspaceResponse(workspace=workspace)

        workspace = await self.repository.create_workspace_with_connection(
            owner_id=user.id,
            name=profile.ig_username,
            ig_user_id=profile.ig_user_id,
            ig_username=profile.ig_username,
            access_token=profile.access_token,
            scopes=profile.scopes,
            connection_type=connection_type,
        )
        await self._activate_workspace(user.id, workspace["id"])
        return InstagramWorkspaceResponse(workspace=workspace)

    async def disconnect(self, workspace: WorkspaceContext) -> dict[str, bool]:
        if not workspace.is_admin:
            raise ApiError(status_code=403, code="forbidden", message="Admin role required")
        await self.repository.disconnect(workspace.id)
        return {"disconnected": True}

    async def get_media(self, workspace_id: UUID, limit: int = 10, after: str | None = None) -> dict:
        connection = await self.repository.get_connection(workspace_id)
        if not connection:
            raise ApiError(status_code=400, code="not_connected", message="Instagram not connected to this workspace")

        ig_user_id = connection["ig_user_id"]
        token = connection["access_token_enc"].decode("utf-8")

        if not token or token.startswith("dev-token") or token == "dev":
            # Return premium mock media in development mode
            mock_data = [
                {
                    "id": f"mock-media-{i}",
                    "caption": f"This is a premium mock Reel #{i} talking about automations! 🚀 #vibedm #socialmedia",
                    "media_type": "VIDEO" if i % 3 == 0 else "IMAGE",
                    "media_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80" if i % 3 != 0 else "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=400&q=80",
                    "thumbnail_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80" if i % 3 != 0 else "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=400&q=80",
                    "permalink": "https://instagram.com",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                for i in range(1, limit + 1)
            ]
            return {
                "data": mock_data,
                "paging": {"cursors": {"after": "mock-cursor"} if after is None else None}
            }

        # Fetch from Instagram Graph API
        api_domain = "graph.facebook.com" if token and token.startswith("EAA") else "graph.instagram.com"
        async with httpx.AsyncClient(timeout=15.0) as client:
            params = {
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
                "limit": limit,
                "access_token": token,
            }
            if after:
                params["after"] = after

            res = await client.get(
                f"https://{api_domain}/v25.0/{ig_user_id}/media",
                params=params
            )
            if res.status_code != 200:
                raise ApiError(status_code=400, code="meta_api_failed", message=f"Meta API failed: {res.text}")
            return res.json()

