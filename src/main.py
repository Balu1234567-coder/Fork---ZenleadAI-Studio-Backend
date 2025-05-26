from fastapi import FastAPI
from src.routes.auth_routes import router as auth_router
from src.routes.user_routes import router as user_router
from src.config.mongodb import MongoDB

app = FastAPI(title="ZenleadAI-Studio Backend")

app.include_router(auth_router)
app.include_router(user_router)

@app.on_event("startup")
async def startup_event():
    print('trying to connect to MongoDB...')
    await MongoDB.connect()
    print('MongoDB connected successfully')

@app.on_event("shutdown")
async def shutdown_event():
    await MongoDB.close()

@app.get("/")
async def root():
    return {"message": "Welcome to ZenleadAI-Studio Backend"}