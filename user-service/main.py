from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
import uuid
from typing import List

# Uvozi lokalne module
from models import User
from database import create_db_and_tables, get_session

app = FastAPI(
    title="User Service",
    description="API za upravljanje uporabnikov projekta Gobe IoT",
    version="1.0.1"
)

# Ustvari tabele ob zagonu
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
async def create_user(user: User, session: Session = Depends(get_session)):
    """Ustvari novega uporabnika. Dostopno na: users.pogobe.top/register"""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/devices/{user_id}", response_model=List[str])
async def get_user_devices(user_id: uuid.UUID, session: Session = Depends(get_session)):
    """Pridobi naprave specifičnega uporabnika. Dostopno na: users.pogobe.top/devices/{id}"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Uporabnik ni najden")
    
    # Preprečimo napako, če so device_ids NULL (vrnemo prazen seznam)
    return user.device_ids or []

# Če želiš obdržati tudi staro pot /users/ za kompatibilnost:
@app.get("/users/", response_model=List[User], include_in_schema=False)
async def legacy_list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()