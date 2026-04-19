from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

menu_service = Blueprint("menu_service", __name__)


# ============================================================
# /menu_items routes
# ============================================================

@menu_service.route("/menu_items", methods=["GET"])
def get_all_menu_items():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /menu_items')

        availability_status = request.args.get("availability_status")

        query = "SELECT * FROM menu_items WHERE 1=1"
        params = []

        if availability_status:
            query += " AND availability_status = %s"
            params.append(availability_status)

        cursor.execute(query, params)
        menu_items = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(menu_items)} menu items')
        return jsonify(menu_items), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_menu_items: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@menu_service.route("/menu_items", methods=["POST"])
def create_menu_item():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('POST /menu_items')

        data = request.get_json()

        required_fields = ["item_name", "price"]
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f'Failed to create menu item, missing required field: {field}')
                return jsonify({"error": f"Missing required field: {field}"}), 400

        columns = ["item_name", "price"]
        values = [data["item_name"], data["price"]]

        if "description" in data:
            columns.append("description")
            values.append(data["description"])
        if "availability_status" in data:
            columns.append("availability_status")
            values.append(data["availability_status"])

        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO menu_items ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(query, values)

        get_db().commit()
        current_app.logger.info(f'Created menu item successfully, menu_item_id: {cursor.lastrowid}')
        return jsonify({"message": "Menu Item created successfully", "menu_item_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_menu_item: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@menu_service.route("/menu_items/<int:menu_item_id>", methods=["PUT"])
def update_menu_item(menu_item_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'PUT /menu_items/{menu_item_id}')

        data = request.get_json()

        cursor.execute("SELECT menu_item_id FROM menu_items WHERE menu_item_id = %s", (menu_item_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Menu Item not found"}), 404

        allowed_fields = ["item_name", "description", "availability_status", "price"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(menu_item_id)
        query = f"UPDATE menu_items SET {', '.join(update_fields)} WHERE menu_item_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        current_app.logger.info(f'Updated menu item successfully, id: {menu_item_id}')
        return jsonify({"message": "Menu Item updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_menu_item: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@menu_service.route("/menu_items/<int:menu_item_id>", methods=["DELETE"])
def delete_menu_item(menu_item_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /menu_items/{menu_item_id}')

        cursor.execute("SELECT menu_item_id FROM menu_items WHERE menu_item_id = %s", (menu_item_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Menu Item not found"}), 404

        cursor.execute("DELETE FROM menu_items WHERE menu_item_id = %s", (menu_item_id,))
        get_db().commit()

        current_app.logger.info(f'Deleted menu item: {menu_item_id}')
        return jsonify({"message": "Menu Item deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in delete_menu_item: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ============================================================
# /notifications routes
# ============================================================

@menu_service.route("/notifications/<int:user_id>", methods=["GET"])
def get_user_notifications(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /notifications/{user_id}')

        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        is_read = request.args.get("is_read")

        query = "SELECT * FROM notifications WHERE user_id = %s"
        params = [user_id]

        if is_read is not None:
            query += " AND is_read = %s"
            params.append(is_read)

        cursor.execute(query, params)
        notification_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(notification_list)} notifications')
        return jsonify(notification_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_user_notifications: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@menu_service.route("/notifications", methods=["POST"])
def create_notification():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('POST /notifications')

        data = request.get_json()

        required_fields = ["user_id", "message"]
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f'Attempted create_notification missing required field: {field}')
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO notifications (user_id, message)
            VALUES (%s, %s)
        """
        cursor.execute(query, (
            data["user_id"],
            data["message"],
        ))

        get_db().commit()
        current_app.logger.info(f'Notification created successfully, id: {cursor.lastrowid}')
        return jsonify({"message": "Notification created successfully", "notification_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f'Database error in create_notification: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@menu_service.route("/notifications/<int:alert_id>", methods=["PUT"])
def update_notification(alert_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'PUT /notifications/{alert_id}')

        data = request.get_json()

        cursor.execute("SELECT alert_id FROM notifications WHERE alert_id = %s", (alert_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Notification not found"}), 404

        allowed_fields = ["message", "is_read"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(alert_id)
        query = f"UPDATE notifications SET {', '.join(update_fields)} WHERE alert_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        current_app.logger.info(f'Updated notification successfully, id: {alert_id}')
        return jsonify({"message": "Notification updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f'Database error in update_notification: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
