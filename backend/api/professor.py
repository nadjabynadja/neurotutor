"""
NeuroTutor - Professor Dashboard Backend
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/professor", tags=["Professor Dashboard"])

# ============== Data Models ==============

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


class CourseSummary(BaseModel):
    id: str
    name: str
    code: str
    student_count: int
    at_risk_count: int
    average_engagement: float


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


# ============== Mock Data ==============

MOCK_COURSES = {
    "1": {"id": "1", "name": "Introduction to Computer Science", "code": "CS101", "professor_id": "prof1", "students": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
    "2": {"id": "2", "name": "Data Structures & Algorithms", "code": "CS201", "professor_id": "prof1", "students": ["s2", "s3", "s4", "s9", "s10"]},
    "3": {"id": "3", "name": "Machine Learning Fundamentals", "code": "CS301", "professor_id": "prof1", "students": ["s1", "s5", "s6", "s11", "s12", "s13"]},
}

MOCK_STUDENTS = {
    "s1": {"id": "s1", "name": "Alice Johnson", "email": "alice@university.edu", "attention": 0.85, "load": 0.45, "engagement": 0.82, "sessions": 12, "avg_duration": 45.2, "last_session": "2026-02-21T14:30:00"},
    "s2": {"id": "s2", "name": "Bob Smith", "email": "bob@university.edu", "attention": 0.42, "load": 0.78, "engagement": 0.38, "sessions": 8, "avg_duration": 32.1, "last_session": "2026-02-21T10:15:00"},
    "s3": {"id": "s3", "name": "Carol Williams", "email": "carol@university.edu", "attention": 0.91, "load": 0.52, "engagement": 0.88, "sessions": 15, "avg_duration": 52.3, "last_session": "2026-02-21T09:00:00"},
    "s4": {"id": "s4", "name": "David Brown", "email": "david@university.edu", "attention": 0.35, "load": 0.85, "engagement": 0.28, "sessions": 5, "avg_duration": 18.5, "last_session": "2026-02-15T16:45:00"},
    "s5": {"id": "s5", "name": "Eva Martinez", "email": "eva@university.edu", "attention": 0.78, "load": 0.55, "engagement": 0.75, "sessions": 10, "avg_duration": 41.0, "last_session": "2026-02-20T11:30:00"},
    "s6": {"id": "s6", "name": "Frank Lee", "email": "frank@university.edu", "attention": 0.52, "load": 0.68, "engagement": 0.48, "sessions": 7, "avg_duration": 35.8, "last_session": "2026-02-18T13:20:00"},
    "s7": {"id": "s7", "name": "Grace Kim", "email": "grace@university.edu", "attention": 0.88, "load": 0.42, "engagement": 0.85, "sessions": 14, "avg_duration": 48.6, "last_session": "2026-02-21T08:15:00"},
    "s8": {"id": "s8", "name": "Henry Chen", "email": "henry@university.edu", "attention": 0.62, "load": 0.58, "engagement": 0.65, "sessions": 9, "avg_duration": 38.2, "last_session": "2026-02-19T15:00:00"},
    "s9": {"id": "s9", "name": "Ivy Patel", "email": "ivy@university.edu", "attention": 0.73, "load": 0.49, "engagement": 0.71, "sessions": 11, "avg_duration": 44.0, "last_session": "2026-02-21T16:00:00"},
    "s10": {"id": "s10", "name": "Jack Wilson", "email": "jack@university.edu", "attention": 0.28, "load": 0.92, "engagement": 0.22, "sessions": 3, "avg_duration": 12.3, "last_session": "2026-02-10T09:00:00"},
    "s11": {"id": "s11", "name": "Karen Davis", "email": "karen@university.edu", "attention": 0.81, "load": 0.47, "engagement": 0.79, "sessions": 13, "avg_duration": 46.8, "last_session": "2026-02-21T12:00:00"},
    "s12": {"id": "s12", "name": "Leo Garcia", "email": "leo@university.edu", "attention": 0.58, "load": 0.62, "engagement": 0.55, "sessions": 6, "avg_duration": 28.4, "last_session": "2026-02-17T14:30:00"},
    "s13": {"id": "s13", "name": "Maya Thompson", "email": "maya@university.edu", "attention": 0.94, "load": 0.38, "engagement": 0.92, "sessions": 18, "avg_duration": 55.1, "last_session": "2026-02-21T17:00:00"},
}


def is_at_risk(student: Dict) -> tuple:
    """Determine if student is at risk and why."""
    reasons = []
    
    if student["attention"] < 0.5:
        reasons.append("Low attention score")
    if student["load"] > 0.7:
        reasons.append("High cognitive overload")
    if student["engagement"] < 0.5:
        reasons.append("Low engagement")
    if student["sessions"] < 5:
        reasons.append("Low session count")
    
    # Check for stale sessions (more than 3 days old)
    if student.get("last_session"):
        try:
            last = datetime.fromisoformat(student["last_session"])
            if (datetime.now() - last).days > 3:
                reasons.append("Inactive for 3+ days")
        except:
            pass
    
    return len(reasons) > 0, reasons


# ============== API Endpoints ==============

@router.get("/courses", response_model=List[CourseSummary])
async def get_professor_courses(professor_id: str = "prof1"):
    """Get all courses for a professor."""
    courses = []
    for cid, course in MOCK_COURSES.items():
        students = [MOCK_STUDENTS[sid] for sid in course["students"] if sid in MOCK_STUDENTS]
        at_risk = sum(1 for s in students if is_at_risk(s)[0])
        avg_engagement = sum(s["engagement"] for s in students) / len(students) if students else 0
        
        courses.append(CourseSummary(
            id=course["id"],
            name=course["name"],
            code=course["code"],
            student_count=len(students),
            at_risk_count=at_risk,
            average_engagement=round(avg_engagement, 2)
        ))
    return courses


@router.get("/courses/{course_id}/students", response_model=List[StudentMetrics])
async def get_course_students(course_id: str):
    """Get all students in a course with their metrics."""
    if course_id not in MOCK_COURSES:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = MOCK_COURSES[course_id]
    students = []
    
    for sid in course["students"]:
        if sid not in MOCK_STUDENTS:
            continue
        
        s = MOCK_STUDENTS[sid]
        at_risk, reasons = is_at_risk(s)
        
        students.append(StudentMetrics(
            student_id=s["id"],
            student_name=s["name"],
            student_email=s["email"],
            attention_score=s["attention"],
            cognitive_load=s["load"],
            engagement_score=s["engagement"],
            sessions_count=s["sessions"],
            average_session_duration=s["avg_duration"],
            last_session=s.get("last_session"),
            is_at_risk=at_risk,
            risk_reasons=reasons
        ))
    
    return students


@router.get("/courses/{course_id}/analytics", response_model=CourseAnalytics)
async def get_course_analytics(course_id: str):
    """Get detailed analytics for a course."""
    if course_id not in MOCK_COURSES:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = MOCK_COURSES[course_id]
    students = [MOCK_STUDENTS[sid] for sid in course["students"] if sid in MOCK_STUDENTS]
    
    if not students:
        raise HTTPException(status_code=404, detail="No students in course")
    
    at_risk_count = sum(1 for s in students if is_at_risk(s)[0])
    
    # Generate mock trend data
    engagement_trend = [0.65 + random.uniform(-0.1, 0.15) for _ in range(7)]
    attention_trend = [0.70 + random.uniform(-0.1, 0.1) for _ in range(7)]
    cognitive_load_trend = [0.50 + random.uniform(-0.1, 0.1) for _ in range(7)]
    
    return CourseAnalytics(
        course_id=course_id,
        course_name=course["name"],
        total_students=len(students),
        active_students=len([s for s in students if s.get("last_session") and 
            (datetime.now() - datetime.fromisoformat(s["last_session"])).days <= 3]),
        average_attention=round(sum(s["attention"] for s in students) / len(students), 2),
        average_cognitive_load=round(sum(s["load"] for s in students) / len(students), 2),
        average_engagement=round(sum(s["engagement"] for s in students) / len(students), 2),
        at_risk_students_count=at_risk_count,
        sessions_this_week=sum(s["sessions"] for s in students) // 2,
        average_session_duration=round(sum(s["avg_duration"] for s in students) / len(students), 1),
        total_learning_hours=round(sum(s["sessions"] * s["avg_duration"] for s in students) / 60, 1),
        engagement_trend=[round(x, 2) for x in engagement_trend],
        attention_trend=[round(x, 2) for x in attention_trend],
        cognitive_load_trend=[round(x, 2) for x in cognitive_load_trend]
    )


@router.get("/students/{student_id}/history", response_model=StudentHistoryResponse)
async def get_student_history(student_id: str):
    """Get detailed history for a specific student."""
    if student_id not in MOCK_STUDENTS:
        raise HTTPException(status_code=404, detail="Student not found")
    
    s = MOCK_STUDENTS[student_id]
    at_risk, reasons = is_at_risk(s)
    
    # Generate mock session history
    sessions = []
    for i in range(min(s["sessions"], 10)):
        sessions.append(StudentSessionHistory(
            session_id=f"session_{student_id}_{i+1}",
            course_id="1",
            course_name="CS101",
            started_at=f"2026-02-{21-i:02d}T{10+i:02d}:00:00",
            ended_at=f"2026-02-{21-i:02d}T{10+i:02d}:{30 + i*5:02d}:00",
            duration_minutes=s["avg_duration"] + random.uniform(-10, 10),
            attention_score=s["attention"] + random.uniform(-0.1, 0.1),
            cognitive_load=s["load"] + random.uniform(-0.1, 0.1),
            engagement_score=s["engagement"] + random.uniform(-0.1, 0.1),
            messages_count=random.randint(5, 20)
        ))
    
    alerts = []
    if at_risk:
        alerts = [
            {"type": "warning", "message": r, "date": "2026-02-21"}
            for r in reasons
        ]
    
    return StudentHistoryResponse(
        student_id=student_id,
        student_name=s["name"],
        total_sessions=s["sessions"],
        total_learning_hours=round(s["sessions"] * s["avg_duration"] / 60, 1),
        average_attention=s["attention"],
        average_cognitive_load=s["load"],
        average_engagement=s["engagement"],
        sessions=sessions,
        at_risk_alerts=alerts
    )


@router.get("/alerts")
async def get_all_alerts(professor_id: str = "prof1"):
    """Get all at-risk alerts across all courses."""
    alerts = []
    
    for cid, course in MOCK_COURSES.items():
        for sid in course["students"]:
            if sid not in MOCK_STUDENTS:
                continue
            
            s = MOCK_STUDENTS[sid]
            at_risk, reasons = is_at_risk(s)
            
            if at_risk:
                alerts.append({
                    "student_id": sid,
                    "student_name": s["name"],
                    "student_email": s["email"],
                    "course_id": cid,
                    "course_name": course["name"],
                    "reasons": reasons,
                    "last_session": s.get("last_session")
                })
    
    return alerts
