from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from src.config.env import env_config
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, env_config.JWT_SECRET_KEY, algorithms=[env_config.JWT_ALGORITHM])
        uid: str = payload.get("sub")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        return uid
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")