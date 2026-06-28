import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.database import Base, get_db
from main import app


class ExpensePatchTests(unittest.TestCase):
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

    def test_patch_updates_partial_fields(self):
        self.client.post("/users/register", json={"name": "Dana", "email": "dana@example.com", "password": "pw"})
        login = self.client.post("/users/login", json={"email": "dana@example.com", "password": "pw"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        create = self.client.post("/expenses/", json={"amount": 20.0, "merchant": "StoreX", "category": "Office", "description": "Pens", "type": "Expense"}, headers=headers)
        self.assertEqual(create.status_code, 200)
        exp_id = create.json()["id"]

        patch = self.client.patch(f"/expenses/{exp_id}", json={"merchant": "StoreY"}, headers=headers)
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["merchant"], "StoreY")
        self.assertEqual(patch.json()["amount"], 20.0)


if __name__ == "__main__":
    unittest.main()
