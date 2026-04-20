import os

from flask import jsonify, request
from mysql.connector import Error
from mysql.connector.errorcode import (
    ER_BAD_NULL_ERROR,
    ER_DUP_ENTRY,
    ER_NO_REFERENCED_ROW_2,
    ER_ROW_IS_REFERENCED_2,
    ER_TRUNCATED_WRONG_VALUE,
    ER_WARN_DATA_OUT_OF_RANGE,
)


def load_required_env() -> dict[str, object]:
    required_values = {
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "MYSQL_DATABASE_USER": os.getenv("DB_USER"),
        "MYSQL_DATABASE_PASSWORD": os.getenv("MYSQL_ROOT_PASSWORD"),
        "MYSQL_DATABASE_HOST": os.getenv("DB_HOST"),
        "MYSQL_DATABASE_PORT": os.getenv("DB_PORT"),
        "MYSQL_DATABASE_DB": os.getenv("DB_NAME"),
    }

    missing = [
        source_name
        for source_name, value in (
            ("SECRET_KEY", required_values["SECRET_KEY"]),
            ("DB_USER", required_values["MYSQL_DATABASE_USER"]),
            ("MYSQL_ROOT_PASSWORD", required_values["MYSQL_DATABASE_PASSWORD"]),
            ("DB_HOST", required_values["MYSQL_DATABASE_HOST"]),
            ("DB_PORT", required_values["MYSQL_DATABASE_PORT"]),
            ("DB_NAME", required_values["MYSQL_DATABASE_DB"]),
        )
        if value is None or not str(value).strip()
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {joined}")

    return {
        "SECRET_KEY": str(required_values["SECRET_KEY"]).strip(),
        "MYSQL_DATABASE_USER": str(required_values["MYSQL_DATABASE_USER"]).strip(),
        "MYSQL_DATABASE_PASSWORD": str(required_values["MYSQL_DATABASE_PASSWORD"]).strip(),
        "MYSQL_DATABASE_HOST": str(required_values["MYSQL_DATABASE_HOST"]).strip(),
        "MYSQL_DATABASE_PORT": int(str(required_values["MYSQL_DATABASE_PORT"]).strip()),
        "MYSQL_DATABASE_DB": str(required_values["MYSQL_DATABASE_DB"]).strip(),
    }


def require_json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Request body must be a JSON object."}), 400)
    return data, None


def db_error_response(error: Error):
    errno = getattr(error, "errno", None)
    if errno in {ER_BAD_NULL_ERROR, ER_TRUNCATED_WRONG_VALUE, ER_WARN_DATA_OUT_OF_RANGE}:
        return jsonify({"error": "Request contains invalid or missing field values."}), 400
    if errno in {ER_DUP_ENTRY, ER_NO_REFERENCED_ROW_2, ER_ROW_IS_REFERENCED_2}:
        return jsonify({"error": "Request conflicts with existing database records."}), 409
    return jsonify({"error": "Database operation failed."}), 500
