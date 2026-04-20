from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for NGO routes
ngos = Blueprint("ngos", __name__)


# Get all NGOs with optional filtering by country, focus area, and founding year
# Example: /ngo/ngos?country=United%20States&focus_area=Environmental%20Conservation
@ngos.route("/ngos", methods=["GET"])
def get_all_ngos():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /ngo/ngos')

        # Query parameters are added after the main part of the URL.
        # Example: http://localhost:4000/ngo/ngos?founding_year=1971
        country = request.args.get("country")
        focus_area = request.args.get("focus_area")
        founding_year = request.args.get("founding_year")

        # WHERE 1=1 lets us append AND clauses cleanly without special-casing the first filter
        query = "SELECT * FROM WorldNGOs WHERE 1=1"
        params = []

        if country:
            query += " AND Country = %s"
            params.append(country)
        if focus_area:
            query += " AND Focus_Area = %s"
            params.append(focus_area)
        if founding_year:
            query += " AND Founding_Year = %s"
            params.append(founding_year)

        cursor.execute(query, params)
        ngo_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(ngo_list)} NGOs')
        return jsonify(ngo_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_ngos: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get detailed information about a specific NGO including its projects and donors
# Example: /ngo/ngos/1
@ngos.route("/ngos/<int:ngo_id>", methods=["GET"])
def get_ngo(ngo_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM WorldNGOs WHERE NGO_ID = %s", (ngo_id,))
        ngo = cursor.fetchone()

        if not ngo:
            return jsonify({"error": "NGO not found"}), 404

        # Reuse the same cursor for the follow-up queries
        cursor.execute("SELECT * FROM Projects WHERE NGO_ID = %s", (ngo_id,))
        ngo["projects"] = cursor.fetchall()

        cursor.execute("SELECT * FROM Donors WHERE NGO_ID = %s", (ngo_id,))
        ngo["donors"] = cursor.fetchall()

        return jsonify(ngo), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new NGO
# Required fields: Name, Country, Founding_Year, Focus_Area, Website
# Example: POST /ngo/ngos with JSON body
@ngos.route("/ngos", methods=["POST"])
def create_ngo():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["Name", "Country", "Founding_Year", "Focus_Area", "Website"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO WorldNGOs (Name, Country, Founding_Year, Focus_Area, Website)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["Name"],
            data["Country"],
            data["Founding_Year"],
            data["Focus_Area"],
            data["Website"],
        ))

        get_db().commit()
        return jsonify({"message": "NGO created successfully", "ngo_id": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update an existing NGO's information
# Can update any field except NGO_ID
# Example: PUT /ngo/ngos/1 with JSON body containing fields to update
@ngos.route("/ngos/<int:ngo_id>", methods=["PUT"])
def update_ngo(ngo_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        cursor.execute("SELECT NGO_ID FROM WorldNGOs WHERE NGO_ID = %s", (ngo_id,))
        if not cursor.fetchone():
            return jsonify({"error": "NGO not found"}), 404

        # Build update query dynamically based on provided fields
        allowed_fields = ["Name", "Country", "Founding_Year", "Focus_Area", "Website"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(ngo_id)
        query = f"UPDATE WorldNGOs SET {', '.join(update_fields)} WHERE NGO_ID = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "NGO updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get all projects associated with a specific NGO
# Example: /ngo/ngos/1/projects
@ngos.route("/ngos/<int:ngo_id>/projects", methods=["GET"])
def get_ngo_projects(ngo_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT NGO_ID FROM WorldNGOs WHERE NGO_ID = %s", (ngo_id,))
        if not cursor.fetchone():
            return jsonify({"error": "NGO not found"}), 404

        cursor.execute("SELECT * FROM Projects WHERE NGO_ID = %s", (ngo_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get all donors associated with a specific NGO
# Example: /ngo/ngos/1/donors
@ngos.route("/ngos/<int:ngo_id>/donors", methods=["GET"])
def get_ngo_donors(ngo_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT NGO_ID FROM WorldNGOs WHERE NGO_ID = %s", (ngo_id,))
        if not cursor.fetchone():
            return jsonify({"error": "NGO not found"}), 404

        cursor.execute("SELECT * FROM Donors WHERE NGO_ID = %s", (ngo_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
