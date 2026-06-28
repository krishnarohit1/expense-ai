import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.database import Base, get_db
from main import app


class ExpenseRoutesTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.engine = create_engine(
            f"sqlite:///{self.temp_db.name}",
            connect_args={"check_same_thread": False},
        )
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        database.engine = self.engine
        database.SessionLocal = self.TestingSessionLocal
        Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_create_and_list_expenses(self):
        # Register and login to obtain bearer token
        self.client.post(
            "/users/register",
            json={"name": "Ada", "email": "ada@example.com", "password": "secret123"},
        )
        login = self.client.post(
            "/users/login",
            json={"email": "ada@example.com", "password": "secret123"},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = self.client.post(
            "/expenses/",
            json={
                "amount": 42.5,
                "merchant": "Coffee Shop",
                "category": "Food",
                "description": "Morning coffee",
                "type": "Expense",
            },
            headers=headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["merchant"], "Coffee Shop")
        self.assertEqual(payload["amount"], 42.5)

        list_response = self.client.get("/expenses/", headers=headers)
        self.assertEqual(list_response.status_code, 200)
        payload = list_response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(len(payload["items"]), 1)


if __name__ == "__main__":
    unittest.main()
