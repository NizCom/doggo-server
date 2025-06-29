import psycopg2
from flask import Blueprint, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

other_routes = Blueprint('other_routes', __name__)


@other_routes.route("/", methods=['GET'])
def health_check():
    db = load_database_config()
    print(db)
    print("checking....")
    return "Hello DOGS !!"


@other_routes.route("/api/user/all", methods=['GET'])
def get_all_users():
    query = "SELECT * FROM {0};".format(USERS_TABLE)
    try:
        db = load_database_config()
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns_names = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns_names, row)) for row in rows]
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(result), HTTP_200_OK


@other_routes.route("/api/dog/all", methods=['GET'])
def get_all_dogs():
    query = "SELECT * FROM {0};".format(DOGS_TABLE)
    try:
        db = load_database_config()
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns_names = [desc[0] for desc in cursor.description]
                result = []
                for row in rows:
                    row_dict = dict(zip(columns_names, row))
                    if 'image' in row_dict:
                        del row_dict['image']  # Remove the 'image' key
                    result.append(row_dict)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(result), HTTP_200_OK
