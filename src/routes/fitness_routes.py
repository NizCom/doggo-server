import psycopg2
from flask import request, Blueprint, jsonify

from src.utils.config import load_database_config
from src.utils.conversion_tables import estimate_bcs
from src.utils.helpers import *
from src.utils.logger import logger

fitness_routes = Blueprint('fitness_routes', __name__)


# Endpoint from mobile
@fitness_routes.route('/api/dog/fitness', methods=['PUT'])
def fitness_from_mobile():
    dog_id = request.args.get('dog_id')
    embedded_steps = request.args.get('steps', type=int)
    today_date = date.today()

    try:
        db = load_database_config()
        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                collar_id = get_collar_from_dog(cursor, dog_id)
                update_collar_connection(cursor, collar_id, CONNECTED_TO_MOBILE)

                if does_exist_by_date(cursor, FITNESS_TABLE, DOG_ID_COLUMN, dog_id, FITNESS_DATE_COLUMN, today_date):
                    update_fitness(cursor, dog_id, embedded_steps)
                else:
                    create_fitness(cursor, dog_id, embedded_steps)

                connection.commit()

    except(Exception, psycopg2.DatabaseError, MissingFieldsError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "Fitness was updated successfully", HTTP_200_OK


# Endpoint from collar
@fitness_routes.route('/api/dog/collar_data', methods=['PUT'])
def data_from_collar():
    data = request.form.to_dict()
    required_data = {"collarID", "battery", "steps"}

    today_date = date.today()
    collar_id = data['collarID']
    battery_level = data['battery']
    embedded_steps = int(data['steps'])

    logger.debug("Values from collar: {0}".format(data))

    try:
        if not required_data.issubset(data.keys()):
            missing_fields = required_data - data.keys()
            raise MissingFieldsError(missing_fields)
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, COLLARS_TABLE, COLLAR_ID_COLUMN, collar_id)
                dog_id = get_dog_id_by_collar_id(cursor, collar_id)
                update_collar_connection(cursor, collar_id, not CONNECTED_TO_MOBILE)
                update_battery_level(cursor, collar_id, battery_level)
                if does_exist_by_date(cursor, FITNESS_TABLE, DOG_ID_COLUMN, dog_id, FITNESS_DATE_COLUMN, today_date):
                    update_fitness(cursor, dog_id, embedded_steps)
                else:
                    create_fitness(cursor, dog_id, embedded_steps)

                connection.commit()

    except(Exception, psycopg2.DatabaseError, MissingFieldsError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"message": "Data was updated"}), HTTP_200_OK


@fitness_routes.route('/api/dog/fitness', methods=['GET'])
def get_dog_fitness():
    dog_id = request.args.get('dog_id')
    fitness_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
    get_fitness_query = """
                        SELECT distance, steps, calories_burned
                        FROM {0} 
                        WHERE dog_id = %s AND fitness_date = %s;
                        """.format(FITNESS_TABLE)
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_fitness_query, (dog_id, fitness_date))
                fitness_details = cursor.fetchone()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    response = {
        "distance": 0.0,
        "steps": 0,
        "calories_burned": 0
    } if not fitness_details else {
        "distance": round(fitness_details[0], 2),
        "steps": fitness_details[1],
        "calories_burned": int(fitness_details[2])
    }

    return jsonify(response), HTTP_200_OK


@fitness_routes.route('/api/dog/bcs', methods=['GET'])
def get_dog_bcs():
    dog_id = request.args.get('dog_id')

    get_dog_properties_query =   f"""
                                    SELECT weight, gender, breed
                                    FROM {DOGS_TABLE} 
                                    WHERE {DOG_ID_COLUMN} = %s;
                                    """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_dog_properties_query, (dog_id,))
                weight, gender, breed = cursor.fetchone()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    bcs = estimate_bcs(weight, gender, breed)

    return jsonify(bcs), HTTP_200_OK
