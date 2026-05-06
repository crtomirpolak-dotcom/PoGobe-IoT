from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
import uuid
from typing import List
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Uvozi svoje modele in bazo
from models import User, UserCreate, UserLogin, Token, Device, UserBase
from database import create_db_and_tables, get_session

app = FastAPI(
    title="User Service",
    description="API za upravljanje uporabnikov projekta Gobe IoT",
    version="1.0.2"
)

# --- KONFIGURACIJA VARNOSTI ---
SECRET_KEY = "skrivna_koda_za_gobe"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- POMOŽNE FUNKCIJE ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Neveljaven žeton")
    except JWTError:
        raise HTTPException(status_code=401, detail="Neveljaven žeton")
        
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Uporabnik ne obstaja")
    return user

# --- STARTUP ---
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- JAVNI ENDPOINTI ---

@app.get("/")
def read_root():
    return {"service": "User Service Online", "status": "running"}

@app.post("/register", response_model=User)
async def create_user(user_in: UserCreate, session: Session = Depends(get_session)):
    user_data = user_in.model_dump(exclude={"password"})
    db_user = User(**user_data, password_hash=user_in.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
async def login(user_in: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if not user or user.password_hash != user_in.password:
        raise HTTPException(status_code=401, detail="Napačen email ali geslo")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=User)
async def get_me(user: User = Depends(get_current_user)):
    return user

# --- UPRAVLJANJE NAPRAV (IoT) ---

@app.put("/devices/claim/{device_id}")
async def claim_device(
    device_id: str, 
    user: User = Depends(get_current_user), 
    session: Session = Depends(get_session)
):
    """Poveže trenutno prijavljenega uporabnika z napravo."""
    if user.device_ids is None:
        user.device_ids = []
    
    if device_id not in user.device_ids:
        # Preverimo, če si to napravo lasti že kdo drug
        # (To je malce počasno s tvojo trenutno List strukturo, a deluje)
        all_users = session.exec(select(User)).all()
        for u in all_users:
            if u.device_ids and device_id in u.device_ids:
                raise HTTPException(status_code=400, detail="Naprava že ima lastnika")

        new_devices = list(user.device_ids)
        new_devices.append(device_id)
        user.device_ids = new_devices
        
        session.add(user)
        session.commit()
        session.refresh(user)
    
    return {"message": f"Naprava {device_id} je zdaj tvoja."}

# --- NOVI INTERNI ENDPOINT ZA SENSOR SERVICE ---

@app.get("/internal/device-owner/{device_id}")
async def get_device_owner(device_id: str, session: Session = Depends(get_session)):
    """
    Interni klic, ki ga uporablja Sensor Service. 
    Poišče uporabnika, ki ima to napravo v svojem seznamu device_ids.
    """
    # Ker imaš device_ids kot list v PostgreSQL stolpcu, uporabimo filter:
    statement = select(User).where(User.device_ids.contains(device_id))
    owner = session.exec(statement).first()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Lastnik naprave ni najden")
    
    return {
        "username": owner.username,
        "email": owner.email,
        "user_id": str(owner.id)
    }

# --- ADMIN / DEBUG ---

@app.get("/all", response_model=List[User])
async def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: uuid.UUID, session: Session = Depends(get_session), token: str = Depends(oauth2_scheme)):
    user = session.get(User, user_id)
    if not user: raise HTTPException(status_code=404)
    session.delete(user)
    session.commit()
    return None