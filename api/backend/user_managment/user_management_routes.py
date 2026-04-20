from flask import Blueprint, jsonify, request, current_app
from backend.api_utils import db_error_response, require_json_object
from backend.db_connection import get_db
from mysql.connector import Error

user_management = Blueprint("user_management", __name__)


@user_management.route("/users", methods=["GET"])
def get_all_users():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /user_management/users')

        role_id = request.args.get("role_id")

        query = "SELECT * FROM users WHERE 1=1"
        params = []

        if role_id:
            query += " AND role_id = %s"
            params.append(role_id)

        cursor.execute(query, params)
        user_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(user_list)} users')
        return jsonify(user_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_users: {e}')
        return db_error_response(e)
    finally:
        cursor.close()


@user_management.route("/users", methods=["POST"])
def create_user():
    cursor = None
    try:
        current_app.logger.info('POST /user_management/users')

        data, error_response = require_json_object()
        if error_response:
            return error_response

        cursor = get_db().cursor(dictionary=True)

        required_fields = ["name", "role_id"]
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Failed to create user, missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400

        if "email" in data:
            query = """
                INSERT INTO users (name, email, role_id)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (
                data["name"],
                data["email"],
                data["role_id"],
            ))
        else:
            query = """
                INSERT INTO users (name, role_id)
                VALUES (%s, %s)
            """
            cursor.execute(query, (
                data["name"],
                data["role_id"],
            ))

        get_db().commit()
        current_app.logger.info(f'Created user successfully, user_id: {cursor.lastrowid}')
        return jsonify({"message": "User created successfully", "user_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_user: {e}')
        return db_error_response(e)
    finally:
        if cursor is not None:
            cursor.close()


@user_management.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    cursor = None
    try:
        current_app.logger.info(f'PUT /user_management/users/{user_id}')

        data, error_response = require_json_object()
        if error_response:
            return error_response

        cursor = get_db().cursor(dictionary=True)

        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        allowed_fields = ["name", "email", "role_id"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        current_app.logger.info(f'Updated user successfully, id: {user_id}')
        return jsonify({"message": "User updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_user: {e}')
        return db_error_response(e)
    finally:
        if cursor is not None:
            cursor.close()


@user_management.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /user_management/users/{user_id}')

        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        get_db().commit()

        current_app.logger.info(f'Deleted user: {user_id}')
        return jsonify({"message": "User deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_user: {e}')
        return db_error_response(e)
    finally:
        cursor.close()



@user_management.route("/roles", methods=["GET"])
def get_all_roles():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /user_management/roles')

        cursor.execute("SELECT * FROM roles")
        role_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(role_list)} roles')
        return jsonify(role_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_roles: {e}')
        return db_error_response(e)
    finally:
        cursor.close()


@user_management.route("/roles/<int:role_id>", methods=["PUT"])
def update_role(role_id):
    cursor = None
    try:
        current_app.logger.info(f'PUT /user_management/roles/{role_id}')

        data, error_response = require_json_object()
        if error_response:
            return error_response

        cursor = get_db().cursor(dictionary=True)

        cursor.execute("SELECT role_id FROM roles WHERE role_id = %s", (role_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Role not found"}), 404

        allowed_fields = ["role_name", "description"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(role_id)
        query = f"UPDATE roles SET {', '.join(update_fields)} WHERE role_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        current_app.logger.info(f'Updated role successfully, id: {role_id}')
        return jsonify({"message": "Role updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_role: {e}')
        return db_error_response(e)
    finally:
        if cursor is not None:
            cursor.close()




@user_management.route("/activity_log", methods=["GET"])
def get_activity_log():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /user_management/activity_log')

        user_id = request.args.get("user_id")
        action = request.args.get("action")

        query = """
            SELECT al.log_id, al.user_id, u.name AS user_name,
                   al.action, al.action_time, al.details
            FROM activity_log al
            JOIN users u ON al.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        if user_id:
            query += " AND al.user_id = %s"
            params.append(user_id)
        if action:
            query += " AND al.action = %s"
            params.append(action)

        query += " ORDER BY al.action_time DESC"

        cursor.execute(query, params)
        log_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(log_list)} activity log entries')
        return jsonify(log_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_activity_log: {e}')
        return db_error_response(e)
    finally:
        cursor.close()
