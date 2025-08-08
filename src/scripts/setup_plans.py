import asyncio
from src.config.mongodb import MongoDB
from datetime import datetime

async def setup_comprehensive_plans():
    """Setup all pricing plans based on frontend structure"""
    plans_collection = await MongoDB.get_collection("plans")
    
    # Clear existing plans if you want to start fresh
    # await plans_collection.delete_many({})
    
    plans = [
        # USD Monthly Plans
        {
            "name": "Starter",
            "description": "Perfect for individuals and small projects",
            "price": 9.0,
            "currency": "USD",
            "billing_cycle": "monthly",
            "credits": 1000,  # You can adjust credits based on your business logic
            "features": {
                "languages_supported": 3,
                "voice_clones": 2,
                "audio_processing_minutes": 100,
                "text_to_speech": "basic",
                "support": "standard",
                "export_formats": ["MP3", "WAV"],
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Professional",
            "description": "Ideal for content creators and businesses",
            "price": 29.0,
            "currency": "USD",
            "billing_cycle": "monthly",
            "credits": 3000,
            "features": {
                "languages_supported": 20,
                "voice_clones": 10,
                "audio_processing_minutes": 500,
                "text_to_speech": "advanced",
                "video_generation": "10 videos/month",
                "support": "priority",
                "export_formats": ["All formats"],
                "api_access": True,
                "best_value": True,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Enterprise",
            "description": "For large teams and organizations",
            "price": 99.0,
            "currency": "USD",
            "billing_cycle": "monthly",
            "credits": 10000,
            "features": {
                "languages_supported": 50,
                "voice_clones": "unlimited",
                "audio_processing_minutes": "unlimited",
                "text_to_speech": "premium",
                "video_generation": "unlimited",
                "support": "24/7 dedicated",
                "white_label_solutions": True,
                "sla_guarantee": True,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        
        # INR Monthly Plans
        {
            "name": "Starter",
            "description": "Perfect for individuals and small projects",
            "price": 799.0,
            "currency": "INR",
            "billing_cycle": "monthly",
            "credits": 1000,
            "features": {
                "languages_supported": 3,
                "voice_clones": 2,
                "audio_processing_minutes": 100,
                "text_to_speech": "basic",
                "support": "standard",
                "export_formats": ["MP3", "WAV"],
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Professional",
            "description": "Ideal for content creators and businesses",
            "price": 1999.0,
            "currency": "INR",
            "billing_cycle": "monthly",
            "credits": 3000,
            "features": {
                "languages_supported": 20,
                "voice_clones": 10,
                "audio_processing_minutes": 500,
                "text_to_speech": "advanced",
                "video_generation": "10 videos/month",
                "support": "priority",
                "export_formats": ["All formats"],
                "api_access": True,
                "best_value": True,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Enterprise",
            "description": "For large teams and organizations",
            "price": 4999.0,
            "currency": "INR",
            "billing_cycle": "monthly",
            "credits": 10000,
            "features": {
                "languages_supported": 50,
                "voice_clones": "unlimited",
                "audio_processing_minutes": "unlimited",
                "text_to_speech": "premium",
                "video_generation": "unlimited",
                "support": "24/7 dedicated",
                "white_label_solutions": True,
                "sla_guarantee": True,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        
        # USD Yearly Plans
        {
            "name": "Starter",
            "description": "Perfect for individuals and small projects",
            "price": 89.0,
            "currency": "USD",
            "billing_cycle": "yearly",
            "credits": 12000,  # 12 months worth
            "features": {
                "languages_supported": 3,
                "voice_clones": 2,
                "audio_processing_minutes": 100,
                "text_to_speech": "basic",
                "support": "standard",
                "export_formats": ["MP3", "WAV"],
                "annual_savings": 19,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Professional",
            "description": "Ideal for content creators and businesses",
            "price": 290.0,
            "currency": "USD",
            "billing_cycle": "yearly",
            "credits": 36000,  # 12 months worth
            "features": {
                "languages_supported": 20,
                "voice_clones": 10,
                "audio_processing_minutes": 500,
                "text_to_speech": "advanced",
                "video_generation": "10 videos/month",
                "support": "priority",
                "export_formats": ["All formats"],
                "api_access": True,
                "best_value": True,
                "annual_savings": 58,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Enterprise",
            "description": "For large teams and organizations",
            "price": 990.0,
            "currency": "USD",
            "billing_cycle": "yearly",
            "credits": 120000,  # 12 months worth
            "features": {
                "languages_supported": 50,
                "voice_clones": "unlimited",
                "audio_processing_minutes": "unlimited",
                "text_to_speech": "premium",
                "video_generation": "unlimited",
                "support": "24/7 dedicated",
                "white_label_solutions": True,
                "sla_guarantee": True,
                "annual_savings": 198,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        
        # INR Yearly Plans
        {
            "name": "Starter",
            "description": "Perfect for individuals and small projects",
            "price": 7990.0,
            "currency": "INR",
            "billing_cycle": "yearly",
            "credits": 12000,
            "features": {
                "languages_supported": 3,
                "voice_clones": 2,
                "audio_processing_minutes": 100,
                "text_to_speech": "basic",
                "support": "standard",
                "export_formats": ["MP3", "WAV"],
                "annual_savings": 1598,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Professional",
            "description": "Ideal for content creators and businesses",
            "price": 19990.0,
            "currency": "INR",
            "billing_cycle": "yearly",
            "credits": 36000,
            "features": {
                "languages_supported": 20,
                "voice_clones": 10,
                "audio_processing_minutes": 500,
                "text_to_speech": "advanced",
                "video_generation": "10 videos/month",
                "support": "priority",
                "export_formats": ["All formats"],
                "api_access": True,
                "best_value": True,
                "annual_savings": 3998,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "name": "Enterprise",
            "description": "For large teams and organizations",
            "price": 49990.0,
            "currency": "INR",
            "billing_cycle": "yearly",
            "credits": 120000,
            "features": {
                "languages_supported": 50,
                "voice_clones": "unlimited",
                "audio_processing_minutes": "unlimited",
                "text_to_speech": "premium",
                "video_generation": "unlimited",
                "support": "24/7 dedicated",
                "white_label_solutions": True,
                "sla_guarantee": True,
                "annual_savings": 9998,
                "free_trial_days": 7,
                "no_credit_card_required": True
            },
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    for plan in plans:
        # Create unique identifier for each plan combination
        plan_identifier = f"{plan['name']}_{plan['currency']}_{plan['billing_cycle']}"
        
        existing_plan = await plans_collection.find_one({
            "name": plan["name"],
            "currency": plan["currency"],
            "billing_cycle": plan["billing_cycle"]
        })
        
        if not existing_plan:
            await plans_collection.insert_one(plan)
            print(f"Created plan: {plan_identifier}")
        else:
            print(f"Plan already exists: {plan_identifier}")

if __name__ == "__main__":
    asyncio.run(setup_comprehensive_plans())
