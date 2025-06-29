import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

nutrition_routes = Blueprint('nutrition_routes', __name__)


@nutrition_routes.route("/api/dog/nutrition", methods=['GET'])
def get_dog_nutrition():
    dog_id = request.args.get('dog_id')
    db = load_database_config()
    get_dog_nutrition_query = f"SELECT * FROM {NUTRITION_TABLE} WHERE {DOG_ID_COLUMN} = %s;"

    try:
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(get_dog_nutrition_query, (dog_id,))
                dict_response = get_dict_for_response(cursor)
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if dict_response is None:
        return "", HTTP_204_STATUS_NO_CONTENT

    return jsonify(dict_response), HTTP_200_OK


@nutrition_routes.route("/api/dog/nutrition", methods=['PUT'])
def add_dog_nutrition():
    data = request.json
    db = load_database_config()
    dog_id = data.get('dog_id')

    create_nutrition_query = f"""
    INSERT INTO {NUTRITION_TABLE} (dog_id, food_brand, food_type, food_amount_grams, daily_snacks, notes)
    VALUES (%(dog_id)s, %(food_brand)s, %(food_type)s, %(food_amount_grams)s, %(daily_snacks)s, %(notes)s);
"""

    update_nutrition_query = f"""
    UPDATE {NUTRITION_TABLE}
    SET food_brand = %(food_brand)s,
        food_type = %(food_type)s,
        food_amount_grams = %(food_amount_grams)s,
        daily_snacks = %(daily_snacks)s,
        notes = %(notes)s
    WHERE dog_id = %(dog_id)s;
    """

    try:
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)

                if does_exist(cursor, NUTRITION_TABLE, DOG_ID_COLUMN, dog_id):
                    cursor.execute(update_nutrition_query, data)
                    msg = "Dog nutrition was updated."
                else:
                    cursor.execute(create_nutrition_query, data)
                    msg = "Dog nutrition was created."
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"message": msg}), HTTP_201_CREATED


@nutrition_routes.route("/api/dog/nutrition", methods=['DELETE'])
def delete_dog_nutrition():
    dog_id = request.args.get('dog_id')
    db = load_database_config()
    delete_nutrition_query = """
    DELETE FROM nutrition
    WHERE dog_id = %s;
    """

    try:
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(delete_nutrition_query, (dog_id,))
                if cursor.rowcount == 0:
                    raise DataNotFoundError(NUTRITION_TABLE, DOG_ID_COLUMN, dog_id)
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"message": "Nutrition record was successfully deleted"}), HTTP_200_OK
