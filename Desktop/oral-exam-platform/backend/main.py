from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import engine, SessionLocal
from models import Base, User, Exam, StudentExam
import hashlib
from datetime import datetime
from typing import List, Optional

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

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

class ConversationMessage(BaseModel):
    student_exam_id: int
    message: str
    current_question_number: int = 1

# ===== Helper Functions =====

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id_from_token(token: str) -> Optional[int]:
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

@app.post("/api/exams")
def create_exam(request: CreateExamRequest, token: str = ""):
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
def get_exams(token: str = ""):
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

# ===== Student Exam Endpoints =====

@app.post("/api/exams/{exam_id}/start")
def start_exam(exam_id: int, token: str = ""):
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    if not exam:
        db.close()
        return {"error": "Exam not found", "success": False}
    
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
def get_available_exams(token: str = ""):
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    try:
        exams = db.query(Exam).all()
        
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
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        db.close()

@app.get("/api/exams/{exam_id}")
def get_exam(exam_id: int, token: str = ""):
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

@app.get("/api/my-exams")
def get_my_exams(token: str = ""):
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    try:
        student_exams = db.query(StudentExam).filter(
            StudentExam.student_id == user_id
        ).all()
        
        result = []
        for se in student_exams:
            exam = db.query(Exam).filter(Exam.id == se.exam_id).first()
            if exam:
                result.append({
                    "id": se.id,
                    "exam_id": exam.id,
                    "exam_name": exam.name,
                    "status": se.status,
                    "started_at": se.started_at.isoformat(),
                    "completed_at": se.completed_at.isoformat() if se.completed_at else None
                })
        
        return {
            "success": True,
            "student_exams": result
        }
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        db.close()

# ===== Conversation/Voice Endpoints =====

EXAM_QUESTIONS = {
    "Python Basics": [
        "What is a variable in Python and how do you declare one?",
        "Can you explain the difference between a list and a tuple?",
        "What is a function and why would you use one?",
        "How do you handle errors in Python?",
        "What is a loop and when would you use it?"
    ],
    "Machine Learning": [
        "What is the difference between supervised and unsupervised learning?",
        "Can you explain what a neural network is?",
        "What is overfitting and how do you prevent it?",
        "What is the purpose of a training set and a test set?",
        "Can you explain what a decision tree is?"
    ]
}

@app.post("/api/conversations/start")
def start_conversation(student_exam_id: int, token: str = ""):
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    student_exam = db.query(StudentExam).filter(
        StudentExam.id == student_exam_id
    ).first()
    
    if not student_exam:
        db.close()
        return {"error": "Student exam not found", "success": False}
    
    exam = db.query(Exam).filter(Exam.id == student_exam.exam_id).first()
    
    db.close()
    
    questions = EXAM_QUESTIONS.get(exam.name, EXAM_QUESTIONS["Python Basics"])
    first_question = questions[0]
    
    try:
        audio = elevenlabs_client.generate(
            text=first_question,
            voice="Bella",
            model="eleven_monolingual_v1"
        )
        
        return {
            "success": True,
            "conversation_id": student_exam_id,
            "question": first_question,
            "question_number": 1,
            "total_questions": len(questions)
        }
    except Exception as e:
        return {"error": f"Failed to generate audio: {str(e)}", "success": False}

@app.post("/api/conversations/message")
def send_conversation_message(msg: ConversationMessage, token: str = ""):
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    student_exam = db.query(StudentExam).filter(
        StudentExam.id == msg.student_exam_id
    ).first()
    
    if not student_exam:
        db.close()
        return {"error": "Student exam not found", "success": False}
    
    exam = db.query(Exam).filter(Exam.id == student_exam.exam_id).first()
    questions = EXAM_QUESTIONS.get(exam.name, EXAM_QUESTIONS["Python Basics"])
    
    db.close()
    
    next_question_idx = msg.current_question_number  # 使用前端传来的
    is_complete = next_question_idx >= len(questions)
    
    if is_complete:
        next_question = None
    else:
        next_question = questions[next_question_idx]
    
    return {
        "success": True,
        "student_answer": msg.message,
        "is_complete": is_complete,
        "next_question": next_question,
        "message": "Exam completed!" if is_complete else "Next question generated"
    }

@app.post("/api/conversations/complete")
def complete_exam(student_exam_id: int, token: str = ""):
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    student_exam = db.query(StudentExam).filter(
        StudentExam.id == student_exam_id
    ).first()
    
    if not student_exam:
        db.close()
        return {"error": "Student exam not found", "success": False}
    
    student_exam.status = "completed"
    student_exam.completed_at = datetime.utcnow()
    
    db.commit()
    db.close()
    
    return {
        "success": True,
        "message": "Exam completed successfully",
        "student_exam_id": student_exam_id
    }

# ===== Health Check =====

@app.get("/")
def read_root():
    return {"message": "Oral Exam Platform API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}