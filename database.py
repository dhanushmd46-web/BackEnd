import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./kuppam.db")
engine =create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False}
)

SessionLocal=sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)
class Base(declarative_base):
    pass
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()