from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os




from database import Base,engine
from routers import auth,students


import models.user
import models.student
Base.metadata.create_all(bind=engine)
load_dotenv()


app=FastAPI(title="students management API",version="1.0.0")

FRONTEND_URL = os.getenv("FRONTEND_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,prefix="/auth",tags=["Authentication"])
app.include_router(students.router,prefix="/students",tags=["students"])


@app.get("/")
def root():
    return {"message": "student API is running"}
