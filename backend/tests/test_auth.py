import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.database import Base, get_db
from main import app


class AuthRoutesTests(unittest.TestCase):
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

    def test_register_and_login_user(self):
        register_response = self.client.post(
            "/users/register",
            json={"name": "Ada", "email": "ada@example.com", "password": "secret123"},
        )
        self.assertEqual(register_response.status_code, 200)
        self.assertEqual(register_response.json()["email"], "ada@example.com")

        login_response = self.client.post(
            "/users/login",
            json={"email": "ada@example.com", "password": "secret123"},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["email"], "ada@example.com")


if __name__ == "__main__":
    unittest.main()
