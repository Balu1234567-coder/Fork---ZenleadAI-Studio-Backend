import asyncio
from src.config.mongodb import MongoDB
from src.utils.ai_model_registry import AI_MODELS_CONFIG
from datetime import datetime

async def setup_ai_models():
    """Setup AI models in database"""
    models_collection = await MongoDB.get_collection("ai_models")
    
    for slug, config in AI_MODELS_CONFIG.items():
        existing_model = await models_collection.find_one({"slug": slug})
        
        if not existing_model:
            model_data = {
                "slug": slug,
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **config
            }
            
            result = await models_collection.insert_one(model_data)
            print(f"Created AI model: {config['name']} - ID: {result.inserted_id}")
        else:
            print(f"AI model already exists: {config['name']}")

if __name__ == "__main__":
    asyncio.run(setup_ai_models())
