import asyncio
from src.config.mongodb import MongoDB
from datetime import datetime

async def setup_sample_organizations():
    """Setup sample organizations for testing"""
    organizations_collection = await MongoDB.get_collection("organizations")
    
    sample_orgs = [
        {
            "name": "RIMES",
            "domain": "rimes.int",
            "discount_percentage": 5.0,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    for org in sample_orgs:
        existing_org = await organizations_collection.find_one({"domain": org["domain"]})
        if not existing_org:
            result = await organizations_collection.insert_one(org)
            print(f"Created organization: {org['name']} for domain {org['domain']} - ID: {result.inserted_id}")
        else:
            print(f"Organization already exists for domain: {org['domain']}")

if __name__ == "__main__":
    asyncio.run(setup_sample_organizations())
