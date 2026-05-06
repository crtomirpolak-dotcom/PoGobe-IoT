from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
import uuid
from typing import List
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

from models import User, UserCreate
from database import create_db_and_tables, get_session

app = FastAPI(
    title="User Service",
    description="API za upravljanje uporabnikov projekta Gobe IoT",
    version="1.0.1"
)

@app.on_event("startup")
def on_startup():
    print("Zagon aplikacije: preverjam tabele...")
    create_db_and_tables()

@app.get("/")
def read_root():
    """Osnovni endpoint za preverjanje delovanja (Healthcheck)."""
    return {
        "service": "User Service Online",
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/all", response_model=List[User])
async def list_users(session: Session = Depends(get_session)):
    """Izpiše vse uporabnike v bazi. Dostopno na: users.pogobe.top/all"""
    users = session.exec(select(User)).all()
    return users

@app.post("/register", response_model=User)
async def create_user(user_in: UserCreate, session: Session = Depends(get_session)):
    # Ustvarimo objekt za bazo iz podatkov, ki so prišli po API-ju
    # .dict() pretvori Pydantic model v slovar, 'exclude' pa odstrani password
    user_data = user_in.model_dump(exclude={"password"})
    
    # Tukaj ustvarimo končni model za bazo
    db_user = User(
        **user_data, 
        password_hash=user_in.password  # Zaenkrat samo prepišemo, kasneje tu dodaš hash()
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/devices/{user_id}", response_model=List[str])
async def get_user_devices(user_id: uuid.UUID, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Uporabnik ni najden")
    
    return user.device_ids or []


@app.get("/users/", response_model=List[User], include_in_schema=False)
async def legacy_list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()

# Povezava user in IoT device
@app.put("/devices/claim/{user_id}/{device_id}")
async def claim_device(user_id: uuid.UUID, device_id: str, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Uporabnik ni najden")
    
    if user.device_ids is None:
        user.device_ids = []
    
    if device_id not in user.device_ids:
        new_devices = list(user.device_ids)
        new_devices.append(device_id)
        user.device_ids = new_devices
        
        session.add(user)
        session.commit()
        session.refresh(user)
    
    return {"message": f"Naprava {device_id} uspešno dodeljena", "current_devices": user.device_ids}

SECRET_KEY = "skrivna_koda_za_gobe"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


#LOGIN
@app.post("/login", response_model=Token)
async def login(user_in: UserCreate, session: Session = Depends(get_session)):
    # Poiščemo uporabnika po emailu ali username-u
    statement = select(User).where(User.email == user_in.email)
    user = session.exec(statement).first()
    
    # Preverimo geslo (zaenkrat direktna primerjava, ker še nimaš hasha)
    if not user or user.password_hash != user_in.password:
        raise HTTPException(status_code=401, detail="Napačen email ali geslo")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

#GET podatki uporabnika
@app.get("/me", response_model=User)
async def get_me(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Neveljaven žeton")
    except:
        raise HTTPException(status_code=401, detail="Neveljaven žeton")
        
    user = session.exec(select(User).where(User.username == username)).first()
    return user

#Delete user
@app.delete("/delete/{user_id}")
async def delete_user(user_id: uuid.UUID, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Uporabnik ni najden")
    
    session.delete(user)
    session.commit()
    return {"message": f"Uporabnik {user_id} je bil uspešno izbrisan"}