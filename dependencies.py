from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jose import JWSError
from sqlalchemy.orm import Session


from database import get_db
from models.user import User
from utils.jwt import verify_access_token

bearer_schema=HTTPBearer()
def get_current_user(
        credentials:HTTPAuthorizationCredentials=Depends(bearer_schema),
        db:Session = Depends(get_db) 
):
    token = credentials.credentials
    try:
        username=verify_access_token(token)
    except JWSError:
        raise HTTPException(status_code=401,detail="token is invalid or expired")
    user=db.query(User).filter(User.username==username).first()
    if not user:
        raise HTTPException(status_code=401,detali="user not found")
    return user