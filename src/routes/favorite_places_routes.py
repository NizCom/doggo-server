import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

favorite_places_routes = Blueprint('favorite_places_routes', __name__)


@favorite_places_routes.route("/api/favorite_places", methods=['GET'])
def get_all_favorite_places():
    dog_id = request.args.get('dog_id')
    get_dog_favorite_places_query = f"SELECT * FROM {FAVORITE_PLACES_TABLE} WHERE dog_id = '{dog_id}';"
    try:
        db = load_database_config()
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(get_dog_favorite_places_query)
                dict_response = get_list_of_dicts_for_response(cursor)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if not dict_response:
        return "", HTTP_204_STATUS_NO_CONTENT

    return jsonify(dict_response), HTTP_200_OK


@favorite_places_routes.route("/api/favorite_places/by_type", methods=['GET'])
def get_all_favorite_place_by_type():
    dog_id = request.args.get('dog_id')
    place_type = request.args.get('place_type')
    get_dog_favorite_places_query = f"""SELECT * 
                                    FROM {FAVORITE_PLACES_TABLE} 
                                    WHERE dog_id = %s AND place_type = %s;"""
    try:
        db = load_database_config()
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(get_dog_favorite_places_query, (dog_id, place_type))
                dict_res = get_dict_for_response(cursor)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if dict_res is None:
        return "Favorite place not found", HTTP_204_STATUS_NO_CONTENT

    return jsonify(dict_res), HTTP_200_OK


@favorite_places_routes.route("/api/favorite_places", methods=['PUT'])
def set_favorite_place():
    data = request.json
    required_data = {"dog_id", "place_name", "place_latitude", "place_longitude", "address", "place_type"}

    insert_favorite_places_query = f"""
    INSERT INTO {FAVORITE_PLACES_TABLE} 
    (dog_id, place_name, place_latitude, place_longitude, address, place_type) 
    VALUES (%(dog_id)s, %(place_name)s, %(place_latitude)s, %(place_longitude)s, %(address)s, %(place_type)s);
    """

    delete_favorite_place_query = f"DELETE FROM {FAVORITE_PLACES_TABLE} WHERE dog_id = %s AND place_type = %s;"

    try:
        if not required_data.issubset(data.keys()):
            missing_fields = required_data - data.keys()
            raise MissingFieldsError(missing_fields)

        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(delete_favorite_place_query, (data['dog_id'], data['place_type']))
                cursor.execute(insert_favorite_places_query, data)
                connection.commit()
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "Favorite place was set successfully", HTTP_200_OK
