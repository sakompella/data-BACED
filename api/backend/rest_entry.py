from flask import Flask
from dotenv import load_dotenv
import logging

from backend.api_utils import load_required_env
from backend.db_connection import init_app as init_db
from backend.simple.simple_routes import simple_routes
from backend.ngos.ngo_routes import ngos

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

    app.config.update(load_required_env())

    # Register the cleanup hook for the database connection.
    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    # Register the routes from each Blueprint with the app object
    # and give a url prefix to each.
    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(simple_routes)
    app.register_blueprint(ngos, url_prefix="/ngo")
    app.register_blueprint(inventory, url_prefix="/inv")
    app.register_blueprint(orders, url_prefix="/ord")
    app.register_blueprint(menu_service, url_prefix="/menu")
    app.register_blueprint(user_management, url_prefix="/user")



    return app
