import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.db_models import Base

def init_db():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set in .env")
        return
    
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
