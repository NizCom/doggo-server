import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

vaccinations_routes = Blueprint('vaccinations_routes', __name__)


@vaccinations_routes.route("/api/dog/vaccinations", methods=['GET'])
def get_dog_vaccinations_list():
    dog_id = request.args.get("dog_id")
    limit = request.args.get("limit", type=int)  # Number of activities to retrieve
    offset = request.args.get("offset", type=int)  # Number of activities to skip
    vaccination_type = request.args.get("vaccination_type")

    get_dog_vaccinations_query = f"""
    SELECT vaccination_id, vaccination_date, vaccination_type, dosage, vet_name, next_vaccination, notes
    FROM {VACCINATIONS_TABLE}
    WHERE {DOG_ID_COLUMN} = %s AND (%s = 'all' OR vaccination_type = %s)
    ORDER BY vaccination_date DESC
    LIMIT %s OFFSET %s;
    """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_dog_vaccinations_query, (dog_id, vaccination_type, vaccination_type, limit, offset))
                list_of_dicts = get_list_of_dicts_for_response(cursor)
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if not list_of_dicts:
        return "", HTTP_204_STATUS_NO_CONTENT

    return jsonify(list_of_dicts), HTTP_200_OK


@vaccinations_routes.route("/api/dog/vaccinations", methods=['POST'])
def add_dog_vaccination():
    data = request.json
    required_data = {"dog_id", "vaccination_date", "vaccination_type", "dosage", "vet_name"}

    add_vaccination_query = f"""
        INSERT INTO {VACCINATIONS_TABLE} 
        (dog_id, vaccination_date, vaccination_type, 
        dosage, vet_name, next_vaccination, notes)
        VALUES 
        (%(dog_id)s, %(vaccination_date)s, %(vaccination_type)s, 
        %(dosage)s, %(vet_name)s, %(next_vaccination)s, %(notes)s)
        RETURNING vaccination_id;
    """

    try:
        if not required_data.issubset(data.keys()):
            missing_fields = required_data - data.keys()
            raise MissingFieldsError(missing_fields)

        dog_id = data.get("dog_id")
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(add_vaccination_query, data)
                new_vaccination_id = cursor.fetchone()[0]
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"vaccination_id": new_vaccination_id}), HTTP_201_CREATED


@vaccinations_routes.route("/api/dog/vaccinations", methods=['PUT'])
def update_dog_vaccination():
    data = request.json
    required_data = {"vaccination_id", "vaccination_date", "vaccination_type", "dosage", "vet_name"}

    update_vaccination_query = f"""
        UPDATE {VACCINATIONS_TABLE} 
        SET vaccination_date = %(vaccination_date)s,
        vaccination_type = %(vaccination_type)s,
        dosage = %(dosage)s,
        vet_name = %(vet_name)s,
        next_vaccination = %(next_vaccination)s,
        notes = %(notes)s
        WHERE vaccination_id = %(vaccination_id)s;
    """

    try:
        if not required_data.issubset(data.keys()):
            missing_fields = required_data - data.keys()
            raise MissingFieldsError(missing_fields)

        vaccination_id = data.get("vaccination_id")
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, VACCINATIONS_TABLE, VACCINATION_ID_COLUMN, vaccination_id)
                cursor.execute(update_vaccination_query, data)
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "vaccination was updated successfully.", HTTP_200_OK


@vaccinations_routes.route("/api/dog/vaccinations", methods=['DELETE'])
def delete_dog_vaccination():
    vaccination_id = request.args.get("vaccination_id")

    delete_vaccination_query = f"""
                                DELETE FROM {VACCINATIONS_TABLE}
                                WHERE {VACCINATION_ID_COLUMN} = %s;
                                """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, VACCINATIONS_TABLE, VACCINATION_ID_COLUMN, vaccination_id)
                cursor.execute(delete_vaccination_query, (vaccination_id,))
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "vaccination was deleted successfully.", HTTP_200_OK
