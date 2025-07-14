from dotenv import load_dotenv
 
from sqlmodel import SQLModel, create_engine, Session
import os
DATABASE_URL="postgresql://abeelity_user:4HfQeVkqAjm=XK_@localhost:5432/abeelity_db"
 

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrado no .env")

engine = create_engine(DATABASE_URL, echo=True)
def get_session():
    return Session(engine)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)