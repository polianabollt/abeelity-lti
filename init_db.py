from db import create_db_and_tables, engine

if __name__ == "__main__":
    print("🧪 DATABASE_URL usado por init_db.py:", engine.url)
    create_db_and_tables()
