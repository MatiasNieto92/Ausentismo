from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Agent:
    agent_id: Optional[int] = None
    acdid: Optional[str] = None
    payroll_number: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    mail: Optional[str] = None
    rut: Optional[str] = None
    site: Optional[str] = None
    status: Optional[str] = None
    hire_date: Optional[str] = None
    scheduled_hours: float = 0.0
    raw_row_json: Optional[str] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class AttendanceEvent:
    event_id: Optional[int] = None
    agent_id: Optional[int] = None
    date: Optional[str] = None
    status_code: Optional[str] = None
    status_detail: Optional[str] = None
    source: Optional[str] = None
    created_by: str = "system"

@dataclass
class LoginLogout:
    ll_id: Optional[int] = None
    agent_id: Optional[int] = None
    date: Optional[str] = None
    login_time: Optional[str] = None
    logout_time: Optional[str] = None
    duration_minutes: int = 0
    source_file: Optional[str] = None

@dataclass
class Feedback:
    feedback_id: Optional[int] = None
    agent_id: Optional[int] = None
    date: Optional[str] = None
    type: Optional[str] = None
    notes: Optional[str] = None
    created_by: str = "manual"
