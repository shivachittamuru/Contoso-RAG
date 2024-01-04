
from datetime import datetime, timedelta
from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Response, HTTPException
from starlette import status
from sqlalchemy.orm import Session
from models import User
from database import get_db
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/token')


class RegisterUser(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    
db_dependency = Annotated[Session, Depends(get_db)]

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Incorrect Credentials',
    headers={'WWW-Authenticate': 'Bearer'}
)


def get_user(db: Session, username: str):
    print('inside get_user')
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_exception
    return user

def verify_password(plain_password, hashed_password):
    print('inside verify_password')
    return bcrypt_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    print('inside get_password_hash')
    return bcrypt_context.hash(password)

def authenticate_user(db: db_dependency, username: str, password: str):
    print('inside authenticate_user')
    user = get_user(db, username)
    if not verify_password(password, user.hashed_password):
        raise credentials_exception
    return user

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    print('inside create_access_token')
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        print('inside get_current_user')
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        username: str = payload.get('sub')
        print(username)
        user_id: int = payload.get('id')
        print(user_id)
        user_role: str = payload.get('role')
        print(user_role)
        if username is None or user_id is None:
            raise credentials_exception
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        print('inside JWTError')
        raise credentials_exception
    

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(user: RegisterUser, db: db_dependency):
    print('inside register_user')
    db_user = User(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=get_password_hash(user.password),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    

@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency, response: Response):
    print('inside login_for_access_token')
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise credentials_exception
    access_token = create_access_token(data={'sub': user.username, 'id': user.id, 'role': user.role}, expires_delta=timedelta(minutes=30))
    response.set_cookie(key="auth_token", value=access_token, httponly=True, secure=True)

    return {'access_token': access_token, 'token_type': 'bearer'}
