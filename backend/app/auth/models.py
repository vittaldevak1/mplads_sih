from pydantic import BaseModel
from typing import Optional


class DemoUser(BaseModel):
    id: str
    username: str
    name: str
    role: str
    state: Optional[str] = None
    district: Optional[str] = None
    constituency: Optional[str] = None


# Predefined demo accounts — same as frontend
DEMO_USERS = {
    "admin": DemoUser(
        id="1", username="admin", name="Rajesh Kumar",
        role="ministry_admin",
    ),
    "state_nodal": DemoUser(
        id="2", username="state_nodal", name="Priya Sharma",
        role="state_nodal", state="Maharashtra",
    ),
    "district": DemoUser(
        id="3", username="district", name="Amit Patel",
        role="district_authority", state="Gujarat", district="PANCH MAHALS",
    ),
    "inspector": DemoUser(
        id="4", username="inspector", name="Sunita Reddy",
        role="inspection_officer", state="Karnataka",
    ),
    "mp": DemoUser(
        id="5", username="mp", name="Dr. Arvind Mehta",
        role="mp_user", state="Uttar Pradesh", constituency="LUCKNOW",
    ),
}

# Default user when no cookie is present (ministry admin — full access)
DEFAULT_USER = DemoUser(
    id="0", username="anonymous", name="Anonymous",
    role="ministry_admin",
)
