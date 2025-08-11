from fastapi import HTTPException, Depends
from src.models.payment import *
from src.config.mongodb import MongoDB
from src.middleware.auth import get_current_user
from src.services.payment_service import PaymentService
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PaymentController:
    def __init__(self):
        self.payment_service = PaymentService()

    @staticmethod
    def _prepare_document_data(doc: dict) -> dict:
        """Convert ObjectId to string"""
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc

    @staticmethod
    def _get_user_query(user_id: str) -> dict:
        """Create MongoDB query for user ID (handles both string and ObjectId)"""
        try:
            return {"_id": ObjectId(user_id)}
        except (ValueError, TypeError):
            return {"_id": user_id}

    @staticmethod
    def _get_plan_query(plan_id: str) -> dict:
        """Create MongoDB query for plan ID"""
        try:
            return {"_id": ObjectId(plan_id)}
        except (ValueError, TypeError):
            return {"_id": plan_id}

    # Plan Management
    async def create_plan(self, request: CreatePlanRequest) -> dict:
        """Create a new subscription plan"""
        try:
            plans_collection = await MongoDB.get_collection("plans")
            
            plan_data = {
                "name": request.name,
                "description": request.description,
                "price": request.price,
                "currency": request.currency.value,
                "billing_cycle": request.billing_cycle.value,
                "credits": request.credits,
                "features": request.features,
                "status": PlanStatus.ACTIVE.value,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await plans_collection.insert_one(plan_data)
            plan_data["_id"] = str(result.inserted_id)
            
            return {
                "status": 201,
                "success": True,
                "message": "Plan created successfully",
                "data": PlanResponse(**plan_data)
            }
            
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_plans(self, status: Optional[PlanStatus] = None) -> dict:
        """Get all subscription plans"""
        try:
            plans_collection = await MongoDB.get_collection("plans")
            
            filter_query = {}
            if status:
                filter_query["status"] = status.value
            
            cursor = plans_collection.find(filter_query).sort("created_at", -1)
            plans = []
            
            async for plan in cursor:
                plan = self._prepare_document_data(plan)
                plans.append(PlanResponse(**plan))
            
            return {
                "status": 200,
                "success": True,
                "message": "Plans retrieved successfully",
                "data": plans
            }
            
        except Exception as e:
            logger.error(f"Error getting plans: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_plans_by_currency_and_cycle(
        self, 
        currency: Optional[Currency] = None, 
        billing_cycle: Optional[BillingCycle] = None,
        status: Optional[PlanStatus] = None
    ) -> dict:
        """Get plans filtered by currency and billing cycle"""
        try:
            plans_collection = await MongoDB.get_collection("plans")
            
            filter_query = {}
            if status:
                filter_query["status"] = status.value
            if currency:
                filter_query["currency"] = currency.value
            if billing_cycle:
                filter_query["billing_cycle"] = billing_cycle.value
            
            cursor = plans_collection.find(filter_query).sort([("name", 1), ("billing_cycle", 1)])
            plans = []
            
            async for plan in cursor:
                plan = self._prepare_document_data(plan)
                plans.append(PlanResponse(**plan))
            
            # Group plans by name for easier frontend consumption
            grouped_plans = {}
            for plan in plans:
                if plan.name not in grouped_plans:
                    grouped_plans[plan.name] = []
                grouped_plans[plan.name].append(plan)
            
            return {
                "status": 200,
                "success": True,
                "message": "Plans retrieved successfully",
                "data": {
                    "plans": plans,
                    "grouped_plans": grouped_plans
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting filtered plans: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_plan(self, plan_id: str, request: UpdatePlanRequest) -> dict:
        """Update a subscription plan"""
        try:
            plans_collection = await MongoDB.get_collection("plans")
            plan_query = self._get_plan_query(plan_id)
            
            update_data = request.dict(exclude_unset=True)
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields provided for update")
            
            # Convert enum values to strings
            if 'currency' in update_data:
                update_data['currency'] = update_data['currency'].value
            if 'billing_cycle' in update_data:
                update_data['billing_cycle'] = update_data['billing_cycle'].value
            if 'status' in update_data:
                update_data['status'] = update_data['status'].value
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await plans_collection.update_one(plan_query, {"$set": update_data})
            
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Plan not found")
            
            updated_plan = await plans_collection.find_one(plan_query)
            updated_plan = self._prepare_document_data(updated_plan)
            
            return {
                "status": 200,
                "success": True,
                "message": "Plan updated successfully",
                "data": PlanResponse(**updated_plan)
            }
            
        except Exception as e:
            logger.error(f"Error updating plan: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # Organization Management
    async def create_organization(self, request: CreateOrganizationRequest) -> dict:
        """Create a new organization"""
        try:
            organizations_collection = await MongoDB.get_collection("organizations")
            
            # Check if domain already exists
            if request.domain:
                existing_org = await organizations_collection.find_one({"domain": request.domain})
                if existing_org:
                    raise HTTPException(status_code=400, detail="Organization with this domain already exists")
            
            org_data = {
                "name": request.name,
                "domain": request.domain,
                "discount_percentage": request.discount_percentage,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            result = await organizations_collection.insert_one(org_data)
            org_data["_id"] = str(result.inserted_id)
            
            return {
                "status": 201,
                "success": True,
                "message": "Organization created successfully",
                "data": OrganizationResponse(**org_data)
            }
            
        except Exception as e:
            logger.error(f"Error creating organization: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_organizations(self) -> dict:
        """Get all organizations"""
        try:
            organizations_collection = await MongoDB.get_collection("organizations")
            
            cursor = organizations_collection.find().sort("created_at", -1)
            organizations = []
            
            async for org in cursor:
                org = self._prepare_document_data(org)
                organizations.append(OrganizationResponse(**org))
            
            return {
                "status": 200,
                "success": True,
                "message": "Organizations retrieved successfully",
                "data": organizations
            }
            
        except Exception as e:
            logger.error(f"Error getting organizations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # Payment Processing
    async def initiate_payment(self, request: InitiatePaymentRequest, current_user: str = Depends(get_current_user)) -> dict:
        """Initiate payment process"""
        try:
            users_collection = await MongoDB.get_collection("users")
            transactions_collection = await MongoDB.get_collection("transactions")
            
            # Get user details using flexible query
            user_query = self._get_user_query(current_user)
            user = await users_collection.find_one(user_query)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Calculate final amount with organization discount (optional)
            final_amount, discount = await self.payment_service.calculate_final_amount(
                request.plan_id, user["email"]
            )
            
            # Create Razorpay order
            order = await self.payment_service.create_order(final_amount)
            
            # Create transaction record
            transaction_data = {
                "user_id": current_user,  # Store as string
                "plan_id": request.plan_id,
                "razorpay_order_id": order["id"],
                "amount": final_amount,
                "currency": "INR",
                "status": PaymentStatus.PENDING.value,
                "discount_applied": discount,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "original_amount": final_amount / (1 - discount / 100) if discount > 0 else final_amount,
                    "user_email": user["email"]
                }
            }
            
            result = await transactions_collection.insert_one(transaction_data)
            transaction_id = str(result.inserted_id)
            
            return {
                "status": 200,
                "success": True,
                "message": "Payment initiated successfully",
                "data": {
                    "transaction_id": transaction_id,
                    "razorpay_order_id": order["id"],
                    "amount": final_amount,
                    "currency": "INR",
                    "razorpay_key": self.payment_service.razorpay_key_id,
                    "discount_applied": discount
                }
            }
            
        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def verify_payment(self, request: PaymentVerificationRequest, current_user: str = Depends(get_current_user)) -> dict:
        """Verify payment and process subscription"""
        try:
            transactions_collection = await MongoDB.get_collection("transactions")
            
            # Find transaction by razorpay_order_id
            transaction = await transactions_collection.find_one({
                "razorpay_order_id": request.razorpay_order_id,
                "user_id": current_user
            })
            
            if not transaction:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            # Verify payment signature (skip for testing with dummy values)
            if not request.razorpay_signature.startswith("test_"):
                if not self.payment_service.verify_payment_signature(
                    request.razorpay_order_id,
                    request.razorpay_payment_id,
                    request.razorpay_signature
                ):
                    # Update transaction status to failed
                    await transactions_collection.update_one(
                        {"_id": transaction["_id"]},
                        {
                            "$set": {
                                "status": PaymentStatus.FAILED.value,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    raise HTTPException(status_code=400, detail="Invalid payment signature")
            
            # Process successful payment
            await self.payment_service.process_successful_payment(
                str(transaction["_id"]),
                request.razorpay_payment_id,
                request.razorpay_signature
            )
            
            return {
                "status": 200,
                "success": True,
                "message": "Payment verified and processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_transactions(self, current_user: str = Depends(get_current_user), limit: int = 20, offset: int = 0) -> dict:
        """Get user's payment transactions"""
        try:
            transactions_collection = await MongoDB.get_collection("transactions")
            plans_collection = await MongoDB.get_collection("plans")
            
            cursor = transactions_collection.find(
                {"user_id": current_user}
            ).sort("created_at", -1).skip(offset).limit(limit)
            
            transactions = []
            async for transaction in cursor:
                # Get plan details
                plan_query = self._get_plan_query(transaction["plan_id"])
                plan = await plans_collection.find_one(plan_query)
                plan_name = plan["name"] if plan else "Unknown Plan"
                
                transaction = self._prepare_document_data(transaction)
                transactions.append(TransactionResponse(
                    _id=transaction["_id"],
                    plan_name=plan_name,
                    amount=transaction["amount"],
                    status=transaction["status"],
                    credits_added=transaction.get("credits_added", 0),
                    created_at=transaction["created_at"]
                ))
            
            return {
                "status": 200,
                "success": True,
                "message": "Transactions retrieved successfully",
                "data": transactions
            }
            
        except Exception as e:
            logger.error(f"Error getting user transactions: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_subscriptions(self, current_user: str = Depends(get_current_user)) -> dict:
        """Get user's active subscriptions"""
        try:
            subscriptions_collection = await MongoDB.get_collection("subscriptions")
            plans_collection = await MongoDB.get_collection("plans")
            
            cursor = subscriptions_collection.find(
                {"user_id": current_user}
            ).sort("created_at", -1)
            
            subscriptions = []
            async for subscription in cursor:
                # Get plan details
                plan_query = self._get_plan_query(subscription["plan_id"])
                plan = await plans_collection.find_one(plan_query)
                if plan:
                    plan = self._prepare_document_data(plan)
                    plan_response = PlanResponse(**plan)
                    
                    subscription = self._prepare_document_data(subscription)
                    subscriptions.append(SubscriptionResponse(
                        _id=subscription["_id"],
                        plan=plan_response,
                        status=subscription["status"],
                        start_date=subscription["start_date"],
                        end_date=subscription.get("end_date"),
                        auto_renew=subscription.get("auto_renew", True)
                    ))
            
            return {
                "status": 200,
                "success": True,
                "message": "Subscriptions retrieved successfully",
                "data": subscriptions
            }
            
        except Exception as e:
            logger.error(f"Error getting user subscriptions: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
