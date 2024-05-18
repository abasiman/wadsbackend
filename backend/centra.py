from fastapi.responses import JSONResponse
from jose import jwt
import requests
from typing import Annotated
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Users, RefreshToken
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional
import logging
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
import schemas
import crud
import schemas

from auth import role_access, get_db
from models import RoleEnum, Users


router = APIRouter(
    prefix="/centra",
    tags=["centra"]
)
SECRET_KEY = '194679e3j938492938382883dej3ioms998323ftu933@jd7233!'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
# auth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependecy = Annotated[Session, Depends(get_db)]

logger = logging.getLogger(__name__)

db_dependency = Depends(get_db)


@router.post("/new_wet_leaves", dependencies=[Depends(role_access(RoleEnum.centra))])
def add_wet_leaves(wet_leaves: schemas.WetLeavesRecord, db: Session = Depends(get_db)):
    db_collection = crud.create_wet_leaves(db=db, wet_leaves=wet_leaves)
    return JSONResponse(content={"detail": "Wet leaves record added successfully"}, status_code=status.HTTP_201_CREATED)


@router.post("/new_dry_leaves", dependencies=[Depends(role_access(RoleEnum.centra))])
def add_dry_leaves(dry_leaves: schemas.DryLeavesRecord, db: Session = Depends(get_db)):
    db_dry = crud.create_dry_leaves(db=db, dry_leaves=dry_leaves)
    return JSONResponse(content={"detail": "Dry leaves record added successfully"}, status_code=status.HTTP_201_CREATED)


@router.post("/new_flour", dependencies=[Depends(role_access(RoleEnum.centra))])
def add_flour(flour: schemas.FlourRecord, db: Session = Depends(get_db)):
    db_flour = crud.create_flour(db=db, flour=flour)
    return JSONResponse(content={"detail": "Flour record added successfully"}, status_code=status.HTTP_201_CREATED)