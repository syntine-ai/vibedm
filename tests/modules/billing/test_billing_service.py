from __future__ import annotations

from uuid import uuid4

import pytest

from app.deps import WorkspaceContext
from app.modules.billing.schemas.billing import CheckoutRequest, PlanResponse
from app.modules.billing.services.billing import BillingService, StaticBillingProvider


class FakeBillingRepository:
    def __init__(self) -> None:
        self.activated_free_plan: tuple[str, str] | None = None

    async def list_plans(self) -> list[PlanResponse]:
        return [
            PlanResponse(
                id="free",
                tier="free",
                display_name="Free",
                monthly_paise=0,
                yearly_paise=0,
                features=["Basic automations"],
                is_popular=False,
            ),
            PlanResponse(
                id="pro",
                tier="pro",
                display_name="Pro",
                monthly_paise=9900,
                yearly_paise=95040,
                features=["Unlimited automations"],
                is_popular=False,
            ),
        ]

    async def activate_free_plan(self, workspace_id, cycle: str) -> None:
        self.activated_free_plan = (str(workspace_id), cycle)


@pytest.mark.parametrize(
    ("monthly", "expected_yearly"),
    [(0, 0), (9900, 95040), (29900, 287040)],
)
def test_yearly_price_is_monthly_times_twelve_less_twenty_percent(
    monthly: int, expected_yearly: int
) -> None:
    assert BillingService.compute_yearly_paise(monthly) == expected_yearly


async def test_free_checkout_activates_immediately() -> None:
    repository = FakeBillingRepository()
    workspace = WorkspaceContext(id=uuid4(), role="owner")
    service = BillingService(repository=repository, provider=StaticBillingProvider())

    result = await service.checkout(workspace, CheckoutRequest(plan_id="free", cycle="monthly"))

    assert result.activated is True
    assert result.checkout_url is None
    assert repository.activated_free_plan == (str(workspace.id), "monthly")


async def test_paid_checkout_returns_adapter_url() -> None:
    repository = FakeBillingRepository()
    workspace = WorkspaceContext(id=uuid4(), role="owner")
    service = BillingService(repository=repository, provider=StaticBillingProvider())

    result = await service.checkout(workspace, CheckoutRequest(plan_id="pro", cycle="yearly"))

    assert result.activated is False
    assert result.checkout_url == "https://billing.example/checkout/pro/yearly"
