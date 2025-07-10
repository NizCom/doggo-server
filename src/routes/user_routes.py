import psycopg2
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from src.utils.config import load_database_config
from src.utils.helpers import *

user_routes = Blueprint('user_routes', __name__)


@user_routes.route('/api/user/register', methods=['POST'])
def register_user():
    data = request.json
    required_data = {"email", "password", "name", "date_of_birth", "phone_number"}

    adding_new_user_query = f"""
                                INSERT INTO {USERS_TABLE} 
                                (email, password, name, date_of_birth, phone_number) VALUES 
                                (%(email)s, %(password)s, %(name)s, %(date_of_birth)s, %(phone_number)s)
                                RETURNING user_id;
                                """
    try:
        check_required_data(required_data, data)
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_email(cursor, data.get('email'))
                check_phone_number(cursor, data.get('phone_number'))
                check_date_of_birth(data.get('date_of_birth'))
                data['password'] = generate_password_hash(data['password'])
                print(data['password'])
                cursor.execute(adding_new_user_query, data)
                user_id = cursor.fetchone()[0]
                connection.commit()
    except(Exception, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"user_id": user_id}), HTTP_201_CREATED


@user_routes.route('/api/user/login', methods=['PUT'])
def login():
    data = request.json
    email_from_user = data.get('email')
    password_from_user = data.get('password')
    logging_in_query = f""" UPDATE {USERS_TABLE}
                           SET logged_in = TRUE
                           WHERE email = %s; """
    try:
        db = load_database_config()
        check_email_and_password_from_user(email_from_user, password_from_user)

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT {USER_ID_COLUMN}, password FROM {USERS_TABLE} WHERE email = %s",
                               (email_from_user,))
                user_data = cursor.fetchone()

                if user_data is None:
                    raise ValueError("User does not exist.")
                elif not check_password_hash(user_data[1], password_from_user):
                    raise ValueError("Incorrect password.")
                else:
                    cursor.execute(logging_in_query, (email_from_user,))
                    connection.commit()
                    user_id = user_data[0]
                    cursor.execute(f"SELECT dog_id FROM {USERS_DOGS_TABLE} WHERE user_id = %s", (user_id,))
                    dog_res = cursor.fetchone()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if dog_res is None: # No dog is attached to the user
        dog_id = None
    else:
        dog_id = dog_res[0]

    return jsonify({"user_id": user_id, "dog_id": dog_id}), HTTP_200_OK


@user_routes.route('/api/user/logout', methods=['PUT'])
def logout():
    user_id = request.args.get('user_id')
    logging_out_query = """ UPDATE {0}
                        SET last_activity = NOW(), logged_in = FALSE
                        WHERE user_id = %s; """.format(USERS_TABLE)
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, USERS_TABLE, USER_ID_COLUMN, user_id)
                cursor.execute(logging_out_query, (user_id,))
                connection.commit()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"message": "You're logged out!"}), HTTP_200_OK


@user_routes.route('/api/user/profile', methods=['GET'])
def get_user_info():
    user_id = request.args.get('user_id')
    get_details_query = f"""SELECT email, password, name, date_of_birth, phone_number 
                            FROM {USERS_TABLE} 
                            WHERE user_id = %s;"""

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(get_details_query, (user_id,))
                user_details = cursor.fetchone()

                if not user_details:
                    raise ValueError("User does not exist.")

    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    user_data = {
        "email": user_details[0],
        "password": user_details[1],
        "name": user_details[2],
        "date_of_birth": user_details[3],
        "phone_number": user_details[4]
    }

    return jsonify(user_data), HTTP_200_OK


@user_routes.route('/api/user/profile', methods=['PUT'])
def update_user_info():
    data = request.json
    user_id = data.get("user_id")

    update_details_without_password_query = f"""
                            UPDATE {USERS_TABLE}
                            SET email = %(email)s, name = %(name)s,
                            date_of_birth = %(date_of_birth)s, phone_number = %(phone_number)s
                            WHERE user_id = %(user_id)s;
                            """

    update_details_with_password_query = f"""
                            UPDATE {USERS_TABLE}
                            SET email = %(email)s, password = %(password)s, name = %(name)s,
                            date_of_birth = %(date_of_birth)s, phone_number = %(phone_number)s
                            WHERE user_id = %(user_id)s;
                            """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, USERS_TABLE, USER_ID_COLUMN, user_id)
                if len(data['password']) == 0:
                    cursor.execute(update_details_without_password_query, data)
                else:
                    data['password'] = generate_password_hash(data['password'])
                    cursor.execute(update_details_with_password_query, data)
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"message": "Profile is updated!"}), HTTP_200_OK


@user_routes.route('/api/user/profile', methods=['DELETE'])
def delete_user():
    user_id = request.args.get('user_id')
    delete_user_query = f"DELETE FROM {USERS_TABLE} WHERE {USER_ID_COLUMN} = %s;"

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, USERS_TABLE, USER_ID_COLUMN, user_id)
                delete_user_dogs(cursor, user_id)
                cursor.execute(delete_user_query, (user_id,))
                connection.commit()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"message": "user '{0}' was successfully deleted".format(user_id)}), HTTP_200_OK


@user_routes.route('/api/user/connection', methods=['GET'])
def is_user_connected():
    user_id = request.args.get('user_id')
    connection_user_query = "SELECT logged_in FROM {0} WHERE {1} = %s;".format(USERS_TABLE, USER_ID_COLUMN)

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, USERS_TABLE, USER_ID_COLUMN, user_id)
                cursor.execute(connection_user_query, (user_id,))
                is_connected = cursor.fetchone()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"user_connection": is_connected[0]}), HTTP_200_OK


@user_routes.route('/api/user/check_password', methods=['GET'])
def check_password():
    user_id = request.args.get('user_id')
    password = request.args.get('password')

    get_hash_password = f"SELECT password FROM {USERS_TABLE} WHERE {USER_ID_COLUMN} = %s;"

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, USERS_TABLE, USER_ID_COLUMN, user_id)
                cursor.execute(get_hash_password, (user_id,))
                hash_password = cursor.fetchone()[0]
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    is_password_valid = check_password_hash(hash_password, password)

    return jsonify({"is_valid": is_password_valid}), HTTP_200_OK
