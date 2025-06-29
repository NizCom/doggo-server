import psycopg2
from flask import Blueprint, request, jsonify, g
from src.utils.helpers import *

faq_routes = Blueprint('faq_routes', __name__)


@faq_routes.route("/api/faq/questions", methods=['GET'])
def get_faq_questions():
    get_questions_query = f"SELECT faq_id, question FROM {FAQ_TABLE};"

    try:
        with g.db_conn.cursor() as cursor:
            cursor.execute(get_questions_query)
            faq_questions = cursor.fetchall()

            # Convert the list of tuples into a dictionary
            faq_dict = {faq_id: question for faq_id, question in faq_questions}

    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(faq_dict), HTTP_200_OK


@faq_routes.route("/api/faq/answer", methods=['GET'])
def get_faq_answer():
    faq_id = request.args.get('faq_id')
    get_answer_query = f"SELECT answer FROM {FAQ_TABLE} WHERE faq_id = %s;"

    try:
        with g.db_conn.cursor() as cursor:
            cursor.execute(get_answer_query, (faq_id,))
            faq_answer = cursor.fetchone()[0]

    except (Exception, ValueError, psycopg2.DatabaseError) as error:
        return jsonify({"error": str(error)}), HTTP_400_BAD_REQUEST

    return jsonify(faq_answer), HTTP_200_OK
