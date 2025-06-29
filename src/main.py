import psycopg2
from dotenv import load_dotenv
from flask import Flask, g, jsonify
from src.routes import init_routes
from src.utils.tasks import run_tasks_thread
from src.utils.db import init_db_pool, get_db_connection, release_db_connection

app = Flask(__name__)

# Load environment variables once at the start of the application
load_dotenv()

# Initialize the database pool once when the app starts
init_db_pool()

# Initialize routes
init_routes(app)

# Start thread of background tasks
run_tasks_thread()


@app.before_request
def before_request():
    try:
        # Attempt to get a connection from the pool
        g.db_conn = get_db_connection()
    except psycopg2.OperationalError as e:
        # Log the error and return a custom error response
        app.logger.error(f"Database connection error: {e}")
        return jsonify({"error": "Could not connect to the database"}), 503


@app.teardown_request
def teardown_request(exception=None):
    db_conn = getattr(g, 'db_conn', None)
    if db_conn:
        # Check if the connection is still open
        if db_conn.closed == 0:
            # Release back to the pool if the connection is valid
            release_db_connection(db_conn)
        else:
            # Close the connection if it is no longer valid
            db_conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
