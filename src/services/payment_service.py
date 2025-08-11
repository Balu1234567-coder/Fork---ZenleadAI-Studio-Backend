import razorpay
from src.config.env import env_config
from src.config.mongodb import MongoDB
from src.models.payment import PaymentTransaction, PaymentStatus
from bson import ObjectId
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.razorpay_key_id = env_config.RAZORPAY_KEY_ID
        self.razorpay_key_secret = env_config.RAZORPAY_KEY_SECRET
        self.client = razorpay.Client(auth=(self.razorpay_key_id, self.razorpay_key_secret))

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

    @staticmethod
    def _get_transaction_query(transaction_id: str) -> dict:
        """Create MongoDB query for transaction ID"""
        try:
            return {"_id": ObjectId(transaction_id)}
        except (ValueError, TypeError):
            return {"_id": transaction_id}

    async def create_order(self, amount: float, currency: str = "INR", receipt: str = None) -> Dict[str, Any]:
        """Create a Razorpay order"""
        try:
            order_data = {
                "amount": int(amount * 100),
                "currency": currency,
                "receipt": receipt or f"receipt_{datetime.utcnow().timestamp()}",
                "payment_capture": 1
            }
            
            order = self.client.order.create(data=order_data)
            return order
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            raise Exception(f"Failed to create payment order: {str(e)}")

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """Verify Razorpay payment signature"""
        try:
            body = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                self.razorpay_key_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, razorpay_signature)
        except Exception as e:
            logger.error(f"Error verifying payment signature: {str(e)}")
            return False

    async def process_successful_payment(self, transaction_id: str, razorpay_payment_id: str, razorpay_signature: str):
        """Process successful payment and update user credits"""
        try:
            transactions_collection = await MongoDB.get_collection("transactions")
            users_collection = await MongoDB.get_collection("users")
            subscriptions_collection = await MongoDB.get_collection("subscriptions")
            plans_collection = await MongoDB.get_collection("plans")

            # Get transaction details
            transaction_query = self._get_transaction_query(transaction_id)
            transaction = await transactions_collection.find_one(transaction_query)
            if not transaction:
                raise Exception("Transaction not found")

            # Update transaction status
            await transactions_collection.update_one(
                transaction_query,
                {
                    "$set": {
                        "razorpay_payment_id": razorpay_payment_id,
                        "razorpay_signature": razorpay_signature,
                        "status": PaymentStatus.COMPLETED.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Get plan details
            plan_query = self._get_plan_query(transaction["plan_id"])
            plan = await plans_collection.find_one(plan_query)
            if not plan:
                raise Exception("Plan not found")

            # Add credits to user
            credits_to_add = plan["credits"]
            user_query = self._get_user_query(transaction["user_id"])
            
            await users_collection.update_one(
                user_query,
                {
                    "$inc": {"credits": credits_to_add},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            # Update transaction with credits added
            await transactions_collection.update_one(
                transaction_query,
                {"$set": {"credits_added": credits_to_add}}
            )

            # Create subscription
            end_date = None
            if plan["billing_cycle"] == "monthly":
                end_date = datetime.utcnow() + timedelta(days=30)
            elif plan["billing_cycle"] == "yearly":
                end_date = datetime.utcnow() + timedelta(days=365)

            subscription_data = {
                "user_id": transaction["user_id"],
                "plan_id": transaction["plan_id"],
                "transaction_id": transaction_id,
                "status": "active",
                "start_date": datetime.utcnow(),
                "end_date": end_date,
                "auto_renew": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            await subscriptions_collection.insert_one(subscription_data)

            logger.info(f"Payment processed successfully for user {transaction['user_id']}, credits added: {credits_to_add}")
            
        except Exception as e:
            logger.error(f"Error processing successful payment: {str(e)}")
            raise Exception(f"Failed to process payment: {str(e)}")

    async def calculate_final_amount(self, plan_id: str, user_email: str) -> tuple[float, float]:
        """Calculate final amount after organization discount (optional)"""
        plans_collection = await MongoDB.get_collection("plans")
        organizations_collection = await MongoDB.get_collection("organizations")
        
        # Get plan
        plan_query = self._get_plan_query(plan_id)
        plan = await plans_collection.find_one(plan_query)
        if not plan:
            raise Exception("Plan not found")
        
        base_amount = plan["price"]
        discount = 0.0
        
        # Check if user belongs to any organization (by email domain) - OPTIONAL
        email_domain = user_email.split("@")[1] if "@" in user_email else ""
        if email_domain:
            organization = await organizations_collection.find_one({
                "domain": email_domain,
                "is_active": True
            })
            if organization:
                discount = organization.get("discount_percentage", 0.0)
                logger.info(f"Applied {discount}% discount for domain {email_domain}")
        
        # Calculate final amount (if no organization discount, discount = 0)
        final_amount = base_amount * (1 - discount / 100)
        return final_amount, discount
