from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Users, RefreshToken, RoleEnum
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
import logging
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

SECRET_KEY = '194679e3j938492938382883dej3ioms998323ftu933@jd7233!'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
auth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


class VerificationEmailRequest(BaseModel):
    email: str
    verification_link: str


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    role: RoleEnum  



class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
logger = logging.getLogger(__name__)

# Register endpoint


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
    try:
        create_user_model = Users(
            username=create_user_request.username,
            email=create_user_request.email,
            hashed_password=bcrypt_context.hash(create_user_request.password),
            role=create_user_request.role  # role assigned from the request
        )
        db.add(create_user_model)
        db.commit()

        access_token = create_user_token(
            username=create_user_request.username,
            email=create_user_request.email,
            user_id=create_user_model.id,
            role=create_user_model.role,
            expires_delta=timedelta(hours=24)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": create_user_model.username,
            "role": create_user_model.role
        }

    except SQLAlchemyError as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")
    except Exception as e:
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error")



def create_refresh_token(user_id: int, expires_delta: Optional[timedelta] = None):
    encode = {'id': user_id}
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
        encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(
                status_code=401, detail="Invalid refresh token")

        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token, RefreshToken.user_id == user_id).first()
        if not db_token or db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=401, detail="Refresh token expired")

        user = db.query(Users).filter(Users.id == user_id).first()
        new_access_token = create_user_token(
            user.username, user.email, user.id, user.role, timedelta(hours=24))

        return {"access_token": new_access_token, "token_type": "bearer", "username": user.username, "role": user.role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password'
            )
        access_token = create_user_token(
            username=user.username,
            email=user.email,
            user_id=user.id,
            role=user.role,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(user.id, timedelta(days=7))
        new_refresh_token = RefreshToken(
            token=refresh_token, user_id=user.id, expires_at=datetime.utcnow() +
            timedelta(days=7)
        )
        db.add(new_refresh_token)
        db.commit()

        response = JSONResponse(content={
            'access_token': access_token,
            'token_type': 'bearer',
            'username': user.username,
            'role': user.role
        })
        response.set_cookie(key="token", value=access_token, httponly=True)
        return response

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=500, detail="Unexpected error during login")


def authenticate_user(email: str, password: str, db):
    user = db.query(Users).filter(Users.email == email).first()
    if user and bcrypt_context.verify(password, user.hashed_password):
        return user
    return None


def create_user_token(username: str, email: str, user_id: int, role: str, expires_delta: Optional[timedelta] = None):
    encode = {'sub': username, 'email': email, 'id': user_id, 'role': role}
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
        encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# Role-based access control (RBAC) middleware function
def role_access(required_role: RoleEnum):
    def role_checker(user: Users = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with role {user.role} is not authorized to access this resource."
            )
    return role_checker

# Get current user from token so that the role_access can track the logged in user
def get_current_user(token: str = Depends(auth2_bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        user = db.query(Users).filter(Users.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
