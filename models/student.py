from sqlalchemy import Column ,Integer,String
from database import Base

class Student(Base):
    __tablename__="students"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(50),nullable=False)
    age=Column(Integer,nullable=False)
    email=Column(String, nullable=False)
    city=Column(String(100),default="unknown")
    