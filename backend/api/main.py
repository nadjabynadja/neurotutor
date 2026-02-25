"""
NeuroTutor Backend - FastAPI Application
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import json
import asyncio
import os
import uuid

# Import our modules
from cognitive.attention_detector import AttentionDetector
from cognitive.webcam_simulator import WebcamSimulator
from llm.directive_engine import DirectiveEngine, DirectiveMapper, CognitiveState as DirectiveCognitiveState, Directive
from llm.minimax_client import NeuroTutorLLM


app = FastAPI(title="NeuroTutor API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Data Models ==============

class CognitiveStateResponse(BaseModel):
    timestamp: str
    cognitive_load: float
    attention_level: float
    engagement: float
    confusion_indicator: float
    fatigue_indicator: float
    is_calibrated: bool


class DirectiveRequest(BaseModel):
    cognitive_load: float
    attention_level: float
    engagement: float
    confusion_indicator: float
    fatigue_indicator: float


class DirectiveResponse(BaseModel):
    directives: List[str]
    prompt_prefix: str
    teaching_tone: str
    content_pacing: str
    suggested_break: bool
    suggested_action: str


class ChatRequest(BaseModel):
    message: str
    cognitive_state: Optional[DirectiveRequest] = None
    context: Optional[Dict] = None
    use_llm: bool = True


class ChatResponse(BaseModel):
    response: str
    directives: List[str]
    cognitive_state: Dict
    llm_provider: Optional[str] = None


# ============== Global State ==============

# Store active attention detectors per session
attention_detectors: Dict[str, AttentionDetector] = {}
directive_engine = DirectiveEngine()

# Initialize LLM
llm = NeuroTutorLLM()


# ============== API Routes ==============

@app.get("/")
async def root():
    return {"message": "NeuroTutor API", "version": "1.0.0"}


@app.get("/health")
async def health():
    # Test simulator availability
    try:
        test_sim = WebcamSimulator()
        test_sim.start()
        simulator_ok = True
        test_sim.stop()
    except Exception:
        simulator_ok = False

    # Test camera availability (non-blocking check)
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        camera_ok = cap.isOpened()
        cap.release()
    except Exception:
        camera_ok = False

    return {
        "status": "healthy",
        "llm_configured": llm.client.is_configured(),
        "llm_provider": "MiniMax" if llm.client.is_configured() else None,
        "simulator_available": simulator_ok,
        "camera_available": camera_ok,
        "active_sessions": len(attention_detectors),
        "active_simulators": len(webcam_simulators),
        "demo_mode": not camera_ok and simulator_ok,
    }


# ============== Cognitive State ==============

@app.post("/cognitive/start/{session_id}")
async def start_cognitive_tracking(session_id: str):
    """Start cognitive tracking for a session."""
    if session_id in attention_detectors:
        return {"message": "Already tracking", "session_id": session_id}
    
    detector = AttentionDetector()
    if not detector.start():
        raise HTTPException(status_code=500, detail="Failed to start camera")
    
    attention_detectors[session_id] = detector
    return {"message": "Started tracking", "session_id": session_id}


@app.post("/cognitive/stop/{session_id}")
async def stop_cognitive_tracking(session_id: str):
    """Stop cognitive tracking for a session."""
    if session_id not in attention_detectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    detector = attention_detectors[session_id]
    detector.stop()
    del attention_detectors[session_id]
    
    return {"message": "Stopped tracking", "session_id": session_id}


@app.get("/cognitive/state/{session_id}")
async def get_cognitive_state(session_id: str):
    """Get current cognitive state for a session."""
    if session_id not in attention_detectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    detector = attention_detectors[session_id]
    state = detector.get_cognitive_state()
    
    return CognitiveStateResponse(
        timestamp=state.timestamp.isoformat(),
        cognitive_load=state.cognitive_load,
        attention_level=state.attention_level,
        engagement=state.engagement,
        confusion_indicator=state.confusion_indicator,
        fatigue_indicator=state.fatigue_indicator,
        is_calibrated=state.is_calibrated
    )


@app.post("/cognitive/calibrate/{session_id}")
async def calibrate_session(session_id: str, duration: int = 60):
    """Calibrate baseline for a session."""
    if session_id not in attention_detectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    detector = attention_detectors[session_id]
    baseline = detector.calibrate(duration)
    
    return {
        "message": "Calibration complete",
        "baseline": {
            "cognitive_load": baseline.cognitive_load,
            "attention_level": baseline.attention_level,
            "engagement": baseline.engagement
        }
    }


# ============== Directives ==============

@app.post("/directive/analyze")
async def analyze_directive(request: DirectiveRequest):
    """Analyze cognitive state and return directives."""
    state = DirectiveCognitiveState(
        cognitive_load=request.cognitive_load,
        attention_level=request.attention_level,
        engagement=request.engagement,
        confusion_indicator=request.confusion_indicator,
        fatigue_indicator=request.fatigue_indicator
    )
    
    directives = directive_engine.get_directives(state)
    
    return DirectiveResponse(
        directives=[d.value for d in directives],
        prompt_prefix=directive_engine.build_prompt_prefix(directives),
        teaching_tone=DirectiveMapper._get_teaching_tone(directives),
        content_pacing=DirectiveMapper._get_pacing(directives),
        suggested_break=Directive.BREAK in directives,
        suggested_action=directive_engine.get_suggested_action()
    )


# ============== Chat (LLM Integration) ==============

def _build_demo_response(message: str, directives: list, state) -> str:
    """
    Build a clean, tutor-sounding response for demo mode (no API key configured).
    Adapts tone based on cognitive state without leaking internal directive text.
    """
    directive_values = [d.value for d in directives]

    # Choose an opening based on highest-priority directive
    if "break" in directive_values:
        opening = "You've been working hard — let's take this one step at a time."
    elif "simplify" in directive_values or "slow_down" in directive_values:
        opening = "Let me walk you through this step by step."
    elif "encourage" in directive_values:
        opening = "You're doing great — let's work through this together."
    elif "speed_up" in directive_values:
        opening = "You're clearly getting the hang of this — let's go deeper."
    elif "example" in directive_values:
        opening = "Great question — here's a concrete way to think about it."
    else:
        opening = "That's a great question!"

    # Build adaptive body
    body = f'You asked about: "{message}". '

    if state.confusion_indicator > 0.6:
        body += "This can feel tricky at first. Let's start from the basics and build up gradually. "
    elif state.cognitive_load > 0.7:
        body += "Let's break this into smaller pieces — no rush. "
    elif state.fatigue_indicator > 0.6:
        body += "I'll keep this concise so we don't overload you right now. "
    elif state.attention_level > 0.8 and state.cognitive_load < 0.5:
        body += "You're in a great learning flow — I'll give you the full picture. "

    footer = (
        "To unlock full AI-powered responses, set the MINIMAX_API_KEY "
        "environment variable and restart the backend."
    )

    return f"{opening} {body}\n\n_{footer}_"


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the NeuroTutor LLM.
    
    Uses MiniMax API when configured, falls back to simulation.
    """
    # Get cognitive state from request or create default
    if request.cognitive_state:
        state_dict = request.cognitive_state.model_dump()
        state = DirectiveCognitiveState(
            cognitive_load=request.cognitive_state.cognitive_load,
            attention_level=request.cognitive_state.attention_level,
            engagement=request.cognitive_state.engagement,
            confusion_indicator=request.cognitive_state.confusion_indicator,
            fatigue_indicator=request.cognitive_state.fatigue_indicator
        )
    else:
        state_dict = {
            "cognitive_load": 0.5,
            "attention_level": 0.5,
            "engagement": 0.5,
            "confusion_indicator": 0.2,
            "fatigue_indicator": 0.2
        }
        state = DirectiveCognitiveState(
            cognitive_load=0.5,
            attention_level=0.5,
            engagement=0.5,
            confusion_indicator=0.2,
            fatigue_indicator=0.2
        )
    
    # Get directives
    directives = directive_engine.get_directives(state)
    
    # Use MiniMax if configured and requested
    if request.use_llm and llm.client.is_configured():
        result = llm.generate_response(
            user_message=request.message,
            cognitive_state=state_dict,
            context=request.context
        )
        
        return ChatResponse(
            response=result.get("response", "Error generating response"),
            directives=result.get("directives", [d.value for d in directives]),
            cognitive_state=state_dict,
            llm_provider="MiniMax"
        )
    
    # Fallback: produce a clean, natural-sounding tutor response (no API key needed)
    response = _build_demo_response(request.message, directives, state)

    return ChatResponse(
        response=response,
        directives=[d.value for d in directives],
        cognitive_state=state_dict,
        llm_provider="demo"
    )


