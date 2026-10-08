"""Complaint API.

Register, log in, create a complaint, change its status, and read the
status history. Every status change is stored as its own row.
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import hash_password, make_token, read_token, verify_password
from database import Base, engine, get_db
from models import Complaint, StatusHistory, User

PRIORITIES = {"low", "medium", "high"}
STATUSES = {"open", "in_progress", "resolved", "closed"}

app = FastAPI(title="Complaint API")
app.mount("/static", StaticFiles(directory="static"), name="static")
bearer = HTTPBearer(auto_error=False)
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return FileResponse("static/index.html")


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6, max_length=80)


class LoginIn(BaseModel):
    username: str
    password: str


class ComplaintIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    priority: str = "medium"


class StatusIn(BaseModel):
    status: str
    note: str = ""


def current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if creds is None:
        raise HTTPException(status_code=401, detail="login required")
    user_id = read_token(creds.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="invalid token")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid token")
    return user


def complaint_out(row):
    return {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "priority": row.priority,
        "status": row.status,
        "owner": row.owner.username,
        "created_at": row.created_at.isoformat(),
    }


@app.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    username = body.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="username taken")
    user = User(username=username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"id": user.id, "username": user.username}


@app.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username.strip()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="bad username or password")
    return {"token": make_token(user.id, user.username)}


@app.post("/complaints", status_code=201)
def create_complaint(body: ComplaintIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.priority not in PRIORITIES:
        raise HTTPException(status_code=400, detail="priority must be low, medium, or high")
    row = Complaint(
        title=body.title.strip(),
        description=body.description.strip(),
        priority=body.priority,
        owner_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    db.add(StatusHistory(
        complaint_id=row.id,
        old_status="-",
        new_status="open",
        changed_by=user.id,
        note="created",
    ))
    db.commit()
    return complaint_out(row)


@app.get("/complaints")
def list_complaints(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Complaint).order_by(Complaint.id.desc()).all()
    return [complaint_out(row) for row in rows]


@app.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(Complaint, complaint_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return complaint_out(row)


@app.patch("/complaints/{complaint_id}/status")
def change_status(
    complaint_id: int,
    body: StatusIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if body.status not in STATUSES:
        raise HTTPException(status_code=400, detail="unknown status")
    row = db.get(Complaint, complaint_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    if body.status == row.status:
        raise HTTPException(status_code=400, detail="status unchanged")
    old = row.status
    row.status = body.status
    db.add(StatusHistory(
        complaint_id=row.id,
        old_status=old,
        new_status=body.status,
        changed_by=user.id,
        note=body.note.strip()[:200],
    ))
    db.commit()
    db.refresh(row)
    return complaint_out(row)


@app.get("/complaints/{complaint_id}/history")
def history(complaint_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(Complaint, complaint_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return [
        {
            "old_status": item.old_status,
            "new_status": item.new_status,
            "note": item.note,
            "changed_at": item.changed_at.isoformat(),
        }
        for item in row.history
    ]
