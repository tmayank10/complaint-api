import os
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["COMPLAINT_SECRET"] = "test-secret"

import database
import main
from database import Base

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
database.engine = engine
database.SessionLocal = TestingSession
main.engine = engine
Base.metadata.create_all(bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[database.get_db] = override_db
client = TestClient(main.app)


class ApiTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def _token(self, username="alice", password="secret12"):
        self.assertEqual(client.post("/register", json={"username": username, "password": password}).status_code, 201)
        res = client.post("/login", json={"username": username, "password": password})
        self.assertEqual(res.status_code, 200)
        return res.json()["token"]

    def test_register_and_reject_duplicate(self):
        first = client.post("/register", json={"username": "alice", "password": "secret12"})
        self.assertEqual(first.status_code, 201)
        second = client.post("/register", json={"username": "alice", "password": "secret12"})
        self.assertEqual(second.status_code, 409)

    def test_complaint_requires_login(self):
        res = client.post("/complaints", json={"title": "Slow wifi", "description": "Office wifi drops"})
        self.assertEqual(res.status_code, 401)

    def test_create_and_status_history(self):
        token = self._token()
        headers = {"Authorization": "Bearer %s" % token}
        created = client.post(
            "/complaints",
            headers=headers,
            json={"title": "Printer jam", "description": "Second floor printer is jammed", "priority": "high"},
        )
        self.assertEqual(created.status_code, 201)
        complaint_id = created.json()["id"]
        self.assertEqual(created.json()["status"], "open")

        changed = client.patch(
            "/complaints/%s/status" % complaint_id,
            headers=headers,
            json={"status": "in_progress", "note": "technician assigned"},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["status"], "in_progress")

        hist = client.get("/complaints/%s/history" % complaint_id, headers=headers)
        self.assertEqual(hist.status_code, 200)
        self.assertEqual(len(hist.json()), 2)
        self.assertEqual(hist.json()[-1]["new_status"], "in_progress")

    def test_bad_priority_rejected(self):
        token = self._token()
        res = client.post(
            "/complaints",
            headers={"Authorization": "Bearer %s" % token},
            json={"title": "Bad data", "description": "This should fail", "priority": "urgent"},
        )
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