# ============== WebSocket for Real-time ==============

@app.websocket("/ws/cognitive/{session_id}")
async def websocket_cognitive(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time cognitive state streaming.
    Tries the physical webcam first; falls back to WebcamSimulator automatically
    so the demo works without any camera hardware.
    """
    await websocket.accept()

    # Try real camera; fall back to simulator for demo/no-hardware environments
    detector = AttentionDetector()
    use_simulator = not detector.start()

    sim = None
    if use_simulator:
        detector.stop()
        sim = WebcamSimulator()
        sim.start()

    try:
        while True:
            if use_simulator:
                state_data = sim.get_state_dict()
            else:
                state = detector.get_cognitive_state()
                state_data = state.to_dict()

            await websocket.send_json(state_data)
            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
    finally:
        if use_simulator and sim:
            sim.stop()
        elif not use_simulator:
            detector.stop()


# ============== Course Management ==============

class Course(BaseModel):
    id: str
    name: str
    professor_id: str
    students: List[str] = []


courses_db: Dict[str, Course] = {}


@app.post("/courses")
async def create_course(course: Course):
    """Create a new course."""
    courses_db[course.id] = course
    return course


@app.get("/courses/{course_id}")
async def get_course(course_id: str):
    """Get course details."""
    if course_id not in courses_db:
        raise HTTPException(status_code=404, detail="Course not found")
    return courses_db[course_id]


# ============== Professor Dashboard APIs ==============

class StudentMetrics(BaseModel):
    student_id: str
    student_name: str
    student_email: str
    attention_score: float
    cognitive_load: float
    engagement_score: float
    sessions_count: int
    average_session_duration: float
    last_session: Optional[str]
    is_at_risk: bool
    risk_reasons: List[str] = []


class CourseAnalytics(BaseModel):
    course_id: str
    course_name: str
    total_students: int
    active_students: int
    average_attention: float
    average_cognitive_load: float
    average_engagement: float
    at_risk_students_count: int
    sessions_this_week: int
    average_session_duration: float
    total_learning_hours: float
    engagement_trend: List[float]
    attention_trend: List[float]
    cognitive_load_trend: List[float]


class StudentSessionHistory(BaseModel):
    session_id: str
    course_id: str
    course_name: str
    started_at: str
    ended_at: Optional[str]
    duration_minutes: float
    attention_score: float
    cognitive_load: float
    engagement_score: float
    messages_count: int


class StudentHistoryResponse(BaseModel):
    student_id: str
    student_name: str
    total_sessions: int
    total_learning_hours: float
    average_attention: float
    average_cognitive_load: float
    average_engagement: float
    sessions: List[StudentSessionHistory]
    at_risk_alerts: List[Dict]


MOCK_COURSES = {
    "1": {"id": "1", "name": "Introduction to Computer Science", "code": "CS101", "professor_id": "prof1", "students": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
    "2": {"id": "2", "name": "Data Structures & Algorithms", "code": "CS201", "professor_id": "prof1", "students": ["s2", "s3", "s4", "s9", "s10"]},
    "3": {"id": "3", "name": "Machine Learning Fundamentals", "code": "CS301", "professor_id": "prof1", "students": ["s1", "s5", "s6", "s11", "s12", "s13"]},
}

MOCK_STUDENTS = {
    "s1": {"id": "s1", "name": "Alice Johnson", "email": "alice@university.edu", "attention": 0.85, "cognitive_load": 0.45, "engagement": 0.82, "sessions": 12, "avg_duration": 45.2, "last_session": "2026-02-20T14:30:00"},
    "s2": {"id": "s2", "name": "Bob Smith", "email": "bob@university.edu", "attention": 0.42, "cognitive_load": 0.78, "engagement": 0.38, "sessions": 8, "avg_duration": 32.1, "last_session": "2026-02-19T10:15:00"},
    "s3": {"id": "s3", "name": "Carol Williams", "email": "carol@university.edu", "attention": 0.91, "cognitive_load": 0.52, "engagement": 0.88, "sessions": 15, "avg_duration": 52.3, "last_session": "2026-02-21T09:00:00"},
    "s4": {"id": "s4", "name": "David Brown", "email": "david@university.edu", "attention": 0.35, "cognitive_load": 0.85, "engagement": 0.28, "sessions": 5, "avg_duration": 18.5, "last_session": "2026-02-15T16:45:00"},
    "s5": {"id": "s5", "name": "Eva Martinez", "email": "eva@university.edu", "attention": 0.78, "cognitive_load": 0.55, "engagement": 0.75, "sessions": 10, "avg_duration": 41.0, "last_session": "2026-02-20T11:30:00"},
    "s6": {"id": "s6", "name": "Frank Lee", "email": "frank@university.edu", "attention": 0.52, "cognitive_load": 0.68, "engagement": 0.48, "sessions": 7, "avg_duration": 35.8, "last_session": "2026-02-18T13:20:00"},
    "s7": {"id": "s7", "name": "Grace Kim", "email": "grace@university.edu", "attention": 0.88, "cognitive_load": 0.42, "engagement": 0.85, "sessions": 14, "avg_duration": 48.6, "last_session": "2026-02-21T08:15:00"},
    "s8": {"id": "s8", "name": "Henry Chen", "email": "henry@university.edu", "attention": 0.62, "cognitive_load": 0.58, "engagement": 0.65, "sessions": 9, "avg_duration": 38.2, "last_session": "2026-02-19T15:00:00"},
    "s9": {"id": "s9", "name": "Iris Wang", "email": "iris@university.edu", "attention": 0.33, "cognitive_load": 0.92, "engagement": 0.25, "sessions": 4, "avg_duration": 15.3, "last_session": "2026-02-14T12:00:00"},
    "s10": {"id": "s10", "name": "Jack Davis", "email": "jack@university.edu", "attention": 0.72, "cognitive_load": 0.48, "engagement": 0.70, "sessions": 11, "avg_duration": 44.5, "last_session": "2026-02-20T16:30:00"},
    "s11": {"id": "s11", "name": "Karen Taylor", "email": "karen@university.edu", "attention": 0.81, "cognitive_load": 0.51, "engagement": 0.79, "sessions": 13, "avg_duration": 46.8, "last_session": "2026-02-21T10:45:00"},
    "s12": {"id": "s12", "name": "Leo Garcia", "email": "leo@university.edu", "attention": 0.28, "cognitive_load": 0.88, "engagement": 0.22, "sessions": 3, "avg_duration": 12.1, "last_session": "2026-02-10T14:00:00"},
    "s13": {"id": "s13", "name": "Maria Rodriguez", "email": "maria@university.edu", "attention": 0.76, "cognitive_load": 0.54, "engagement": 0.73, "sessions": 9, "avg_duration": 39.5, "last_session": "2026-02-19T11:15:00"},
}


def calculate_risk(student_data):
    risk_reasons = []
    is_at_risk = False
    
    if student_data["attention"] < 0.5:
        is_at_risk = True
        risk_reasons.append("Low attention (<50%)")
    
    if student_data["engagement"] < 0.4:
        is_at_risk = True
        risk_reasons.append("Low engagement (<40%)")
    
    if student_data["cognitive_load"] > 0.8:
        is_at_risk = True
        risk_reasons.append("High cognitive overload (>80%)")
    
    if student_data["sessions"] < 5:
        is_at_risk = True
        risk_reasons.append("Low session count (<5)")
    
    return is_at_risk, risk_reasons


@app.get("/api/professor/courses")
async def get_professor_courses(professor_id: str = "prof1"):
    """Get all courses for a professor."""
    courses = []
    for course_id, course in MOCK_COURSES.items():
        if course["professor_id"] == professor_id:
            student_count = len(course["students"])
            at_risk_count = sum(
                1 for sid in course["students"] 
                if calculate_risk(MOCK_STUDENTS[sid])[0]
            )
            courses.append({
                "id": course["id"],
                "name": course["name"],
                "code": course["code"],
                "student_count": student_count,
                "at_risk_count": at_risk_count,
                "active_today": student_count - at_risk_count
            })
    return courses


@app.get("/api/professor/courses/{course_id}/students")
async def get_course_students(course_id: str):
    """Get all students in a course with their metrics."""
    if course_id not in MOCK_COURSES:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = MOCK_COURSES[course_id]
    students = []
    
    for student_id in course["students"]:
        student_data = MOCK_STUDENTS.get(student_id)
        if student_data:
            is_at_risk, risk_reasons = calculate_risk(student_data)
            students.append({
                "student_id": student_id,
                "student_name": student_data["name"],
                "student_email": student_data["email"],
                "attention_score": student_data["attention"],
                "cognitive_load": student_data["cognitive_load"],
                "engagement_score": student_data["engagement"],
                "sessions_count": student_data["sessions"],
                "average_session_duration": student_data["avg_duration"],
                "last_session": student_data["last_session"],
                "is_at_risk": is_at_risk,
                "risk_reasons": risk_reasons
            })
    
    return {
        "course_id": course_id,
        "course_name": course["name"],
        "students": students
    }


@app.get("/api/professor/courses/{course_id}/analytics")
async def get_course_analytics(course_id: str):
    """Get detailed analytics for a course."""
    if course_id not in MOCK_COURSES:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = MOCK_COURSES[course_id]
    students_data = [MOCK_STUDENTS[sid] for sid in course["students"] if sid in MOCK_STUDENTS]
    
    if not students_data:
        raise HTTPException(status_code=404, detail="No students in course")
    
    avg_attention = sum(s["attention"] for s in students_data) / len(students_data)
    avg_cognitive_load = sum(s["cognitive_load"] for s in students_data) / len(students_data)
    avg_engagement = sum(s["engagement"] for s in students_data) / len(students_data)
    at_risk_count = sum(1 for s in students_data if calculate_risk(s)[0])
    
    total_sessions = sum(s["sessions"] for s in students_data)
    total_hours = sum(s["sessions"] * s["avg_duration"] for s in students_data) / 60
    
    return {
        "course_id": course_id,
        "course_name": course["name"],
        "total_students": len(students_data),
        "active_students": len(students_data) - at_risk_count,
        "average_attention": round(avg_attention, 2),
        "average_cognitive_load": round(avg_cognitive_load, 2),
        "average_engagement": round(avg_engagement, 2),
        "at_risk_students_count": at_risk_count,
        "sessions_this_week": total_sessions // 4,
        "average_session_duration": round(total_hours * 60 / total_sessions if total_sessions > 0 else 0, 1),
        "total_learning_hours": round(total_hours, 1),
        "engagement_trend": [0.65, 0.68, 0.72, 0.70, 0.75, avg_engagement],
        "attention_trend": [0.70, 0.72, 0.75, 0.73, 0.78, avg_attention],
        "cognitive_load_trend": [0.55, 0.52, 0.58, 0.60, 0.55, avg_cognitive_load],
        "metrics_distribution": {
            "high_attention": sum(1 for s in students_data if s["attention"] >= 0.7),
            "medium_attention": sum(1 for s in students_data if 0.4 <= s["attention"] < 0.7),
            "low_attention": sum(1 for s in students_data if s["attention"] < 0.4),
            "high_engagement": sum(1 for s in students_data if s["engagement"] >= 0.7),
            "medium_engagement": sum(1 for s in students_data if 0.4 <= s["engagement"] < 0.7),
            "low_engagement": sum(1 for s in students_data if s["engagement"] < 0.4),
        }
    }


@app.get("/api/professor/alerts")
async def get_professor_alerts(professor_id: str = "prof1"):
    """Get at-risk student alerts across all courses for a professor."""
    alerts = []
    for course_id, course in MOCK_COURSES.items():
        if course["professor_id"] != professor_id:
            continue
        for student_id in course["students"]:
            student = MOCK_STUDENTS.get(student_id)
            if not student:
                continue
            is_at_risk, risk_reasons = calculate_risk(student)
            if is_at_risk:
                alerts.append({
                    "student_id": student_id,
                    "student_name": student["name"],
                    "course_id": course_id,
                    "course_name": course["name"],
                    "reasons": risk_reasons,
                    "severity": "high" if len(risk_reasons) >= 2 else "medium",
                    "last_session": student["last_session"],
                })
    # Sort by severity then student name
    alerts.sort(key=lambda a: (0 if a["severity"] == "high" else 1, a["student_name"]))
    return alerts


@app.get("/api/professor/students/{student_id}/history")
async def get_student_history(student_id: str):
    """Get detailed learning history for a student."""
    if student_id not in MOCK_STUDENTS:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = MOCK_STUDENTS[student_id]
    
    sessions = [
        {
            "session_id": f"{student_id}_session_{i+1}",
            "course_id": "1" if i % 2 == 0 else "2",
            "course_name": "Introduction to Computer Science" if i % 2 == 0 else "Data Structures & Algorithms",
            "started_at": f"2026-02-{15+i:02d}T{10+i:02d}:00:00",
            "ended_at": f"2026-02-{15+i:02d}T{10+i+1:02d}:30:00",
            "duration_minutes": student["avg_duration"] - (i * 2),
            "attention_score": min(0.95, student["attention"] + (i * 0.02)),
            "cognitive_load": max(0.3, student["cognitive_load"] - (i * 0.03)),
            "engagement_score": min(0.95, student["engagement"] + (i * 0.01)),
            "messages_count": 5 + i
        }
        for i in range(min(student["sessions"], 10))
    ]
    
    at_risk_alerts = []
    if student["attention"] < 0.5:
        at_risk_alerts.append({
            "type": "attention",
            "severity": "high",
            "message": f"Attention score ({student['attention']:.0%}) below threshold",
            "date": "2026-02-20"
        })
    if student["engagement"] < 0.4:
        at_risk_alerts.append({
            "type": "engagement",
            "severity": "high",
            "message": f"Engagement score ({student['engagement']:.0%}) below threshold",
            "date": "2026-02-20"
        })
    if student["cognitive_load"] > 0.8:
        at_risk_alerts.append({
            "type": "cognitive_overload",
            "severity": "medium",
            "message": f"Cognitive load ({student['cognitive_load']:.0%}) too high",
            "date": "2026-02-20"
        })
    if student["sessions"] < 5:
        at_risk_alerts.append({
            "type": "low_participation",
            "severity": "medium",
            "message": f"Only {student['sessions']} sessions completed",
            "date": "2026-02-20"
        })
    
    total_hours = student["sessions"] * student["avg_duration"] / 60
    
    return {
        "student_id": student_id,
        "student_name": student["name"],
        "student_email": student["email"],
        "total_sessions": student["sessions"],
        "total_learning_hours": round(total_hours, 1),
        "average_attention": student["attention"],
        "average_cognitive_load": student["cognitive_load"],
        "average_engagement": student["engagement"],
        "sessions": sessions,
        "at_risk_alerts": at_risk_alerts
    }


# ============== Webcam Simulator ==============

webcam_simulators: Dict[str, WebcamSimulator] = {}


@app.post("/simulator/start/{session_id}")
async def start_simulator(session_id: str):
    """Start webcam simulator for a session."""
    if session_id in webcam_simulators:
        return {"message": "Already running", "session_id": session_id}
    
    sim = WebcamSimulator()
    sim.start()
    webcam_simulators[session_id] = sim
    return {"message": "Simulator started", "session_id": session_id}


@app.post("/simulator/stop/{session_id}")
async def stop_simulator(session_id: str):
    """Stop webcam simulator."""
    if session_id not in webcam_simulators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    webcam_simulators[session_id].stop()
    del webcam_simulators[session_id]
    return {"message": "Simulator stopped"}


@app.get("/simulator/state/{session_id}")
async def get_simulator_state(session_id: str):
    """Get simulator cognitive state."""
    if session_id not in webcam_simulators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return webcam_simulators[session_id].get_state_dict()


@app.post("/simulator/scenario/{session_id}")
async def set_simulator_scenario(session_id: str, scenario: str):
    """Apply a scenario to simulator."""
    if session_id not in webcam_simulators:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sim = webcam_simulators[session_id]
    if scenario == "struggling":
        sim.simulate_struggling_student()
    elif scenario == "engaged":
        sim.simulate_engaged_student()
    elif scenario == "flow":
        sim.simulate_flow_state()
    elif scenario == "fatigued":
        sim.simulate_fatigued_student()
    
    return {"message": f"Scenario {scenario} applied", "session_id": session_id}


# ============== Demo Mode ==============

_DEMO_SCENARIOS = {
    "struggling": "simulate_struggling_student",
    "engaged": "simulate_engaged_student",
    "flow": "simulate_flow_state",
    "fatigued": "simulate_fatigued_student",
}


@app.post("/demo")
async def start_demo_session(scenario: str = "engaged"):
    """
    Start a pre-configured demo session instantly.

    Creates a WebcamSimulator with the given scenario and returns everything
    needed to connect. Useful for starting a live demo in seconds.

    Available scenarios: normal, struggling, engaged, flow, fatigued, distracted, confused
    """
    session_id = f"demo_{uuid.uuid4().hex[:8]}"

    sim = WebcamSimulator()
    sim.start()

    # Apply scenario
    if scenario in _DEMO_SCENARIOS:
        getattr(sim, _DEMO_SCENARIOS[scenario])()
    elif scenario == "confused":
        sim.target_attention = 0.3
        sim.target_load = 0.75
        sim.trigger_confusion_event(120)
    elif scenario == "distracted":
        sim.target_attention = 0.4
        sim.trigger_attention_dip(30)
    # "normal" uses simulator defaults

    webcam_simulators[session_id] = sim
    initial_state = sim.get_state_dict()

    return {
        "session_id": session_id,
        "scenario": scenario,
        "initial_state": initial_state,
        "available_scenarios": list(_DEMO_SCENARIOS.keys()) + ["normal", "confused", "distracted"],
        "instructions": {
            "change_scenario": f"POST /simulator/scenario/{session_id}?scenario=struggling",
            "get_state": f"GET /simulator/state/{session_id}",
            "stop": f"POST /simulator/stop/{session_id}",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
