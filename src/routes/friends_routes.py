import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

friends_routes = Blueprint('friends_routes', __name__)


@friends_routes.route("/api/dog/friends/add", methods=['POST'])
def add_friend():
    dog1_id = request.args.get('dog1_id') # Dog 1 is the sender
    dog2_id = request.args.get('dog2_id') # Dog 2 is the receiver

    insert_friendship_query = f"""
        INSERT INTO {FRIENDS_TABLE} (dog1_id, dog2_id)
        VALUES (%s, %s);
        """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog1_id)
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog2_id)
                cursor.execute(insert_friendship_query, (dog1_id, dog2_id))
                connection.commit()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return "", HTTP_200_OK


@friends_routes.route("/api/dog/friends/all", methods=['GET'])
def get_all_friends():
    dog_id = request.args.get('dog_id')

    get_friends_query = f"""
        SELECT
            CASE
                WHEN f.dog1_id = {dog_id} THEN f.dog2_id
                ELSE f.dog1_id
            END AS dog_id,
            CASE
                WHEN f.dog1_id = {dog_id} THEN d2.name
                ELSE d1.name
            END AS name
        FROM {FRIENDS_TABLE} f
        JOIN {DOGS_TABLE} d1 ON f.dog1_id = d1.dog_id
        JOIN {DOGS_TABLE} d2 ON f.dog2_id = d2.dog_id
        WHERE (f.dog1_id = {dog_id} OR f.dog2_id = {dog_id}) AND f.are_friends = TRUE;
    """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_friends_query)
                friends_list = get_list_of_dicts_for_response(cursor)
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    if not friends_list:
        return "", HTTP_204_STATUS_NO_CONTENT

    return jsonify(friends_list), HTTP_200_OK


@friends_routes.route("/api/dog/friends/profile", methods=['GET'])
def get_friend_profile():
    dog_id = request.args.get('dog_id')

    get_friend_details_query = f"""
        SELECT name, description, breed, gender,
            date_of_birth, weight, height
        FROM {DOGS_TABLE}
        WHERE dog_id = {dog_id};
    """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_friend_details_query)
                friend_details = get_dict_for_response(cursor)
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify(friend_details), HTTP_200_OK


@friends_routes.route('/api/dog/friends/delete', methods=['DELETE'])
def delete_dog():
    dog1_id = request.args.get('dog1_id')   # The dog who deletes
    dog2_id = request.args.get('dog2_id')

    delete_friendship_query = f"""
        DELETE FROM {FRIENDS_TABLE}
        WHERE (dog1_id = {dog1_id} AND dog2_id = {dog2_id}) OR (dog1_id = {dog2_id} AND dog2_id = {dog1_id});
    """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog1_id)
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog2_id)
                cursor.execute(delete_friendship_query)
                connection.commit()
    except(Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), 400

    return "", HTTP_200_OK


