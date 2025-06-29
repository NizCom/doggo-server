import psycopg2
from flask import Blueprint, request, jsonify

from src.utils.config import load_database_config
from src.utils.helpers import *

goals_routes = Blueprint('goals_routes', __name__)


@goals_routes.route("/api/dog/goal_templates/all", methods=['GET'])
def get_dog_goal_templates_list():
    dog_id = request.args.get('dog_id')
    get_dog_goal_templates_query = f""" 
                            SELECT *
                            FROM {GOAL_TEMPLATES_TABLE} 
                            WHERE {DOG_ID_COLUMN} = %s
                            ORDER BY template_id DESC
                            """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_dog_goal_templates_query, (dog_id,))
                list_of_template_dicts = get_list_of_dicts_for_response(cursor)
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if not list_of_template_dicts: # List is empty --> no templates
        return "", HTTP_204_STATUS_NO_CONTENT
    else:
        for template_dict in list_of_template_dicts:
            if template_dict["category"] != "distance":
                template_dict["target_value"] = int(template_dict["target_value"])

    return jsonify(list_of_template_dicts), HTTP_200_OK


@goals_routes.route("/api/dog/goal_templates", methods=['GET'])
def get_dog_goal_template():
    template_id = request.args.get('template_id')
    get_goal_template_query = f""" 
                            SELECT *
                            FROM {GOAL_TEMPLATES_TABLE} 
                            WHERE {TEMPLATE_ID_COLUMN} = %s
                            """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, GOAL_TEMPLATES_TABLE, TEMPLATE_ID_COLUMN, template_id)
                cursor.execute(get_goal_template_query, (template_id,))
                template_res = get_dict_for_response(cursor)
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if template_res["category"] != DISTANCE_CATEGORY:
        template_res["target_value"] = int(template_res["target_value"])

    return jsonify(template_res), HTTP_200_OK


@goals_routes.route("/api/dog/goals/all", methods=['GET'])
def get_dog_goals_list():
    dog_id = request.args.get('dog_id')
    limit = request.args.get('limit', type=int)  # Number of activities to retrieve
    offset = request.args.get('offset', type=int)  # Number of activities to skip

    get_dog_goals_query = f"""
                        SELECT goal_id, start_date, end_date, category, 
                        current_value, target_value, done, is_finished
                        FROM {GOALS_TABLE} 
                        WHERE {DOG_ID_COLUMN} = %s
                        ORDER BY start_date DESC
                        LIMIT %s OFFSET %s;
                        """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_dog_goals_query, (dog_id, limit, offset))
                list_of_goal_dicts = get_list_of_dicts_for_response(cursor)
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    if not list_of_goal_dicts: # List is empty --> no goals
        return "", HTTP_204_STATUS_NO_CONTENT
    else:
        for goal_dict in list_of_goal_dicts:
            set_goal_data_by_category(goal_dict)

    return jsonify(list_of_goal_dicts), HTTP_200_OK


@goals_routes.route("/api/dog/goals", methods=['GET'])
def get_dog_goal_log():
    goal_id = request.args.get("goal_id")
    get_dog_goal_query = f"""
                        SELECT 
                        start_date, end_date,         
                        current_value, target_value,
                        category, done, is_finished
                        FROM {GOALS_TABLE}
                        WHERE {GOAL_ID_COLUMN} = %s;
                        """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, GOALS_TABLE, GOAL_ID_COLUMN, goal_id)
                cursor.execute(get_dog_goal_query, (goal_id,))
                goal_res = get_dict_for_response(cursor)
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    set_goal_data_by_category(goal_res)

    return goal_res, HTTP_200_OK


@goals_routes.route("/api/dog/goals/add", methods=['POST'])
def add_goal_template():
    template_data = request.json
    add_goal_template_query = f"""
        INSERT INTO {GOAL_TEMPLATES_TABLE} (dog_id, target_value, frequency, category)
        VALUES (%(dog_id)s, %(target_value)s, %(frequency)s, %(category)s)
        RETURNING template_id;
        """

    if template_data['category'] == DISTANCE_CATEGORY:
        template_data['target_value'] = float(template_data['target_value'])
    else:
        template_data['target_value'] = int(template_data['target_value'])

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, template_data['dog_id'])
                delete_previous_template_if_exists(cursor, template_data['frequency'], template_data['category'])
                cursor.execute(add_goal_template_query, template_data)
                create_goal(cursor, template_data, cursor.fetchone()[0])
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "Goal template was added successfully.", HTTP_201_CREATED


@goals_routes.route("/api/dog/goals", methods=['PUT'])
def update_goal_template():
    template_id = request.args.get("template_id")
    new_target_value = request.args.get("target_value")

    update_template_query = f"""
                            UPDATE {GOAL_TEMPLATES_TABLE}
                            SET target_value = %s
                            WHERE template_id = %s;
                            """
    update_active_goal_query = f"""
                                UPDATE {GOALS_TABLE}
                                SET target_value = %s
                                WHERE template_id = %s AND is_finished = FALSE;
                                """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, GOAL_TEMPLATES_TABLE, TEMPLATE_ID_COLUMN, template_id)
                cursor.execute(update_template_query, (new_target_value, template_id))
                cursor.execute(update_active_goal_query, (new_target_value, template_id))
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "Goal template was updated successfully.", HTTP_200_OK


@goals_routes.route("/api/dog/goal_templates", methods=['DELETE'])
def delete_goal_template():
    template_id = request.args.get("template_id")

    delete_goal_template_query = f"""
        DELETE FROM {GOAL_TEMPLATES_TABLE}
        WHERE {TEMPLATE_ID_COLUMN} = %s;
    """

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                cursor.execute(delete_goal_template_query, (template_id,))
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "Goal template was deleted successfully.", HTTP_200_OK


@goals_routes.route("/api/dog/goals", methods=['DELETE'])
def delete_goal():
    goal_id = request.args.get("goal_id")
    delete_goal_query = f"DELETE FROM {GOALS_TABLE} WHERE {GOAL_ID_COLUMN} = %s;"

    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, GOALS_TABLE, GOAL_ID_COLUMN, goal_id)
                cursor.execute(delete_goal_query, (goal_id,))
                connection.commit()
    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return "Goal was deleted successfully.", HTTP_200_OK


@goals_routes.route("/api/dog/dailyStepsGoal", methods=['GET'])
def get_daily_steps_goal():
    dog_id = request.args.get("dog_id")
    today = datetime.now().date()
    target_steps = DEFAULT_TARGET_STEPS

    get_daily_steps_goal_query = f"""
                SELECT target_value
                FROM {GOALS_TABLE} 
                WHERE {DOG_ID_COLUMN} = %s AND start_date = %s AND category = 'steps';
                """
    try:
        db = load_database_config()

        with psycopg2.connect(**db) as connection:
            with connection.cursor() as cursor:
                check_if_exists(cursor, DOGS_TABLE, DOG_ID_COLUMN, dog_id)
                cursor.execute(get_daily_steps_goal_query, (dog_id, today))
                query_res = cursor.fetchone()

                if query_res is not None:
                    target_steps = int(query_res[0])

    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify({"daily_steps_goal": target_steps}), HTTP_200_OK
