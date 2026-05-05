import os
from sqlmodel import create_engine, SQLModel, Session
from models import User  # Nujno za SQLModel.metadata.create_all

# Prebere URL iz docker-compose.yml, če ga ni, uporabi privzetega
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user_admin:user_password@db-users:5432/user_db"
)

# echo=True nam v logih pokaže vse SQL ukaze, kar je super za debuggiranje
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """
    Ta funkcija dejansko ustvari tabele v Postgres bazi.
    Pokliči jo v main.py znotraj @app.on_event("startup").
    """
    print("Preverjam in ustvarjam tabele v bazi...")
    SQLModel.metadata.create_all(engine)
    print("Tabele so bile uspešno preverjene/ustvarjene.")

def get_session():
    """
    Dependency, ki ga uporabiš v FastAPI endpointih za delo z bazo.
    """
    with Session(engine) as session:
        yield session