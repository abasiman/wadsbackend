from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Users, RefreshToken, RoleEnum
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional, Annotated
import logging
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
import schemas
import crud

from auth import role_access, get_db  # Import role_access and get_db from auth

router = APIRouter(
    prefix="/guard_harbor",
    tags=["guard_harbor"]
)

SECRET_KEY = '194679e3j938492938382883dej3ioms998323ftu933@jd7233!'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependecy = Annotated[Session, Depends(get_db)]
logger = logging.getLogger(__name__)

@router.post("/add_checkpoint", dependencies=[Depends(role_access(RoleEnum.guard_harbor))])
def add_checkpoint_data(checkpoint: schemas.CheckpointDataRecord, db: db_dependecy):
    db_checkpoint = crud.create_checkpoint(db=db, checkpoint=checkpoint)
    db.add(db_checkpoint)
    db.commit()
    db.refresh(db_checkpoint)
    return JSONResponse(content={"detail": "Checkpoint data added successfully"}, status_code=status.HTTP_201_CREATED)



#added update_checkpoint endpoint in case we need it
@router.post("/update_checkpoint", dependencies=[Depends(role_access(RoleEnum.guard_harbor))])
def update_checkpoint_data(checkpoint_id: int, checkpoint: schemas.CheckpointDataRecord, db: db_dependecy):
    db_checkpoint = crud.get_checkpoint(db=db, checkpoint_id=checkpoint_id)
    if not db_checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    db_checkpoint.data = checkpoint.data
    db.commit()
    db.refresh(db_checkpoint)
    return JSONResponse(content={"detail": "Checkpoint data updated successfully"}, status_code=status.HTTP_200_OK)
#delete checkpoint endpoint
@router.post("/delete_checkpoint", dependencies=[Depends(role_access(RoleEnum.guard_harbor))])
def delete_checkpoint_data(checkpoint_id: int, db: db_dependecy):
    db_checkpoint = crud.get_checkpoint(db=db, checkpoint_id=checkpoint_id)
    if not db_checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    db.delete(db_checkpoint)
    db.commit()
    return JSONResponse(content={"detail": "Checkpoint data deleted successfully"}, status_code=status.HTTP_200_OK)
