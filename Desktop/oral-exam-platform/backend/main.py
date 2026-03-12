from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, SessionLocal
from models import Base, User, Exam, StudentExam  # 添加 StudentExam！
import hashlib
from datetime import datetime
from typing import List, Optional

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

# ===== Request Models =====

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    user_type: str = "student"

class CreateExamRequest(BaseModel):
    name: str
    description: str
    topics: List[str]

# ===== Helper Functions =====

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from token (simple implementation)"""
    try:
        return int(token.split('_')[1])
    except:
        return None

# ===== Auth Endpoints =====

@app.post("/api/auth/register")
def register(request: RegisterRequest):
    db = SessionLocal()
    
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        db.close()
        return {"error": "User already exists"}
    
    password_hash = hash_password(request.password)
    new_user = User(
        email=request.email,
        username=request.username,
        password_hash=password_hash,
        user_type=request.user_type
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "user_type": new_user.user_type,
        "message": "User created successfully"
    }

@app.post("/api/auth/login")
def login(request: LoginRequest):
    db = SessionLocal()
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        db.close()
        return {"error": "User not found", "success": False}
    
    password_hash = hash_password(request.password)
    if password_hash != user.password_hash:
        db.close()
        return {"error": "Invalid password", "success": False}
    
    db.close()
    
    return {
        "success": True,
        "token": f"token_{user.id}",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "user_type": user.user_type
        }
    }

# ===== Exam Endpoints =====

# ===== Student Exam Endpoints =====

@app.post("/api/exams/{exam_id}/start")
def start_exam(exam_id: int, token: str):
    """Student starts an exam"""
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    # Check if exam exists
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    if not exam:
        db.close()
        return {"error": "Exam not found", "success": False}
    
    # Create student exam record
    student_exam = StudentExam(
        student_id=user_id,
        exam_id=exam_id,
        status="in_progress"
    )
    
    db.add(student_exam)
    db.commit()
    db.refresh(student_exam)
    db.close()
    
    return {
        "success": True,
        "student_exam": {
            "id": student_exam.id,
            "exam_id": exam_id,
            "status": "in_progress",
            "started_at": student_exam.started_at.isoformat()
        }
    }

@app.get("/api/exams/available")
def get_available_exams(token: str):
    """Get all exams available for students"""
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    # Get all exams (all exams are available to all students)
    exams = db.query(Exam).all()
    
    db.close()
    
    return {
        "success": True,
        "exams": [
            {
                "id": exam.id,
                "name": exam.name,
                "description": exam.description,
                "topics": exam.topics,
                "teacher_id": exam.teacher_id,
                "created_at": exam.created_at.isoformat()
            }
            for exam in exams
        ]
    }

@app.get("/api/my-exams")
def get_my_exams(token: str):
    """Get exams that student has taken"""
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    student_exams = db.query(StudentExam).filter(
        StudentExam.student_id == user_id
    ).all()
    
    result = []
    for se in student_exams:
        exam = db.query(Exam).filter(Exam.id == se.exam_id).first()
        result.append({
            "id": se.id,
            "exam_id": exam.id,
            "exam_name": exam.name,
            "status": se.status,
            "started_at": se.started_at.isoformat(),
            "completed_at": se.completed_at.isoformat() if se.completed_at else None
        })
    
    db.close()
    
    return {
        "success": True,
        "student_exams": result
    }

@app.post("/api/exams")
def create_exam(request: CreateExamRequest, token: str):
    """Create a new exam"""
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    new_exam = Exam(
        name=request.name,
        description=request.description,
        topics=request.topics,
        teacher_id=user_id
    )
    
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    db.close()
    
    return {
        "success": True,
        "exam": {
            "id": new_exam.id,
            "name": new_exam.name,
            "description": new_exam.description,
            "topics": new_exam.topics,
            "created_at": new_exam.created_at.isoformat()
        }
    }

@app.get("/api/exams")
def get_exams(token: str):
    """Get all exams for the logged-in teacher"""
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    exams = db.query(Exam).filter(Exam.teacher_id == user_id).all()
    
    db.close()
    
    return {
        "success": True,
        "exams": [
            {
                "id": exam.id,
                "name": exam.name,
                "description": exam.description,
                "topics": exam.topics,
                "created_at": exam.created_at.isoformat()
            }
            for exam in exams
        ]
    }

@app.get("/api/exams/{exam_id}")
def get_exam(exam_id: int, token: str):
    """Get a specific exam"""
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.teacher_id == user_id
    ).first()
    
    db.close()
    
    if not exam:
        return {"error": "Exam not found", "success": False}
    
    return {
        "success": True,
        "exam": {
            "id": exam.id,
            "name": exam.name,
            "description": exam.description,
            "topics": exam.topics,
            "created_at": exam.created_at.isoformat()
        }
    }

# ===== Health Check =====

@app.get("/")
def read_root():
    return {"message": "Oral Exam Platform API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}