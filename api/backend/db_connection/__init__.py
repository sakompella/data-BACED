#------------------------------------------------------------
# This file manages the database connection for each request.
#
# get_db() returns a mysql.connector connection, creating one
# the first time it's called in a request and reusing it after.
#
# Flask's `g` object is a request-scoped store: anything placed
# in `g` lives for exactly one request and is cleaned up when
# the request ends. That cleanup is registered via init_app().
#------------------------------------------------------------
import mysql.connector
from flask import g, current_app


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['MYSQL_DATABASE_HOST'],
            user=current_app.config['MYSQL_DATABASE_USER'],
            password=current_app.config['MYSQL_DATABASE_PASSWORD'],
            database=current_app.config['MYSQL_DATABASE_DB'],
            port=current_app.config['MYSQL_DATABASE_PORT']
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def log_activity(user_id, action, details=None):
    # Writes a row to activity_log. No-op when user_id is falsy so callers
    # can pass through an optional actor without branching. Never raises —
    # logging failures must not break the primary request.
    if not user_id:
        return
    try:
        cursor = get_db().cursor()
        cursor.execute(
            "INSERT INTO activity_log (user_id, action, details) VALUES (%s, %s, %s)",
            (user_id, action, details),
        )
        get_db().commit()
        cursor.close()
    except Exception as e:
        current_app.logger.error(f"log_activity failed: {e}")


def init_app(app):
    # This registers close_db as a teardown function, meaning Flask will
    # call it automatically at the end of every request. There is no
    # connection setup here because get_db() opens the connection lazily —
    # only when a route actually needs it. init_app's only job is to make
    # sure the cleanup always happens, even if the route raises an exception.
    app.teardown_appcontext(close_db)
