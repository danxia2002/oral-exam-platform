from openai import OpenAI
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
import base64
from io import BytesIO

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
        # 不要设置 total_score 和 answers，让它们用默认值
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

def evaluate_answer(question: str, student_answer: str) -> dict:
    """Evaluate student's answer using OpenAI GPT"""
    try:
        prompt = f"""
You are a professional education assessment expert. Please evaluate the student's answer.

Question: {question}

Student's Answer: {student_answer}

Please return ONLY a JSON response in this exact format, no other text:
{{
  "score": <0-100>,
  "strengths": "<strengths>",
  "improvements": "<improvements>",
  "feedback": "<feedback>"
}}
"""
        
        message = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        response_text = message.choices[0].message.content.strip()
        
        print(f"OpenAI response: {response_text[:200]}")  # 调试用
        
        # 提取 JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        import json
        evaluation = json.loads(response_text.strip())
        
        return {
            "success": True,
            "score": evaluation.get("score", 0),
            "strengths": evaluation.get("strengths", ""),
            "improvements": evaluation.get("improvements", ""),
            "feedback": evaluation.get("feedback", "")
        }
    
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        print(f"Response was: {response_text}")
        return {
            "success": False,
            "score": 0,
            "feedback": "Evaluation failed"
        }
    except Exception as e:
        print(f"Evaluation error: {str(e)}")
        return {
            "success": False,
            "score": 0,
            "feedback": "Evaluation failed"
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
        audio_stream = elevenlabs_client.text_to_speech.convert(
            text=first_question,
            voice_id="EXAVITQu4vr4xnSDxMaL",
            model_id="eleven_turbo_v2"
        )
        
        # 读取 generator
        audio_bytes = b''.join(audio_stream)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "success": True,
            "conversation_id": student_exam_id,
            "question": first_question,
            "question_audio": f"data:audio/mpeg;base64,{audio_base64}",
            "question_number": 1,
            "total_questions": len(questions)
        }
    except Exception as e:
        print(f"Audio error: {str(e)}")
        return {
            "success": True,
            "conversation_id": student_exam_id,
            "question": first_question,
            "question_audio": None,
            "question_number": 1,
            "total_questions": len(questions)
        }

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
    
    # 获取当前问题
    current_question_idx = msg.current_question_number - 1
    current_question = questions[current_question_idx] if current_question_idx < len(questions) else None
    
    response_data = {
        "success": True,
        "student_answer": msg.message,
        "is_complete": False,
        "next_question": None,
        "next_question_audio": None,
        "score": 0,
        "feedback": "",
        "message": "Next question generated"
    }
    
    # 评估当前问题的答案
    if current_question:
        evaluation = evaluate_answer(current_question, msg.message)
        response_data["score"] = evaluation.get("score", 0)
        response_data["feedback"] = evaluation.get("feedback", "")
        
        # 保存答案到 answers 字段（JSON 格式）
        import json
        try:
            answers = json.loads(student_exam.answers or "[]")
        except:
            answers = []
        
        existing = [a for a in answers if a["question_number"] == msg.current_question_number]

        if not existing:
          answers.append({
              "question_number": msg.current_question_number,
              "question": current_question,
              "answer": msg.message,
              "score": evaluation.get("score", 0),
              "feedback": evaluation.get("feedback", ""),
              "strengths": evaluation.get("strengths", ""),
              "improvements": evaluation.get("improvements", "")
          })
        
        student_exam.answers = json.dumps(answers)
    
    # 检查是否完成
    next_question_idx = msg.current_question_number
    is_complete = next_question_idx >= len(questions)
    response_data["is_complete"] = is_complete
    
    if not is_complete:
        next_question = questions[next_question_idx]
        response_data["next_question"] = next_question
        
        try:
            audio_stream = elevenlabs_client.text_to_speech.convert(
                text=next_question,
                voice_id="EXAVITQu4vr4xnSDxMaL",
                model_id="eleven_turbo_v2"
            )
            
            audio_bytes = b''.join(audio_stream)
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            response_data["next_question_audio"] = f"data:audio/mpeg;base64,{audio_base64}"
        except Exception as e:
            print(f"Audio error: {str(e)}")
            response_data["next_question_audio"] = None
    else:
        response_data["message"] = "Exam completed!"
        
        # 计算总分
        import json
        answers = json.loads(student_exam.answers or "[]")
        total_score = sum(ans.get("score", 0) for ans in answers)
        student_exam.total_score = total_score
    
    db.commit()
    db.close()
    
    return response_data

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

@app.get("/api/student-exams/{student_exam_id}/details")
def get_exam_details(student_exam_id: int, token: str = ""):
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    student_exam = db.query(StudentExam).filter(
        StudentExam.id == student_exam_id,
        StudentExam.student_id == user_id
    ).first()
    
    if not student_exam:
        db.close()
        return {"error": "Student exam not found", "success": False}
    
    exam = db.query(Exam).filter(Exam.id == student_exam.exam_id).first()
    
    db.close()
    
    import json
    answers = json.loads(student_exam.answers or "[]")
    
    return {
        "success": True,
        "exam_id": student_exam.exam_id,
        "exam_name": exam.name,
        "total_score": student_exam.total_score,
        "started_at": student_exam.started_at.isoformat(),
        "completed_at": student_exam.completed_at.isoformat() if student_exam.completed_at else None,
        "answers": answers
    }

@app.get("/api/teacher/analytics")
def get_teacher_analytics(token: str = ""):
    """Get analytics for teacher - all student exam results"""
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        return {"error": "Invalid token", "success": False}
    
    db = SessionLocal()
    
    # 获取该教师创建的所有考试
    exams = db.query(Exam).filter(Exam.teacher_id == user_id).all()
    
    analytics_data = []
    
    for exam in exams:
        # 获取该考试的所有学生参与记录
        student_exams = db.query(StudentExam).filter(
            StudentExam.exam_id == exam.id
        ).all()
        
        # 过滤已完成的考试
        completed_exams = [se for se in student_exams if se.status == "completed"]
        
        if len(completed_exams) == 0:
            continue  # 跳过没有完成记录的考试
        
        # 计算统计数据
        scores = [se.total_score for se in completed_exams]
        total_questions = 5  # 固定为 5 题
        max_score = total_questions * 100  # 最高分 500
        
        exam_analytics = {
            "exam_id": exam.id,
            "exam_name": exam.name,
            "description": exam.description,
            "total_students": len(completed_exams),
            "completed_students": len(completed_exams),
            "completion_rate": f"{(len(completed_exams) / len(student_exams) * 100) if student_exams else 0:.1f}%",
            "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "max_score": max_score,
            "students": []
        }
        
        # 收集学生信息
        for se in completed_exams:
            student = db.query(User).filter(User.id == se.student_id).first()
            if student:
                exam_analytics["students"].append({
                    "student_id": student.id,
                    "student_name": student.username,
                    "student_email": student.email,
                    "score": se.total_score,
                    "score_percentage": round((se.total_score / max_score) * 100, 1),
                    "completed_at": se.completed_at.isoformat() if se.completed_at else None
                })
        
        # 按分数降序排序
        exam_analytics["students"].sort(key=lambda x: x["score"], reverse=True)
        
        analytics_data.append(exam_analytics)
    
    db.close()
    
    return {
        "success": True,
        "analytics": analytics_data
    }

# ===== Health Check =====

@app.get("/")
def read_root():
    return {"message": "Oral Exam Platform API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}