from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List
import nh3
from database import CensusTract, get_db
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI(title="IGS API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CensusTractModel(BaseModel):
    census_tract: str = Field(..., max_length=11)
    inclusion_score: float = Field(..., ge=0, le=100)
    growth_score: float = Field(..., ge=0, le=100)
    economy_score: float = Field(..., ge=0, le=100)
    community_score: float = Field(..., ge=0, le=100)

# Simulated user database (replace with real database in production)
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("securepassword123")
    }
}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username not in users_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/tracts/", response_model=List[CensusTractModel])
async def get_tracts(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    tracts = db.query(CensusTract).all()
    return [
        {
            "census_tract": nh3.clean(t.census_tract),
            "inclusion_score": t.inclusion_score,
            "growth_score": t.growth_score,
            "economy_score": t.economy_score,
            "community_score": t.community_score
        } for t in tracts
    ]