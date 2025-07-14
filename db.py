from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://abeelity_user:4HfQeVkqAjm%3DXK%5F@localhost:5432/abeelity_db"
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    return Session(engine)

def create_db_and_tables():
    from models import LMSPlatform
    SQLModel.metadata.create_all(engine)

def create_db():
    SQLModel.metadata.create_all(engine)