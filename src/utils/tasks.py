import time
from datetime import timedelta, datetime
from threading import Thread
import psycopg2

from src.utils.config import load_database_config
from src.utils.constants import *
from src.utils.helpers import get_beginning_next_month
from src.utils.logger import logger

ACTIVITY_TIME_THRESHOLD = timedelta(hours=5)
COLLAR_LAST_UPDATE_TIME_THRESHOLD = timedelta(hours=5)
LAST_STEPS_FILE_PATH = "last_date.txt"


def run_tasks_thread():
    activities_check_thread = Thread(target=start_tasks)
    activities_check_thread.start()


def start_tasks():
    while True:
        try:
            db = load_database_config()
            with psycopg2.connect(**db) as connection:
                with connection.cursor() as cursor:
                    while True:
                        check_collars_connection(cursor)
                        check_and_end_activities(cursor)
                        finish_and_set_goals(cursor)
                        connection.commit()
                        time.sleep(10)
        except (Exception, ValueError, psycopg2.DatabaseError) as error:
            logger.error(f"Error with tasks thread: {error}")
            time.sleep(10)  # Wait before retrying the entire process


######## Task 1 ########
def check_collars_connection(cursor):
    delta_query = f""" SELECT NOW() - last_update AS time_delta
                      FROM {COLLARS_TABLE}
                      WHERE collar_id = %s; """

    collar_ids = get_all_collar_ids(cursor)

    for collar_id in collar_ids:
        cursor.execute(delta_query, (collar_id[0],))
        result = cursor.fetchone()

        # If result is None --> the server never received steps from the current collar
        if result[0] is None or result[0] >= COLLAR_LAST_UPDATE_TIME_THRESHOLD:
            disconnect_collar(cursor, collar_id)


def get_all_collar_ids(cursor):
    get_collar_ids_query = f"""SELECT {COLLAR_ID_COLUMN}
                            FROM {COLLARS_TABLE};"""
    cursor.execute(get_collar_ids_query)
    collar_ids = cursor.fetchall()

    return collar_ids


def disconnect_collar(cursor, collar_id):
    disconnect_collar_query = f""" UPDATE {COLLARS_TABLE}
                              SET wifi_connected = FALSE, ble_connected = FALSE
                              WHERE {COLLAR_ID_COLUMN} = %s; """
    cursor.execute(disconnect_collar_query, (collar_id, ))


######## Task 2 ########
def check_and_end_activities(cursor):
    get_active_activities_query = f"""SELECT {ACTIVITY_ID_COLUMN}, start_time
                          FROM {ACTIVITIES_TABLE} WHERE end_time IS NULL;"""
    cursor.execute(get_active_activities_query)
    active_activities = cursor.fetchall()
    end_activities_by_time_threshold(cursor, active_activities)


def end_activities_by_time_threshold(cursor, active_activities):
    current_time = datetime.now()

    end_activity_query = f"""
                        UPDATE {ACTIVITIES_TABLE}
                        SET end_time = %s, duration = %s
                        WHERE {ACTIVITY_ID_COLUMN} = %s
                        """

    for activity in active_activities:
        activity_id, start_time = activity
        elapsed_time = current_time - start_time
        if elapsed_time >= ACTIVITY_TIME_THRESHOLD:
            end_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            duration = format_timedelta(elapsed_time)
            cursor.execute(end_activity_query, (end_time, duration, activity_id))


def format_timedelta(delta):
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Return as formatted string
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def finish_and_set_goals(cursor):
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    last_date_str = load_dates_from_file()

    if current_date_str != last_date_str:
        current_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
        finish_goals(cursor, current_date)
        set_goals(cursor, current_date)
        save_date_to_file(current_date_str)


def save_date_to_file(current_date):
    with open(LAST_STEPS_FILE_PATH, 'w') as file:
        file.write(current_date)


def load_dates_from_file():
    try:
        with open(LAST_STEPS_FILE_PATH, 'r') as file:
            date = file.readline().strip()
        return date
    except FileNotFoundError:
        print(f"File not found: last_date.txt")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def finish_goals(cursor, current_date):
    finish_goals_query = f"""
            UPDATE {GOALS_TABLE}
            SET is_finished = TRUE
            WHERE is_finished = FALSE AND end_date = %s;
            """
    cursor.execute(finish_goals_query, (current_date, ))


def set_goals(cursor, current_date):
    tomorrow_date = current_date + timedelta(days=1)
    set_goals_by_frequency(cursor, current_date, tomorrow_date, DAILY_FREQUENCY)

    if current_date.weekday() == SUNDAY:
        next_sunday_date = current_date + timedelta(days=7)
        set_goals_by_frequency(cursor, current_date, next_sunday_date, WEEKLY_FREQUENCY)

    if current_date.day == FIRST_OF_MONTH:
        next_beginning_month_date = get_beginning_next_month(current_date)
        set_goals_by_frequency(cursor, current_date, next_beginning_month_date, MONTHLY_FREQUENCY)


def set_goals_by_frequency(cursor, current_date, end_date, template_frequency):
    get_goal_template_query = f"""
        SELECT {TEMPLATE_ID_COLUMN}, {DOG_ID_COLUMN}, target_value, category 
        FROM {GOAL_TEMPLATES_TABLE}
        WHERE frequency = %s;
        """
    create_goal_query = f"""
        INSERT INTO {GOALS_TABLE} (template_id, dog_id, target_value, category, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s);
        """

    cursor.execute(get_goal_template_query, (template_frequency,))
    goal_templates = cursor.fetchall()

    for template in goal_templates:
        template = template + (current_date, end_date,)
        cursor.execute(create_goal_query, template)
