# Complaint API

Small REST API for registering users, filing complaints, and tracking status changes. Built with FastAPI and a relational database (SQLite here; the same tables work on MySQL).

This replaces a desktop Tkinter form with an API an interviewer can call.

## What it does

- Register and log in. Login returns a token.
- Create a complaint with title, description, and priority (`low`, `medium`, `high`).
- List and fetch complaints. No token means 401.
- Change status (`open`, `in_progress`, `resolved`, `closed`).
- Every status change is a new row in `status_history`. The old status is not overwritten.
- Bad priority or unknown status returns 400.

## Run

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000 for the desk UI.  
Open http://127.0.0.1:8000/docs for the raw API page.

Example calls:

```bash
curl -X POST http://127.0.0.1:8000/register -H "Content-Type: application/json" -d "{\"username\":\"alice\",\"password\":\"secret12\"}"
curl -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" -d "{\"username\":\"alice\",\"password\":\"secret12\"}"
```

Copy the token, then:

```bash
curl -X POST http://127.0.0.1:8000/complaints -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d "{\"title\":\"Printer jam\",\"description\":\"Second floor printer is jammed\",\"priority\":\"high\"}"
```

Tests:

```bash
python test_api.py
```

## Tables

- `users` — username, password hash, role
- `complaints` — title, description, priority, current status, owner
- `status_history` — old status, new status, who changed it, when, note

## Design choices you should be able to explain

- Status history is a separate table so you can show every change, not just the latest status.
- Password is hashed. The database never stores the raw password.
- Token is required on complaint routes. Missing or bad token is 401.
- Priority and status are checked against a fixed set so junk values cannot land in the table.
- SQLite is used so the project runs with no extra server. The schema is normal relational SQL and moves to MySQL without a redesign.

## Resume line

Built a complaint tracking REST API with FastAPI and a relational database: user login, priority-based tickets, and a status-history table so each change is kept instead of overwritten. Rejected bad input and unauthenticated calls; covered the main flows with tests.
