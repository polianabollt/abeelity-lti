from dotenv import load_dotenv
load_dotenv()

from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrado no .env")

engine = create_engine(DATABASE_URL, echo=True)
def get_session():
    return Session(engine)