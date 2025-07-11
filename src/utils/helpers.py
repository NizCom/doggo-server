import re
from calendar import monthrange
from datetime import date, timedelta, datetime

from src.utils.constants import *
from src.utils.conversion_tables import get_burned_calories, \
    get_converted_steps, get_calculated_distance
from src.utils.exceptions import *
from src.utils.logger import logger


def check_required_data(required_data, received_data):
    if not required_data.issubset(received_data.keys()):
        missing_fields = required_data - received_data.keys()
        raise MissingFieldsError(missing_fields)


def is_in_use(cursor, query, data_to_check):
    cursor.execute(query, (data_to_check,))
    return cursor.fetchone()[0] > 0


def check_email_and_password_from_user(email_from_user, password_from_user):
    if not email_from_user:
        raise MissingFieldsError({"email"})
    elif not password_from_user:
        raise MissingFieldsError({"password"})


def check_if_exists(cursor, table_to_check, column_to_check, data_to_check):
    if not does_exist(cursor, table_to_check, column_to_check, data_to_check):
        raise DataNotFoundError(table_to_check, column_to_check, data_to_check)


def does_exist(cursor, table_to_check, column_to_check, data_to_check):
    cursor.execute("SELECT COUNT(*) FROM {0} WHERE {1} = %s".format(table_to_check, column_to_check), (data_to_check,))
    exists = cursor.fetchone()[0]
    return exists


def does_exist_by_date(cursor, table_to_check, column1_to_check, data1_to_check, column2_to_check, data2_to_check):
    cursor.execute(f"SELECT COUNT(*) FROM {table_to_check} WHERE {column1_to_check} = %s and {column2_to_check} = %s",
                   (data1_to_check, data2_to_check))
    exists = cursor.fetchone()[0]

    return exists


def update_fitness(cursor, dog_id, embedded_steps):
    update_fitness_query = f"""
        UPDATE {FITNESS_TABLE}
        SET {STEPS_COLUMN} = {STEPS_COLUMN} + %s, 
            {DISTANCE_COLUMN} = {DISTANCE_COLUMN} + %s, 
            {CALORIES_COLUMN} = {CALORIES_COLUMN} + %s
        WHERE {DOG_ID_COLUMN} = %s AND {FITNESS_DATE_COLUMN} = %s;
    """

    today_date = date.today()
    dog_weight, dog_height = get_dog_weight_and_height(cursor, dog_id)
    # dog_weight, dog_breed = get_dog_weight_and_breed(cursor, dog_id)

    fixed_steps = fix_steps_before_update(cursor, dog_id, embedded_steps)
    save_last_steps(cursor, dog_id, embedded_steps)
    steps_to_db = get_converted_steps(dog_weight, fixed_steps)

    if steps_to_db != 0:
        distance_to_db = get_calculated_distance(steps_to_db, dog_weight)
        calories_to_db = get_burned_calories(dog_weight, distance_to_db)
        cursor.execute(update_fitness_query, (steps_to_db, distance_to_db, calories_to_db, dog_id, today_date))
        update_dog_activity(cursor, dog_id, steps_to_db, distance_to_db, calories_to_db)
        update_dog_goals(cursor, dog_id, steps_to_db, distance_to_db, calories_to_db)


def create_fitness(cursor, dog_id, embedded_steps):
    create_fitness_query = f""" INSERT INTO {FITNESS_TABLE} ({DOG_ID_COLUMN}, {FITNESS_DATE_COLUMN}, 
                                {DISTANCE_COLUMN}, {STEPS_COLUMN}, {CALORIES_COLUMN})
                                VALUES (%s, %s, %s, %s, %s); """
    today_date = date.today()
    dog_weight, dog_height = get_dog_weight_and_height(cursor, dog_id)

    fixed_steps = fix_steps_before_create(cursor, dog_id, embedded_steps)
    save_last_steps(cursor, dog_id, embedded_steps)

    steps_to_db = get_converted_steps(dog_weight, fixed_steps)
    distance_to_db = get_calculated_distance(steps_to_db, dog_weight)
    calories_to_db = get_burned_calories(dog_weight, distance_to_db)

    cursor.execute(create_fitness_query, (dog_id, today_date, distance_to_db, steps_to_db, calories_to_db))
    update_dog_activity(cursor, dog_id, steps_to_db, distance_to_db, calories_to_db)
    update_dog_goals(cursor, dog_id, steps_to_db, distance_to_db, calories_to_db)


