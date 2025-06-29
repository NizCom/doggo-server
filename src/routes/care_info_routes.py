import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

care_info_routes = Blueprint('care_info_routes', __name__)


@care_info_routes.route('/api/dog/vet', methods=['PUT'])
def add_dog_vet():
    data = request.json
    dog_id = data.get("dog_id")
    update_dog_vet_query = f""" UPDATE {CARE_INFO_TABLE}
                                   SET vet_name = %(vet_name)s, vet_phone = %(vet_phone)s, 
                                   vet_latitude = %(vet_latitude)s, vet_longitude = %(vet_longitude)s
                                   WHERE {DOG_ID_COLUMN} = %(dog_id)s; """

    create_dog_vet_query = f""" INSERT INTO {CARE_INFO_TABLE} (dog_id, vet_name, vet_phone, vet_latitude, vet_longitude)
                                VALUES (%(dog_id)s, %(vet_name)s, %(vet_phone)s, %(vet_latitude)s, %(vet_longitude)s); 
                            """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                if does_exist(cursor, CARE_INFO_TABLE, DOG_ID_COLUMN, dog_id):
                    cursor.execute(update_dog_vet_query, data)
                    msg = "Vet info was updated"
                else:
                    cursor.execute(create_dog_vet_query, data)
                    msg = "Vet info was created"
                connection.commit()
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"message": msg}), HTTP_200_OK


@care_info_routes.route('/api/dog/vet', methods=['GET'])
def get_dog_vet():
    dog_id = request.args.get('dog_id')
    get_vet_query = f""" SELECT vet_name, vet_phone, vet_latitude, vet_longitude
                        FROM {CARE_INFO_TABLE} WHERE {DOG_ID_COLUMN} = %s; """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                if not does_exist(cursor, CARE_INFO_TABLE, DOG_ID_COLUMN, dog_id):
                    return "", HTTP_204_STATUS_NO_CONTENT
                cursor.execute(get_vet_query, (dog_id,))
                res = get_dict_for_response(cursor)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(res), HTTP_200_OK


@care_info_routes.route('/api/dog/pension', methods=['PUT'])
def add_dog_pension():
    data = request.json
    dog_id = data.get("dog_id")
    update_dog_pension_query = f""" UPDATE {CARE_INFO_TABLE}
                                   SET pension_name = %(pension_name)s, pension_phone = %(pension_phone)s,
                                   pension_latitude = %(pension_latitude)s, pension_longitude = %(pension_longitude)s
                                   WHERE {DOG_ID_COLUMN} = %(dog_id)s; """

    create_dog_pension_query = f""" INSERT INTO {CARE_INFO_TABLE} 
                                    (dog_id, pension_name, pension_phone, pension_latitude, pension_longitude)
                                    VALUES (%(dog_id)s, %(pension_name)s, %(pension_phone)s, 
                                    %(pension_longitude)s, %(pension_latitude)s); 
                                    """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                if does_exist(cursor, CARE_INFO_TABLE, DOG_ID_COLUMN, dog_id):
                    cursor.execute(update_dog_pension_query, data)
                    msg = "Pension info was updated"
                else:
                    cursor.execute(create_dog_pension_query, data)
                    msg = "Pension info was created"
                connection.commit()
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"message": msg}), HTTP_200_OK


@care_info_routes.route('/api/dog/pension', methods=['GET'])
def get_dog_pension():
    dog_id = request.args.get('dog_id')
    get_pension_query = f""" SELECT pension_name, pension_phone, pension_latitude, pension_longitude
                                 FROM {CARE_INFO_TABLE} WHERE {DOG_ID_COLUMN} = %s; """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                if not does_exist(cursor, CARE_INFO_TABLE, DOG_ID_COLUMN, dog_id):
                    return "", HTTP_204_STATUS_NO_CONTENT

                cursor.execute(get_pension_query, (dog_id,))
                res = get_dict_for_response(cursor)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(res), HTTP_200_OK


@care_info_routes.route('/api/dog/care_info', methods=['GET'])
def get_dog_care_info():
    dog_id = request.args.get('dog_id')
    get_dog_care_info_query = """ SELECT *
                                FROM {0}
                                WHERE {1} = %s; """.format(CARE_INFO_TABLE, DOG_ID_COLUMN)

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                if not does_exist(cursor, CARE_INFO_TABLE, DOG_ID_COLUMN, dog_id):
                    return '', HTTP_204_STATUS_NO_CONTENT
                cursor.execute(get_dog_care_info_query, (dog_id,))
                res = get_dict_for_response(cursor)
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(res), HTTP_200_OK
