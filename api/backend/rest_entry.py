from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import logging

from backend.db_connection import init_app as init_db

from backend.inventory.inventory_routes import inventory
from backend.orders.orders_routes import orders
from backend.menu_service.menu_service_routes import menu_service
from backend.user_managment.user_management_routes import user_management


def create_app():
    app = Flask(__name__)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('API startup')

    # Load environment variables from the .env file so they are
    # accessible via os.getenv() below.
    load_dotenv()

    # Secret key used by Flask for securely signing session cookies.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Database connection settings — values come from the .env file.
    app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USER").strip()
    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_ROOT_PASSWORD").strip()
    app.config["MYSQL_DATABASE_HOST"] = os.getenv("DB_HOST").strip()
    app.config["MYSQL_DATABASE_PORT"] = int(os.getenv("DB_PORT").strip())
    app.config["MYSQL_DATABASE_DB"] = os.getenv("DB_NAME").strip()

    # Register the cleanup hook for the database connection.
    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    @app.route("/")
    def health_check():
        return jsonify({"status": "healthy"}), 200

    # Register the routes from each Blueprint with the app object.
    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(inventory)
    app.register_blueprint(orders)
    app.register_blueprint(menu_service)
    app.register_blueprint(user_management)

    return app
