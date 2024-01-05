from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from models import User
from database import get_db
from .auth import db_dependency, get_current_user, verify_password, get_password_hash, credentials_exception

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class ChangePassword(BaseModel):
    old_password: str
    new_password: str    
    

@router.get('/', status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    print('inside get_user')
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    print('returning user')
    return db.query(User).filter(User.id == user.get('id')).first()

@router.get('/hello', status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    print('inside get_user')
    return { 'message': 'hello world' }

@router.put('/password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, change_password: ChangePassword, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    user_model = db.query(User).filter(User.id == user.get('id')).first()
    if not verify_password(change_password.old_password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail='Incorrect Password')
    user_model.hashed_password = get_password_hash(change_password.new_password)
    db.add(user_model)
    db.commit()