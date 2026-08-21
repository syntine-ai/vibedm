from __future__ import annotations

import pytest

from app.core.errors import ApiError
from app.modules.automations.schemas.automations import AutomationDetail, AutomationStep
from app.modules.automations.services.automations import validate_activation


def test_activation_validation_reports_missing_requirements() -> None:
    automation = AutomationDetail(
        id="00000000-0000-0000-0000-000000000001",
        name="Draft",
        status="draft",
        trigger_type=None,
        trigger_config={},
        steps=[],
    )

    with pytest.raises(ApiError) as exc:
        validate_activation(automation)

    assert exc.value.status_code == 422
    assert exc.value.code == "automation_incomplete"
    assert exc.value.details == {"missing": ["trigger_type", "trigger_config", "steps"]}


def test_activation_validation_accepts_valid_dm_flow() -> None:
    automation = AutomationDetail(
        id="00000000-0000-0000-0000-000000000001",
        name="DM Welcome",
        status="draft",
        trigger_type="dm",
        trigger_config={"keywords": ["price"], "match": "any"},
        steps=[
            AutomationStep(
                id="00000000-0000-0000-0000-000000000002",
                order=1,
                action_type="send_dm",
                config={"message": "Hello"},
            )
        ],
    )

    validate_activation(automation)
