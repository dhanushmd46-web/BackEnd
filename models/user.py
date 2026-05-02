from sqlalchemy import Column,Integer,String
from database import Base

class User(Base):
    __tablename__="User"

    id=Column(Integer,primary_key=True)

    username=Column(String(50),unique=True,nullable=False)
    hashed_password=Column(String,nullable=False)