def update_dog_goals(cursor, dog_id, steps_to_db, distance_to_db, calories_to_db):
    update_steps_goals(cursor, dog_id, steps_to_db)
    update_distance_goals(cursor, dog_id, distance_to_db)
    update_calories_goals(cursor, dog_id, calories_to_db)
    finish_completed_goals(cursor, dog_id)


def update_steps_goals(cursor, dog_id, steps_to_db):
    update_steps_goals_query = f"""
    UPDATE {GOALS_TABLE}
    SET current_value = current_value + %s
    WHERE {DOG_ID_COLUMN} = %s AND category = %s AND done = FALSE;
    """
    cursor.execute(update_steps_goals_query, (steps_to_db, dog_id, STEPS_CATEGORY))


def update_distance_goals(cursor, dog_id, distance_to_db):
    update_distance_goals_query = f"""
    UPDATE {GOALS_TABLE}
    SET current_value = current_value + %s
    WHERE {DOG_ID_COLUMN} = %s AND category = %s AND done = FALSE;
    """

    cursor.execute(update_distance_goals_query, (distance_to_db, dog_id, DISTANCE_CATEGORY))


def update_calories_goals(cursor, dog_id, calories_to_db):
    update_calories_goals_query = f"""
    UPDATE {GOALS_TABLE}
    SET current_value = current_value + %s
    WHERE {DOG_ID_COLUMN} = %s AND category = %s AND done = FALSE;
    """

    cursor.execute(update_calories_goals_query, (calories_to_db, dog_id, CALORIES_BURNED_CATEGORY))


def finish_completed_goals(cursor, dog_id):
    finish_completed_goals_query = f"""
    UPDATE {GOALS_TABLE}
    SET done = TRUE, is_finished = TRUE
    WHERE {DOG_ID_COLUMN} = %s 
    AND CAST(target_value AS FLOAT) <= CAST(current_value AS FLOAT)
    AND is_finished = FALSE;
    """

    cursor.execute(finish_completed_goals_query, (dog_id, ))


def update_battery_level(cursor, collar_id, new_level):
    update_battery_level_query = """
                                 UPDATE {0}
                                 SET battery_level = %s
                                 WHERE {1} = %s;
                                 """.format(COLLARS_TABLE, COLLAR_ID_COLUMN)
    cursor.execute(update_battery_level_query, (int(new_level), collar_id))


def get_dog_id_by_collar_id(cursor, collar_id):
    get_dog_id_query = "SELECT {0} FROM {1} WHERE {2} = %s;".format(DOG_ID_COLUMN, COLLARS_TABLE, COLLAR_ID_COLUMN)
    cursor.execute(get_dog_id_query, (collar_id,))
    dog_id = cursor.fetchone()

    if not dog_id:
        raise ValueError("There is no collar attached to this dog.")
    else:
        return dog_id[0]


def get_collar_from_dog(cursor, dog_id):
    get_collar_id_query = "SELECT {0} FROM {1} WHERE {2} = %s;".format(COLLAR_ID_COLUMN, COLLARS_TABLE, DOG_ID_COLUMN)
    cursor.execute(get_collar_id_query, (dog_id,))
    collar_id = cursor.fetchone()

    if not collar_id:
        raise ValueError("There is no collar attached to this dog.")
    else:
        return collar_id[0]


def get_dict_for_response(cursor):
    data_from_query = cursor.fetchone()
    res = None

    if data_from_query is not None:
        columns_names = [desc[0] for desc in cursor.description]
        res = dict(zip(columns_names, data_from_query))

    return res


def get_list_of_dicts_for_response(cursor):
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]

    list_of_dicts = [
        dict(zip(column_names, row)) for row in rows
    ]

    return list_of_dicts


def update_collar_connection(cursor, collar_id, connection):
    # If connected to mobile --> ble = True
    # else (connected to collar) --> wifi = True

    update_connection_query = f""" UPDATE {COLLARS_TABLE}
                                  SET wifi_connected = %s, ble_connected = %s, last_update = NOW()
                                  WHERE collar_id = %s; """
    cursor.execute(update_connection_query, (not connection, connection, collar_id))


def check_collar_attachment(cursor, collar_id):
    get_attachment_status_query = f"SELECT {DOG_ID_COLUMN} FROM {COLLARS_TABLE} WHERE {COLLAR_ID_COLUMN} = %s;"
    cursor.execute(get_attachment_status_query, (collar_id,))
    dog_id = cursor.fetchone()[0]
    is_attached = dog_id is not None

    if is_attached:
        raise ValueError("Collar is attached to a dog already.")


def get_dog_weight_and_height(cursor, dog_id):
    get_dog_weight_query = f"""
        SELECT {WEIGHT_COLUMN}, {HEIGHT_COLUMN}
        FROM {DOGS_TABLE}
        WHERE {DOG_ID_COLUMN} = %s;
    """

    cursor.execute(get_dog_weight_query, (dog_id, ))

    return cursor.fetchone()


def update_dog_activity(cursor, dog_id, steps_to_db, distance_to_db, calories_to_db):

    add_fitness_data_to_active_activity_query = f"""
    UPDATE {ACTIVITIES_TABLE}
    SET {STEPS_COLUMN} = {STEPS_COLUMN} + %s, 
        {DISTANCE_COLUMN} = {DISTANCE_COLUMN} + %s, 
        {CALORIES_COLUMN} = {CALORIES_COLUMN} + %s
    WHERE duration IS NULL AND {DOG_ID_COLUMN} = %s;
    """

    cursor.execute(add_fitness_data_to_active_activity_query,
                   (steps_to_db, distance_to_db, calories_to_db, dog_id))


def check_for_active_activity(cursor, dog_id):
    get_active_activity_count =   f"""
                            SELECT COUNT(*) 
                            FROM {ACTIVITIES_TABLE} 
                            WHERE {DOG_ID_COLUMN} = %s AND end_time IS NULL
                            ;"""

    cursor.execute(get_active_activity_count, (dog_id,))
    activities_count = cursor.fetchone()[0]

    if activities_count != 0:
        raise ActiveActivityExistsError()


def fix_steps_before_create(cursor, dog_id, new_steps):
    last_steps = load_last_steps(cursor, dog_id)

    if last_steps <= new_steps:
        fixed_steps = new_steps - last_steps
    else:   # Can happen because of BLE overflow or embedded was off
        fixed_steps = new_steps

    return fixed_steps


def fix_steps_before_update(cursor, dog_id, new_steps):
    # # Get the battery level
    # get_battery_level_query = f"SELECT battery_level FROM {COLLARS_TABLE} WHERE collar_id = %s;"
    # collar_id = get_collar_from_dog(cursor, dog_id)
    # cursor.execute(get_battery_level_query, (collar_id,))
    # battery_level_result = cursor.fetchone()[0]

    last_steps = load_last_steps(cursor, dog_id)

    logger.debug("Last steps loaded: {0}".format(last_steps))

    # if last_steps > new_steps and battery_level_result < BATTERY_THRESHOLD:  # Battery was off
    if last_steps > new_steps: # Battery was off
        fixed_steps = new_steps
    # elif last_steps > new_steps:      # Overflow because of Arduino
    #     converted_collar_count_limit = get_converted_steps(dog_weight, COLLAR_FITNESS_COUNT_LIMIT)
    #     fixed_fitness_to_db = new_steps + converted_collar_count_limit - last_steps
    #     logger.debug("Fixed after BLE LIMIT: {0}".format(fixed_fitness_to_db))
    elif last_steps == new_steps:
        fixed_steps = 0
    else:   # last_steps < new_steps
        fixed_steps = new_steps - last_steps
        logger.debug("Fixed after 'else': {0}".format(fixed_steps))

    return fixed_steps


def save_last_steps(cursor, dog_id, current_steps):
    update_last_steps_query = f"""
    UPDATE {DOGS_TABLE}
    SET last_steps = %s
    WHERE {DOG_ID_COLUMN} = %s;
    """

    cursor.execute(update_last_steps_query, (current_steps, dog_id))


def load_last_steps(cursor, dog_id):
    get_last_steps_query = f"""
    SELECT last_steps
    FROM {DOGS_TABLE}
    WHERE {DOG_ID_COLUMN} = %s;
    """

    cursor.execute(get_last_steps_query, (dog_id, ))
    
    result = cursor.fetchone()
    return int(result[0]) if result and result[0] is not None else 0


def delete_user_dogs(cursor, user_id):
    get_dogs_query = f"SELECT {DOG_ID_COLUMN} FROM {USERS_DOGS_TABLE} WHERE {USER_ID_COLUMN} = %s;"
    delete_dog_query = f"DELETE FROM {DOGS_TABLE} WHERE {DOG_ID_COLUMN} = %s;"

    cursor.execute(get_dogs_query, (user_id,))
    dogs = cursor.fetchall()

    for dog in dogs:
        dog_id = dog[0]
        disconnect_dog_from_collar(cursor, dog_id)
        cursor.execute(delete_dog_query, (dog_id,))


def set_goal_data_by_category(goal):
    if goal["category"] != DISTANCE_CATEGORY:
        goal["current_value"] = int(goal["current_value"])
        goal["target_value"] = int(goal["target_value"])
    else:
        goal["current_value"] = round(goal["current_value"], 2)
        goal["target_value"] = round(goal["target_value"], 2)


def get_day_record_map(cursor, month, year):
    records = cursor.fetchall()
    total_days_in_month = monthrange(int(year), int(month))[1]
    day_record_map = {day: False for day in range(1, total_days_in_month + 1)}

    for record in records:
        day = int(record[0])  # Extract the day number from the result
        day_record_map[day] = True

    return day_record_map


def create_goal(cursor, template_data, template_id):
    insert_goal_query = f"""
        INSERT INTO {GOALS_TABLE} (dog_id, start_date, end_date, current_value, 
        target_value, category, template_id, is_finished, done)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
    initial_fitness = get_initial_fitness_for_goal(cursor, template_data['dog_id'], template_data['frequency'],
                                                   template_data['category'])

    # If the dog passed already the target_value --> the goal is completed already.
    is_completed = initial_fitness >= template_data['target_value']
    goal_start_date, goal_end_date = get_start_and_end_date(template_data['frequency'])

    cursor.execute(insert_goal_query, (template_data['dog_id'], goal_start_date, goal_end_date, initial_fitness,
                                       template_data['target_value'], template_data['category'], template_id,
                                       is_completed, is_completed))


def get_initial_fitness_for_goal(cursor, dog_id, frequency, category):
    if frequency == DAILY_FREQUENCY:
        initial_fitness = get_today_fitness_category(cursor, dog_id, category)
    elif frequency == WEEKLY_FREQUENCY:
        initial_fitness = get_weekly_fitness_category(cursor, dog_id, category)
    else:   # frequency == MONTHLY_FREQUENCY
        initial_fitness = get_monthly_fitness_category(cursor, dog_id, category)

    if category != DISTANCE_CATEGORY:
        initial_fitness = int(initial_fitness)
    else:
        initial_fitness = round(initial_fitness, 2)

    return initial_fitness


def get_today_fitness_category(cursor, dog_id, category):
    get_current_fitness_category_query = f"""
            SELECT {category} FROM {FITNESS_TABLE}
            WHERE {DOG_ID_COLUMN} = %s AND {FITNESS_DATE_COLUMN} = CURRENT_DATE
            """
    cursor.execute(get_current_fitness_category_query, (dog_id,))
    query_res = cursor.fetchone()

    if query_res is not None:
        daily_fitness = query_res[0]
    else:
        daily_fitness = 0

    return daily_fitness


def get_weekly_fitness_category(cursor, dog_id, category):
    last_sunday_date = get_last_sunday_date(datetime.today().date())
    total_fitness = 0

    get_weekly_fitness_category_query = f"""
        SELECT {category} 
        FROM {FITNESS_TABLE}
        WHERE {DOG_ID_COLUMN} = %s
        AND {FITNESS_DATE_COLUMN} >= %s;
    """

    cursor.execute(get_weekly_fitness_category_query, (dog_id, last_sunday_date))
    fitness_window = cursor.fetchall()

    if fitness_window:
        total_fitness = sum(fitness for (fitness,) in fitness_window)

    return total_fitness


def get_monthly_fitness_category(cursor, dog_id, category):
    total_fitness = 0

    get_monthly_fitness_category_query = f"""
        SELECT {category} FROM {FITNESS_TABLE}
        WHERE {DOG_ID_COLUMN} = %s
        AND {FITNESS_DATE_COLUMN} >= date_trunc('month', CURRENT_DATE)
        """

    cursor.execute(get_monthly_fitness_category_query, (dog_id,))
    fitness_window = cursor.fetchall()

    if fitness_window:
        total_fitness = sum(fitness for (fitness,) in fitness_window)

    return total_fitness


def get_start_and_end_date(frequency):
    start_date = get_start_date_by_frequency(frequency)
    end_date = get_end_date_by_frequency(frequency)

    return start_date, end_date


def get_start_date_by_frequency(frequency):
    today = datetime.today().date()
    start_date = None

    if frequency == DAILY_FREQUENCY:
        start_date = today
    elif frequency == WEEKLY_FREQUENCY:
        start_date = get_last_sunday_date(today)
    elif frequency == MONTHLY_FREQUENCY:
        start_date = today.replace(day=1)

    return start_date


def get_end_date_by_frequency(frequency):
    today = datetime.today().date()
    end_date = None

    if frequency == DAILY_FREQUENCY:
        end_date = today + timedelta(days=1)
    elif frequency == WEEKLY_FREQUENCY:
        if today.weekday() == SUNDAY:  # If today is Sunday (Sunday is day 6)
            end_date = today + timedelta(7)  # Set end_date to next Sunday
        else:
            end_date = today + timedelta(6 - today.weekday())  # Set to the upcoming Sunday
    elif frequency == MONTHLY_FREQUENCY:
        end_date = get_beginning_next_month(today)

    return end_date


def get_last_sunday_date(today):
    days_since_sunday = today.weekday()  # weekday() gives 0 for Monday, 6 for Sunday
    last_sunday_date = today - timedelta(days=(days_since_sunday + 1) % 7)  # Returns last Sunday

    return last_sunday_date


def delete_goal_from_template(cursor, template_id):

    delete_active_goal_query = f"""
        DELETE FROM {GOALS_TABLE} 
        WHERE {TEMPLATE_ID_COLUMN} = %s AND is_finished = FALSE;
        """

    cursor.execute(delete_active_goal_query, (template_id,))


def delete_previous_template_if_exists(cursor, frequency, category):
    # Deleting an existing template with the same frequency and category to avoid duplication
    delete_same_goal_template_query = f"""
                DELETE FROM {GOAL_TEMPLATES_TABLE}
                WHERE frequency = %s AND category = %s
                RETURNING {TEMPLATE_ID_COLUMN};
                """
    cursor.execute(delete_same_goal_template_query, (frequency, category))
    query_res = cursor.fetchone()

    if query_res is not None:
        delete_goal_from_template(cursor, query_res[0])


def get_beginning_next_month(current_date):
    if current_date.month == DECEMBER:
        beginning_next_month = current_date.replace(day=1, month=1, year=current_date.year + 1)
    else:
        beginning_next_month = current_date.replace(day=1, month=current_date.month + 1)

    return beginning_next_month


def is_valid_email(email):
    email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    return re.match(email_pattern, email) is not None


def check_email(cursor, email):
    email_query = "SELECT COUNT(*) FROM users WHERE email = %s"

    if is_in_use(cursor, email_query, email):
        raise Exception("Email is already in use.")
    elif not is_valid_email(email):
        raise Exception("Email is invalid.")


def is_valid_phone_number(phone_number):
    phone_pattern = r'^\+?[\d\s\-()]{7,15}$'

    return re.match(phone_pattern, phone_number) is not None


def check_phone_number(cursor, phone_number):
    phone_number_query = "SELECT COUNT(*) FROM users WHERE phone_number = %s"

    if is_in_use(cursor, phone_number_query, phone_number):
        raise Exception("Phone number is already in use.")
    elif not is_valid_phone_number(phone_number):
        raise Exception("Phone number is invalid.")


def check_date_of_birth(date_of_birth_input):
    date_of_birth = datetime.strptime(date_of_birth_input, "%Y-%m-%d")
    current_date = datetime.now()
    min_date_of_birth = current_date - timedelta(days=APP_MIN_AGE * DAYS_IN_YEAR)  # Since age of 8

    if date_of_birth >= min_date_of_birth:
        raise Exception("Date of birth must be at least {0} years old.".format(APP_MIN_AGE))


def disconnect_dog_from_collar(cursor, dog_id):
    remove_dog_from_collar_query = f"""
        UPDATE {COLLARS_TABLE}
        SET {DOG_ID_COLUMN} = NULL
        WHERE {DOG_ID_COLUMN} = %s;
        """

    cursor.execute(remove_dog_from_collar_query, (dog_id, ))