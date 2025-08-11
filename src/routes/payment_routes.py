from fastapi import APIRouter, Depends, Query
from src.controllers.payment_controller import PaymentController
from src.models.payment import *
from src.middleware.auth import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/payments", tags=["Payments"])
controller = PaymentController()

# Plan Management Routes
@router.post("/plans")
async def create_plan(request: CreatePlanRequest):
    """Create a new subscription plan"""
    return await controller.create_plan(request)

@router.get("/plans")
async def get_plans(status: Optional[PlanStatus] = None):
    """Get all subscription plans"""
    return await controller.get_plans(status)

@router.get("/plans/filtered")
async def get_filtered_plans(
    currency: Optional[Currency] = None,
    billing_cycle: Optional[BillingCycle] = None,
    status: Optional[PlanStatus] = None
):
    """Get plans filtered by currency and billing cycle"""
    return await controller.get_plans_by_currency_and_cycle(currency, billing_cycle, status)

@router.put("/plans/{plan_id}")
async def update_plan(plan_id: str, request: UpdatePlanRequest):
    """Update a subscription plan"""
    return await controller.update_plan(plan_id, request)

# Organization Management Routes
@router.post("/organizations")
async def create_organization(request: CreateOrganizationRequest):
    """Create a new organization"""
    return await controller.create_organization(request)

@router.get("/organizations")
async def get_organizations():
    """Get all organizations"""
    return await controller.get_organizations()

# Payment Processing Routes
@router.post("/initiate")
async def initiate_payment(
    request: InitiatePaymentRequest,
    current_user: str = Depends(get_current_user)
):
    """Initiate payment process"""
    return await controller.initiate_payment(request, current_user)

@router.post("/verify")
async def verify_payment(
    request: PaymentVerificationRequest,
    current_user: str = Depends(get_current_user)
):
    """Verify payment and process subscription"""
    return await controller.verify_payment(request, current_user)

# User Transaction and Subscription Routes
@router.get("/transactions")
async def get_user_transactions(
    current_user: str = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get user's payment transactions"""
    return await controller.get_user_transactions(current_user, limit, offset)

@router.get("/subscriptions")
async def get_user_subscriptions(
    current_user: str = Depends(get_current_user)
):
    """Get user's active subscriptions"""
    return await controller.get_user_subscriptions(current_user)
