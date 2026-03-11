from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, SessionLocal
from models import Base, User
import hashlib

# create database
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# identify requested data form
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

# fx
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# API root
@app.get("/")
def read_root():
    return {"message": "Oral Exam Platform API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/auth/register")
def register(request: RegisterRequest):
    db = SessionLocal()
    
    # check if the user exist
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        db.close()
        return {"error": "User already exists"}
    
    # create new user
    password_hash = hash_password(request.password)
    new_user = User(
        email=request.email,
        username=request.username,
        password_hash=password_hash
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "message": "User created successfully"
    }

@app.post("/api/auth/login")
def login(request: LoginRequest):
    db = SessionLocal()
    
    # find user
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        db.close()
        return {"error": "User not found", "success": False}
    
    # verify password
    password_hash = hash_password(request.password)
    if password_hash != user.password_hash:
        db.close()
        return {"error": "Invalid password", "success": False}
    
    db.close()
    
    # login success
    return {
        "success": True,
        "token": f"token_{user.id}",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }