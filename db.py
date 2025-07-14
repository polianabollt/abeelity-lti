# db.py
from sqlmodel import SQLModel, create_engine, Session
from models import LTIUserLaunch  # e outros modelos

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def get_session():
    return Session(engine)

def create_db_and_tables():
    from models import LMSPlatform
    SQLModel.metadata.create_all(engine)

def create_db():
    SQLModel.metadata.create_all(engine)