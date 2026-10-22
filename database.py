import os
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load .env from the same folder as database.py
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

#======or you can use====
# DATABASE_URL = "mysql+pymysql://root:@localhost:3306/mini_ecommerce"


engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

