from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.modules.automations.workers.automations import run_automation


@patch("app.modules.automations.workers.automations.AutomationRepository", autospec=True)
@patch("app.db.get_sessionmaker")
async def test_run_automation_mock_mode_success(mock_get_sessionmaker, MockRepoClass) -> None:
    # Set up mock session and sessionmaker
    mock_session = MagicMock()
    mock_sessionmaker = MagicMock()
    
    # Mock the async context manager:
    # async with sessionmaker() as session:
    async_context = AsyncMock()
    async_context.__aenter__.return_value = mock_session
    mock_sessionmaker.return_value = async_context
    mock_get_sessionmaker.return_value = mock_sessionmaker

    mock_repo = MockRepoClass.return_value
    mock_repo.get_run = AsyncMock(
        return_value={
            "id": "11111111-1111-1111-1111-111111111111",
            "workspace_id": "22222222-2222-2222-2222-222222222222",
            "automation_id": "33333333-3333-3333-3333-333333333333",
            "trigger_event": {
                "sender": {"id": "ig-sender-bob"},
                "comment_id": "comment-abc",
            },
        }
    )
    mock_repo.get_detail = AsyncMock(
        return_value={
            "id": "33333333-3333-3333-3333-333333333333",
            "name": "Auto DM",
            "steps": [
                {
                    "id": "44444444-4444-4444-4444-444444444444",
                    "action_type": "send_dm",
                    "config": {"message": "Here is your coupon!"},
                },
                {
                    "id": "55555555-5555-5555-5555-555555555555",
                    "action_type": "send_comment_reply",
                    "config": {"message": "Done!"},
                },
            ],
        }
    )
    mock_repo.get_workspace_token = AsyncMock(return_value="dev-token")
    mock_repo.update_run = AsyncMock()

    res = await run_automation("11111111-1111-1111-1111-111111111111")
    assert res == {"status": "succeeded", "error": None}

    # Verify update_run was called with correct trace and succeeded status
    mock_repo.update_run.assert_called_once()
    _, kwargs = mock_repo.update_run.call_args
    assert kwargs["status"] == "succeeded"
    assert len(kwargs["step_trace"]) == 2
    assert kwargs["step_trace"][0]["status"] == "succeeded"
    assert kwargs["step_trace"][0]["action_type"] == "send_dm"
    assert kwargs["step_trace"][1]["status"] == "succeeded"
    assert kwargs["step_trace"][1]["action_type"] == "send_comment_reply"
