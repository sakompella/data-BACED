from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db, log_activity
from mysql.connector import Error

# Create Blueprint for orders-related routes
orders = Blueprint("orders", __name__)

# ============================================================
# /kitchen_orders routes
# ============================================================

@orders.route("/kitchen_orders", methods=["GET"])
def get_all_kitchen_orders():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /kitchen_orders")
        cursor.execute("""
           SELECT ko.order_id, ko.table_id, ko.status, ko.waiter_id,
           ko.created_at, ko.filled_at, ko.notes,
           u.name AS waiter_name
           FROM kitchen_orders ko
           LEFT JOIN users u ON ko.waiter_id = u.user_id
        """)
        results = cursor.fetchall()
        return jsonify(results), 200
    except Error as e:
        current_app.logger.error(f"Error in get_all_kitchen_orders: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# ============================================================

@orders.route("/kitchen_orders", methods=["POST"])
def add_kitchen_order():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f"POST /kitchen_orders with data: {data}")

        required_fields = ["table_id", "status", "waiter_id", "created_at"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO kitchen_orders (table_id, status, waiter_id, created_at, notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["table_id"],
            data["status"],
            data["waiter_id"],
            data["created_at"],
            data.get("notes")
        ))
        get_db().commit()
        new_id = cursor.lastrowid
        log_activity(
            data.get("actor_id") or data["waiter_id"],
            "kitchen_order_created",
            f"order_id={new_id}, table_id={data['table_id']}, waiter_id={data['waiter_id']}",
        )
        return jsonify({"message": "Order added successfully",
                        "order_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Error in add_order: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# ============================================================

@orders.route("/kitchen_orders/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f"PUT /kitchen_orders/{order_id} with data: {data}")

        cursor.execute("SELECT order_id FROM kitchen_orders WHERE order_id = %s", (order_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Order not found"}), 404

        allowed_fields = ["table_id", "status", "waiter_id", "filled_at", "notes"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(order_id)
        query = f"UPDATE kitchen_orders SET {', '.join(update_fields)} WHERE order_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        changed = ", ".join(f for f in allowed_fields if f in data)
        log_activity(
            data.get("actor_id") or data.get("waiter_id"),
            "kitchen_order_updated",
            f"order_id={order_id}, fields=[{changed}]",
        )
        return jsonify({"message": "Order updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Error in update_order: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# ============================================================

@orders.route("/kitchen_orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"DELETE /kitchen_orders/{order_id}")

        cursor.execute("SELECT order_id FROM kitchen_orders WHERE order_id = %s", (order_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Order not found"}), 404

        actor_id = request.args.get("actor_id") or (request.get_json(silent=True) or {}).get("actor_id")

        cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM kitchen_orders WHERE order_id = %s", (order_id,))
        get_db().commit()

        log_activity(actor_id, "kitchen_order_deleted", f"order_id={order_id}")
        return jsonify({"message": "Order deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Error in delete_order: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# ============================================================
# /order_items routes
# ============================================================

@orders.route("/order_items/<int:order_id>", methods=["GET"])
def get_order_items(order_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /order_items/{order_id}")
        cursor.execute("""
            SELECT oi.order_item_id, oi.order_id, oi.special_notes,
                   mi.item_name, mi.price
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.menu_item_id
            WHERE oi.order_id = %s
        """, (order_id,))
        results = cursor.fetchall()
        return jsonify(results), 200
    except Error as e:
        current_app.logger.error(f"Error in get_order_items: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# ============================================================

@orders.route("/order_items", methods=["POST"])
def add_order_item():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f"POST /order_items with data: {data}")

        required_fields = ["order_id", "menu_item_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO order_items (order_id, menu_item_id, special_notes)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            data["order_id"],
            data["menu_item_id"],
            data.get("special_notes")
        ))
        get_db().commit()
        new_id = cursor.lastrowid
        log_activity(data.get("actor_id"), "order_item_created",
                     f"order_item_id={new_id}, order_id={data['order_id']}, menu_item_id={data['menu_item_id']}")
        return jsonify({"message": "Order item added successfully",
                        "order_item_id": new_id}), 201
    except Error as e:
        current_app.logger.error(f"Error in add_order_item: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# ============================================================

@orders.route("/order_items/<int:order_item_id>", methods=["PUT"])
def update_order_item(order_item_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f"PUT /order_items/{order_item_id} with data: {data}")

        cursor.execute("SELECT order_item_id FROM order_items WHERE order_item_id = %s",
                        (order_item_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Order item not found"}), 404

        allowed_fields = ["menu_item_id", "special_notes"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(order_item_id)
        query = f"UPDATE order_items SET {', '.join(update_fields)} WHERE order_item_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        changed = ", ".join(f for f in allowed_fields if f in data)
        log_activity(data.get("actor_id"), "order_item_updated",
                     f"order_item_id={order_item_id}, fields=[{changed}]")
        return jsonify({"message": "Order item updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Error in update_order_item: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# ============================================================
@orders.route("/order_items/<int:order_item_id>", methods=["DELETE"])
def delete_order_item(order_item_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"DELETE /order_items/{order_item_id}")

        cursor.execute("SELECT order_item_id FROM order_items WHERE order_item_id = %s",
                        (order_item_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Order item not found"}), 404

        actor_id = request.args.get("actor_id") or (request.get_json(silent=True) or {}).get("actor_id")

        cursor.execute("DELETE FROM order_items WHERE order_item_id = %s",
                        (order_item_id,))
        get_db().commit()

        log_activity(actor_id, "order_item_deleted", f"order_item_id={order_item_id}")
        return jsonify({"message": "Order item deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Error in delete_order_item: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()