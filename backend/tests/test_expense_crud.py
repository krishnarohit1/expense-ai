import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.database import Base, get_db
from main import app


class ExpenseCrudTests(unittest.TestCase):
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

    def test_crud_flow(self):
        # register & login
        self.client.post("/users/register", json={"name": "Cleo", "email": "cleo@example.com", "password": "pw"})
        login = self.client.post("/users/login", json={"email": "cleo@example.com", "password": "pw"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # create
        create = self.client.post("/expenses/", json={"amount": 10.0, "merchant": "Shop", "category": "Misc", "description": "Buy", "type": "Expense"}, headers=headers)
        self.assertEqual(create.status_code, 200)
        exp = create.json()
        exp_id = exp["id"]

        # get
        get = self.client.get(f"/expenses/{exp_id}", headers=headers)
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json()["merchant"], "Shop")

        # update
        upd = self.client.put(f"/expenses/{exp_id}", json={"amount": 15.5}, headers=headers)
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(upd.json()["amount"], 15.5)

        # delete
        rm = self.client.delete(f"/expenses/{exp_id}", headers=headers)
        self.assertEqual(rm.status_code, 200)
        self.assertEqual(rm.json()["deleted"], True)

        # confirm gone
        gone = self.client.get(f"/expenses/{exp_id}", headers=headers)
        self.assertEqual(gone.status_code, 404)


if __name__ == "__main__":
    unittest.main()
