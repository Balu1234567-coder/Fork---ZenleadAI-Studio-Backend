from fastapi import APIRouter, Depends
from controllers.user_controller import UserController, UserResponseModel, CreditsResponseModel
from middleware.auth import get_current_user
from models.user import UserUpdate

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/{userId}", response_model=UserResponseModel)
async def get_user(userId: str, current_user: str = Depends(get_current_user)):
    return await UserController.get_user(userId, current_user)

@router.put("/{userId}", response_model=UserResponseModel)
async def update_user(userId: str, user_data: UserUpdate, current_user: str = Depends(get_current_user)):
    return await UserController.update_user(userId, user_data, current_user)

@router.get("/{userId}/credits", response_model=CreditsResponseModel)
async def get_user_credits(userId: str, current_user: str = Depends(get_current_user)):
    return await UserController.get_user_credits(userId, current_user)
