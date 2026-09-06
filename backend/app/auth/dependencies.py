import base64
import json
from fastapi import Request
from .models import DemoUser, DEMO_USERS, DEFAULT_USER


def get_current_user(request: Request) -> DemoUser:
    """Extract current demo user from the mplads_demo_user cookie.

    The frontend stores a base64-encoded JSON of the DemoUser object
    in a cookie named 'mplads_demo_user'. This function reads and
    decodes it. If the cookie is missing or invalid, returns the
    DEFAULT_USER (ministry admin — full access).
    """
    cookie_val = request.cookies.get("mplads_demo_user")
    if not cookie_val:
        return DEFAULT_USER

    try:
        decoded = base64.b64decode(cookie_val).decode("utf-8")
        data = json.loads(decoded)
        return DemoUser(**data)
    except Exception:
        return DEFAULT_USER


def apply_scope_filters(query, model, user: DemoUser):
    """Apply jurisdiction-based WHERE clauses to a SQLAlchemy query.

    Uses the 'state', 'constituency', and 'ida' columns on the model
    to restrict data to the user's authorized scope.

    - ministry_admin: no filters (full access)
    - state_nodal: filter by model.state == user.state
    - district_authority: filter by model.ida ILIKE user.district
    - inspection_officer: filter by model.state == user.state
    - mp_user: filter by model.constituency == user.constituency
    """
    if user.role == "ministry_admin":
        return query

    if user.role in ("state_nodal", "inspection_officer") and user.state:
        return query.filter(model.state == user.state)

    if user.role == "district_authority" and user.district:
        # ida field format: "DISTRICT_NAME(DESIGNATION ...)"
        # Filter by ida starting with the district name
        return query.filter(model.ida.ilike(f"{user.district}%"))

    if user.role == "mp_user" and user.constituency:
        return query.filter(model.constituency == user.constituency)

    return query


def apply_work_scope_filters(query, user: DemoUser):
    """Apply jurisdiction filters specifically to queries on the Work model.

    This is a convenience wrapper that imports Work and calls apply_scope_filters.
    Used by routers that query the Work model directly.
    """
    from ..models.work import Work
    return apply_scope_filters(query, Work, user)


def get_scope_filter(user: DemoUser, model=None):
    """Return a list of SQLAlchemy filter conditions for the user's scope.

    Some routers build complex queries where apply_scope_filters doesn't
    fit cleanly. This function returns filter conditions as a list that
    can be added to a query with .filter(*conditions).

    If model is None, defaults to Work model.
    """
    from ..models.work import Work
    if model is None:
        model = Work

    if user.role == "ministry_admin":
        return []

    if user.role in ("state_nodal", "inspection_officer") and user.state:
        return [model.state == user.state]

    if user.role == "district_authority" and user.district:
        return [model.ida.ilike(f"{user.district}%")]

    if user.role == "mp_user" and user.constituency:
        return [model.constituency == user.constituency]

    return []
