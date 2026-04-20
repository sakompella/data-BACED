import os
import unittest
from unittest.mock import patch

from mysql.connector.errors import IntegrityError

from backend.rest_entry import create_app


REQUIRED_ENV = {
    "SECRET_KEY": "test-secret",
    "DB_USER": "root",
    "MYSQL_ROOT_PASSWORD": "password",
    "DB_HOST": "db",
    "DB_PORT": "3306",
    "DB_NAME": "RestaurantBACED",
}


class FakeCursor:
    def __init__(self, execute_error=None):
        self.execute_error = execute_error
        self.lastrowid = 123

    def execute(self, *_args, **_kwargs):
        if self.execute_error is not None:
            raise self.execute_error

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def close(self):
        return None


class FakeConnection:
    def __init__(self, execute_error=None):
        self.execute_error = execute_error

    def cursor(self, dictionary=False):
        return FakeCursor(execute_error=self.execute_error)

    def commit(self):
        return None


class ApiGuardsTestCase(unittest.TestCase):
    def test_create_app_requires_all_database_env_vars(self):
        env = REQUIRED_ENV.copy()
        env.pop("DB_PORT")

        with patch("backend.rest_entry.load_dotenv"):
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaisesRegex(RuntimeError, "DB_PORT"):
                    create_app()

    def test_create_user_rejects_null_json_body(self):
        with patch("backend.rest_entry.load_dotenv"):
            with patch.dict(os.environ, REQUIRED_ENV, clear=True):
                app = create_app()

        client = app.test_client()
        response = client.post(
            "/user/users",
            data="null",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"error": "Request body must be a JSON object."},
        )

    def test_create_user_maps_duplicate_email_to_conflict(self):
        with patch("backend.rest_entry.load_dotenv"):
            with patch.dict(os.environ, REQUIRED_ENV, clear=True):
                app = create_app()

        duplicate_error = IntegrityError(msg="Duplicate entry", errno=1062)
        client = app.test_client()

        with patch(
            "backend.user_managment.user_management_routes.get_db",
            return_value=FakeConnection(execute_error=duplicate_error),
        ):
            response = client.post(
                "/user/users",
                json={
                    "name": "Taylor Example",
                    "email": "taken@example.com",
                    "role_id": 1,
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.get_json(),
            {"error": "Request conflicts with existing database records."},
        )


if __name__ == "__main__":
    unittest.main()
