import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

collar_routes = Blueprint('collar_routes', __name__)


@collar_routes.route("/api/collar/add", methods=['PUT'])
def add_collar():
    data = request.json
    collar_id = data.get("collar_id")
    dog_id = data.get("dog_id")
    attach_dog_collar_query = f""" UPDATE {COLLARS_TABLE}
                                  SET dog_id = %s
                                  WHERE collar_id = %s; """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, COLLARS_TABLE, COLLAR_ID_COLUMN, collar_id)
                check_collar_attachment(cursor, collar_id)
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(attach_dog_collar_query, (dog_id, collar_id))
                connection.commit()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"message": "Collar {0} connected to dog {1}".format(collar_id, dog_id)}), HTTP_200_OK


@collar_routes.route("/api/collar/get", methods=['GET'])
def get_collar_id_by_dog_id():
    dog_id = request.args.get('dog_id')
    get_collar_id_query = f"SELECT collar_id FROM {COLLARS_TABLE} WHERE dog_id = %s;"

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_collar_id_query, (dog_id,))
                collar_id = cursor.fetchone()
                if not collar_id:
                    raise ValueError("There is no collar attached to this dog.")
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"collar_id": collar_id[0]}), HTTP_200_OK


@collar_routes.route("/api/collar/battery", methods=['GET'])
def get_battery_level():
    collar_id = request.args.get('collar_id')
    get_battery_level_query = f"SELECT battery_level FROM {COLLARS_TABLE} WHERE collar_id = %s;"

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, COLLARS_TABLE, COLLAR_ID_COLUMN, collar_id)
                cursor.execute(get_battery_level_query, (collar_id,))
                battery_level = cursor.fetchone()[0]
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"battery_level": battery_level}), HTTP_200_OK


@collar_routes.route("/api/collar/battery", methods=['PUT'])
def update_battery_collar():
    dog_id = request.args.get('dog_id')
    new_battery_level = request.args.get('battery_level')

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                collar_id = get_collar_from_dog(cursor, dog_id)
                update_battery_level(cursor, collar_id, new_battery_level)
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"message": "Battery level was updated successfully!"}), HTTP_200_OK


@collar_routes.route("/api/collar/availability", methods=['GET'])
def is_collar_available():
    collar_id = request.args.get('collar_id')
    get_attached_dog_query = f"SELECT {DOG_ID_COLUMN} FROM {COLLARS_TABLE} WHERE {COLLAR_ID_COLUMN} = %s;"

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, COLLARS_TABLE, COLLAR_ID_COLUMN, collar_id)
                cursor.execute(get_attached_dog_query, (collar_id, ))
                dog_id = cursor.fetchone()[0]
                is_available = dog_id is None
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"Available": is_available}), HTTP_200_OK


@collar_routes.route("/api/collar/connectionStatus", methods=['GET'])
def get_collar_connection():
    collar_id = request.args.get('collar_id')

    get_collar_connection_query = f"SELECT ble_connected, wifi_connected FROM {COLLARS_TABLE} " \
                                  f"WHERE {COLLAR_ID_COLUMN} = %s;"

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, COLLARS_TABLE, COLLAR_ID_COLUMN, collar_id)
                cursor.execute(get_collar_connection_query, (collar_id, ))
                connection = cursor.fetchone()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"ble_connected": connection[0], "wifi_connected": connection[1]}), HTTP_200_OK


@collar_routes.route("/api/collar/disconnect", methods=['PUT'])
def disconnect_collar():
    collar_id = request.args.get('collar_id')
    disconnect_collar_query =   f"""UPDATE {COLLARS_TABLE}
                                SET {DOG_ID_COLUMN} = NULL
                                WHERE {COLLAR_ID_COLUMN} = %s
                                """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, COLLARS_TABLE, COLLAR_ID_COLUMN, collar_id)
                cursor.execute(disconnect_collar_query, (collar_id,))
                connection.commit()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return "", HTTP_200_OK
