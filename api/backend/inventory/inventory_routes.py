from flask import Blueprint, jsonify, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create Blueprint for inventory-related routes
inventory = Blueprint("inventory", __name__)


# ============================================================
# /ingredients routes
# ============================================================

# GET all ingredients (Armando 1 & 4, Charles 1 & 3 & 4, Priya 6)
@inventory.route("/ingredients", methods=["GET"])
def get_all_ingredients():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /ingredients")
        cursor.execute("""
            SELECT i.ingredient_id, i.ingredient_name, i.quantity, i.unit,
                   i.cost_per_unit, i.reorder_count, i.expiration_date,
                   s.supplier_name
            FROM ingredients i
            LEFT JOIN suppliers s ON i.supplier_id = s.supplier_id
        """)
        results = cursor.fetchall()
        return jsonify(results), 200
    except Error as e:
        current_app.logger.error(f"Error in get_all_ingredients: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# POST a new ingredient (Priya 5)
@inventory.route("/ingredients", methods=["POST"])
def add_ingredient():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f"POST /ingredients with data: {data}")

        required_fields = ["ingredient_name", "supplier_id", "unit",
                           "cost_per_unit", "quantity", "reorder_count",
                           "expiration_date"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO ingredients (ingredient_name, supplier_id, unit,
                                     cost_per_unit, quantity, reorder_count,
                                     expiration_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["ingredient_name"],
            data["supplier_id"],
            data["unit"],
            data["cost_per_unit"],
            data["quantity"],
            data["reorder_count"],
            data["expiration_date"]
        ))
        get_db().commit()
        return jsonify({"message": "Ingredient added successfully",
                        "ingredient_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f"Error in add_ingredient: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# GET a specific ingredient by ID (Armando 1 & 4, Priya 6)
@inventory.route("/ingredients/<int:ingredient_id>", methods=["GET"])
def get_ingredient(ingredient_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT i.*, s.supplier_name
            FROM ingredients i
            LEFT JOIN suppliers s ON i.supplier_id = s.supplier_id
            WHERE i.ingredient_id = %s
        """, (ingredient_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Ingredient not found"}), 404

        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# PUT update an ingredient (Armando 2, Priya 5 & 6)
@inventory.route("/ingredients/<int:ingredient_id>", methods=["PUT"])
def update_ingredient(ingredient_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f"PUT /ingredients/{ingredient_id} with data: {data}")

        cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient_id = %s",
                        (ingredient_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Ingredient not found"}), 404

        allowed_fields = ["ingredient_name", "supplier_id", "unit",
                          "cost_per_unit", "quantity", "reorder_count",
                          "expiration_date"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(ingredient_id)
        query = f"UPDATE ingredients SET {', '.join(update_fields)} WHERE ingredient_id = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "Ingredient updated successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Error in update_ingredient: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# DELETE an ingredient (Priya 5)
@inventory.route("/ingredients/<int:ingredient_id>", methods=["DELETE"])
def delete_ingredient(ingredient_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"DELETE /ingredients/{ingredient_id}")

        cursor.execute("SELECT ingredient_id FROM ingredients WHERE ingredient_id = %s",
                        (ingredient_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Ingredient not found"}), 404

        cursor.execute("DELETE FROM ingredients WHERE ingredient_id = %s",
                        (ingredient_id,))
        get_db().commit()

        return jsonify({"message": "Ingredient deleted successfully"}), 200
    except Error as e:
        current_app.logger.error(f"Error in delete_ingredient: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ============================================================
# /expected_usage routes
# ============================================================

# GET all expected usage entries (Charles 4 & 5)
@inventory.route("/expected_usage", methods=["GET"])
def get_expected_usage():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /expected_usage")
        cursor.execute("""
            SELECT eu.usage_id, eu.expected_quantity, eu.time_period,
                   eu.start_timestamp, i.ingredient_name, i.quantity AS current_quantity
            FROM expected_usage eu
            JOIN ingredients i ON eu.ingredient_id = i.ingredient_id
        """)
        results = cursor.fetchall()
        return jsonify(results), 200
    except Error as e:
        current_app.logger.error(f"Error in get_expected_usage: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# POST a new expected usage entry (Charles 5)
@inventory.route("/expected_usage", methods=["POST"])
def add_expected_usage():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        current_app.logger.info(f"POST /expected_usage with data: {data}")

        required_fields = ["ingredient_id", "expected_quantity",
                           "time_period", "start_timestamp"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO expected_usage (ingredient_id, expected_quantity,
                                        time_period, start_timestamp)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["ingredient_id"],
            data["expected_quantity"],
            data["time_period"],
            data["start_timestamp"]
        ))
        get_db().commit()
        return jsonify({"message": "Expected usage entry created",
                        "usage_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f"Error in add_expected_usage: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ============================================================
# /suppliers routes
# ============================================================

# GET all suppliers (Charles 6)
@inventory.route("/suppliers", methods=["GET"])
def get_all_suppliers():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /suppliers")
        cursor.execute("SELECT * FROM suppliers")
        results = cursor.fetchall()
        return jsonify(results), 200
    except Error as e:
        current_app.logger.error(f"Error in get_all_suppliers: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# ============================================================
# /supplier_prices routes
# ============================================================

# GET all supplier prices (Charles 6)
@inventory.route("/supplier_prices", methods=["GET"])
def get_supplier_prices():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /supplier_prices")
        cursor.execute("""
            SELECT sp.price_id, sp.previous_price, sp.current_price,
                   s.supplier_name, i.ingredient_name
            FROM supplier_prices sp
            JOIN suppliers s ON sp.supplier_id = s.supplier_id
            JOIN ingredients i ON sp.ingredient_id = i.ingredient_id
        """)
        results = cursor.fetchall()
        return jsonify(results), 200
    except Error as e:
        current_app.logger.error(f"Error in get_supplier_prices: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
