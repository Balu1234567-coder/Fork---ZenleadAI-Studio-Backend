from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"

class Currency(str, Enum):
    USD = "USD"
    INR = "INR"

class PlanStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"

class Organization(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    name: str
    domain: Optional[str] = None
    discount_percentage: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class SubscriptionPlan(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    name: str
    description: str
    price: float
    currency: Currency = Currency.INR
    billing_cycle: BillingCycle
    credits: int
    features: Dict[str, Any] = {}
    status: PlanStatus = PlanStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentTransaction(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    user_id: str
    plan_id: str
    organization_id: Optional[str] = None
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    amount: float
    currency: str = "INR"
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: Optional[str] = None
    credits_added: int = 0
    discount_applied: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class UserSubscription(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    user_id: str
    plan_id: str
    transaction_id: str
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response Models
class CreatePlanRequest(BaseModel):
    name: str
    description: str
    price: float
    currency: Currency = Currency.INR
    billing_cycle: BillingCycle
    credits: int
    features: Dict[str, Any] = {}

class UpdatePlanRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[Currency] = None
    credits: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    status: Optional[PlanStatus] = None

class CreateOrganizationRequest(BaseModel):
    name: str
    domain: Optional[str] = None
    discount_percentage: float = 0.0

class InitiatePaymentRequest(BaseModel):
    plan_id: str

class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PlanResponse(BaseModel):
    uid: str = Field(alias="_id")
    name: str
    description: str
    price: float
    currency: Currency
    billing_cycle: BillingCycle
    credits: int
    features: Dict[str, Any]
    status: PlanStatus
    created_at: datetime

class OrganizationResponse(BaseModel):
    uid: str = Field(alias="_id")
    name: str
    domain: Optional[str]
    discount_percentage: float
    is_active: bool
    created_at: datetime

class TransactionResponse(BaseModel):
    uid: str = Field(alias="_id")
    plan_name: str
    amount: float
    status: PaymentStatus
    credits_added: int
    created_at: datetime

class SubscriptionResponse(BaseModel):
    uid: str = Field(alias="_id")
    plan: PlanResponse
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime]
    auto_renew: bool
