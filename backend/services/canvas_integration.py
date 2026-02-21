"""
NeuroTutor - Canvas LMS Integration

LTI 1.3 integration for Canvas LMS.
"""
import os
import json
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests


@dataclass
class CanvasConfig:
    """Canvas LMS configuration."""
    base_url: str
    client_id: str
    deployment_id: str
    secret_key: str
    account_id: int = 1


@dataclass
class CanvasUser:
    """Canvas user information."""
    canvas_user_id: str
    name: str
    email: str
    login_id: str
    roles: List[str]


@dataclass
class CanvasCourse:
    """Canvas course information."""
    course_id: str
    name: str
    code: str
    enrollment_term_id: str
    workflow_state: str


class CanvasLTI:
    """Canvas LMS integration via LTI 1.3."""
    
    def __init__(self, config: CanvasConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.token: Optional[str] = None
        self.token_expires: float = 0
    
    def _get_access_token(self, force: bool = False) -> str:
        """Get Canvas API access token."""
        if not force and self.token and time.time() < self.token_expires:
            return self.token
        
        # In production, this would use OAuth2
        # For now, use access token from environment
        self.token = os.environ.get("CANVAS_API_TOKEN", "")
        self.token_expires = time.time() + 3600
        return self.token
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Canvas API."""
        url = f"{self.base_url}/api/v1{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }
        headers.update(kwargs.pop("headers", {}))
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # ============== Course Operations ==============
    
    def get_courses(self, enrollment_type: str = "teacher") -> List[CanvasCourse]:
        """Get courses where user is enrolled."""
        courses = self._request(
            "GET", 
            f"/courses?enrollment_type={enrollment_type}&per_page=100"
        )
        return [
            CanvasCourse(
                course_id=str(c["id"]),
                name=c["name"],
                code=c.get("course_code", ""),
                enrollment_term_id=str(c.get("term_id", "")),
                workflow_state=c.get("workflow_state", "")
            )
            for c in courses
        ]
    
    def get_course(self, course_id: str) -> CanvasCourse:
        """Get a specific course."""
        course = self._request("GET", f"/courses/{course_id}")
        return CanvasCourse(
            course_id=str(course["id"]),
            name=course["name"],
            code=course.get("course_code", ""),
            enrollment_term_id=str(course.get("term_id", "")),
            workflow_state=course.get("workflow_state", "")
        )
    
    def get_course_students(self, course_id: str) -> List[CanvasUser]:
        """Get students enrolled in a course."""
        enrollments = self._request(
            "GET",
            f"/courses/{course_id}/enrollments?per_page=100"
        )
        
        students = {}
        for e in enrollments:
            if e.get("type") == "StudentEnrollment":
                u = e.get("user", {})
                uid = str(u.get("id", ""))
                if uid and uid not in students:
                    students[uid] = CanvasUser(
                        canvas_user_id=uid,
                        name=u.get("name", ""),
                        email=u.get("email", ""),
                        login_id=u.get("login_id", ""),
                        roles=["student"]
                    )
        
        return list(students.values())
    
    # ============== Assignment Operations ==============
    
    def get_assignments(self, course_id: str) -> List[Dict]:
        """Get assignments for a course."""
        return self._request(
            "GET",
            f"/courses/{course_id}/assignments?per_page=100"
        )
    
    def create_assignment(
        self, 
        course_id: str, 
        name: str,
        points_possible: float = 100,
        description: str = ""
    ) -> Dict:
        """Create an assignment in a course."""
        return self._request(
            "POST",
            f"/courses/{course_id}/assignments",
            json={
                "assignment": {
                    "name": name,
                    "points_possible": points_possible,
                    "description": description
                }
            }
        )
    
    # ============== Grade Operations ==============
    
    def submit_grade(
        self,
        course_id: str,
        assignment_id: str,
        student_id: str,
        grade: float,
        comment: str = ""
    ) -> Dict:
        """Submit a grade for a student."""
        return self._request(
            "POST",
            f"/courses/{course_id}/assignments/{assignment_id}/submissions/{student_id}",
            json={
                "submission": {
                    "posted_grade": str(grade),
                    "text_comment": comment
                }
            }
        )
    
    def get_grades(self, course_id: str, assignment_id: str) -> List[Dict]:
        """Get all grades for an assignment."""
        return self._request(
            "GET",
            f"/courses/{course_id}/assignments/{assignment_id}/submissions?per_page=100"
        )
    
    # ============== LTI Launch ==============
    
    def verify_launch_request(
        self,
        id_token: str,
        nonce: str,
        state: str
    ) -> Optional[Dict]:
        """Verify LTI 1.3 launch request."""
        # In production, this would verify JWT signature
        # For now, decode and return claims
        try:
            # Placeholder - real implementation would use PyJWT
            return {
                "sub": "canvas_user_id",
                "name": "Student Name",
                "email": "student@university.edu",
                "https://purl.imsglobal.org/spec/lti/claim/roles": [
                    "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
                ],
                "https://purl.imsglobal.org/spec/lti/claim/context": {
                    "id": "course_123",
                    "title": "Course Name"
                }
            }
        except Exception as e:
            print(f"Launch verification failed: {e}")
            return None
    
    # ============== Sync Operations ==============
    
    def sync_course(self, course_id: str) -> Dict:
        """Sync a course with NeuroTutor."""
        course = self.get_course(course_id)
        students = self.get_course_students(course_id)
        
        return {
            "course": {
                "id": course.course_id,
                "name": course.name,
                "code": course.code
            },
            "students": [
                {
                    "id": s.canvas_user_id,
                    "name": s.name,
                    "email": s.email
                }
                for s in students
            ],
            "synced_at": datetime.now().isoformat()
        }


class CanvasIntegration:
    """High-level Canvas integration for NeuroTutor."""
    
    def __init__(self, config: Optional[CanvasConfig] = None):
        self.config = config or self._load_config()
        self.lti = CanvasLTI(self.config) if self.config else None
    
    def _load_config(self) -> Optional[CanvasConfig]:
        """Load configuration from environment."""
        base_url = os.environ.get("CANVAS_BASE_URL")
        client_id = os.environ.get("CANVAS_CLIENT_ID")
        deployment_id = os.environ.get("CANVAS_DEPLOYMENT_ID")
        secret_key = os.environ.get("CANVAS_SECRET_KEY")
        
        if not all([base_url, client_id, deployment_id, secret_key]):
            return None
        
        return CanvasConfig(
            base_url=base_url,
            client_id=client_id,
            deployment_id=deployment_id,
            secret_key=secret_key
        )
    
    def is_configured(self) -> bool:
        """Check if Canvas is configured."""
        return self.lti is not None
    
    def get_neurotutor_assignments(self, course_id: str) -> List[Dict]:
        """Get NeuroTutor-specific assignments (practice sessions)."""
        if not self.lti:
            return []
        
        assignments = self.lti.get_assignments(course_id)
        return [
            a for a in assignments 
            if a.get("name", "").startswith("[NeuroTutor]")
        ]
    
    def create_practice_session(
        self,
        course_id: str,
        topic: str,
        duration_minutes: int = 30
    ) -> Dict:
        """Create a NeuroTutor practice session assignment."""
        if not self.lti:
            return {"error": "Canvas not configured"}
        
        assignment = self.lti.create_assignment(
            course_id=course_id,
            name=f"[NeuroTutor] {topic}",
            points_possible=10,
            description=f"NeuroTutor AI tutoring session on {topic}. Duration: {duration_minutes} minutes."
        )
        
        return {
            "assignment_id": assignment.get("id"),
            "assignment_name": assignment.get("name"),
            "url": f"{self.config.base_url}/courses/{course_id}/assignments/{assignment.get('id')}",
            "lti_launch_url": f"{self.config.base_url}/api/v1/lti/assignments/{assignment.get('id')}/launch"
        }
    
    def sync_student_progress(
        self,
        course_id: str,
        student_id: str,
        neurotutor_data: Dict
    ) -> Dict:
        """Sync NeuroTutor progress to Canvas gradebook."""
        if not self.lti:
            return {"error": "Canvas not configured"}
        
        # Find NeuroTutor assignment for this student
        assignments = self.get_neurotutor_assignments(course_id)
        if not assignments:
            return {"error": "No NeuroTutor assignments found"}
        
        # Calculate grade based on engagement score
        engagement = neurotutor_data.get("engagement_score", 0.5)
        grade = engagement * 10  # Convert 0-1 to 0-10
        
        # Submit grade to most recent assignment
        assignment_id = assignments[0].get("id")
        
        result = self.lti.submit_grade(
            course_id=course_id,
            assignment_id=str(assignment_id),
            student_id=student_id,
            grade=grade,
            comment=f"NeuroTutor engagement score: {engagement:.1%}"
        )
        
        return {
            "success": True,
            "student_id": student_id,
            "grade": grade,
            "comment": f"Engagement: {engagement:.1%}"
        }


# ============== Configuration Helpers ==============

CANVAS_ENV_VARS = [
    "CANVAS_BASE_URL",
    "CANVAS_CLIENT_ID", 
    "CANVAS_DEPLOYMENT_ID",
    "CANVAS_SECRET_KEY",
    "CANVAS_API_TOKEN"
]


def check_canvas_config() -> Dict:
    """Check Canvas configuration status."""
    configured = []
    missing = []
    
    for var in CANVAS_ENV_VARS:
        if os.environ.get(var):
            configured.append(var)
        else:
            missing.append(var)
    
    return {
        "configured": len(configured) > 4,  # Need all 5 for full functionality
        "configured_vars": configured,
        "missing_vars": missing,
        "required_for_lti": ["CANVAS_BASE_URL", "CANVAS_CLIENT_ID", "CANVAS_DEPLOYMENT_ID", "CANVAS_SECRET_KEY"],
        "required_for_api": ["CANVAS_BASE_URL", "CANVAS_API_TOKEN"]
    }


# Example usage
if __name__ == "__main__":
    status = check_canvas_config()
    print(f"Canvas configured: {status['configured']}")
    print(f"Missing: {status['missing_vars']}")
