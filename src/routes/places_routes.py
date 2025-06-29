import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

places_routes = Blueprint('places_routes', __name__)


@places_routes.route("/api/places/all", methods=['GET'])
def get_all_places():
    all_places_query = "SELECT * FROM {0};".format(PLACES_TABLE)
    try:
        db = load_database_config()
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(all_places_query)
                dict_response = get_list_of_dicts_for_response(cursor)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(dict_response), HTTP_200_OK


@places_routes.route("/api/places/by_type", methods=['GET'])
def get_places_by_type():
    place_type = request.args.get('place_type')
    all_places_query = "SELECT * FROM {0};".format(PLACES_TABLE)
    get_places_by_type_query = f"SELECT * FROM {PLACES_TABLE} WHERE place_type = '{place_type}';"

    try:
        db = load_database_config()
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                if place_type == "ALL":
                    cursor.execute(all_places_query)
                    response = cursor.fetchall()
                else:
                    cursor.execute(get_places_by_type_query)
                    response = get_list_of_dicts_for_response(cursor)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(response), HTTP_200_OK
