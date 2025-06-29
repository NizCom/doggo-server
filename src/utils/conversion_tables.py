from enum import Enum, auto


# For BCS calculation
class ConditionCategory(Enum):
    EMACIATED = auto()
    VERY_THIN = auto()
    THIN = auto()
    IDEAL = auto()
    OVERWEIGHT = auto()
    OBESE = auto()
    VERY_OBESE = auto()
    SEVERELY_OBESE = auto()
    EXTREMELY_OBESE = auto()


class BCSValue(Enum):
    EMACIATED = 1
    VERY_THIN = 2
    THIN = 3
    IDEAL = 4
    OVERWEIGHT = 5
    OBESE = 6
    VERY_OBESE = 7
    SEVERELY_OBESE = 8
    EXTREMELY_OBESE = 9


THRESHOLDS = {
    ConditionCategory.EMACIATED: 0.4,
    ConditionCategory.VERY_THIN: 0.5,
    ConditionCategory.THIN: 0.6,
    ConditionCategory.IDEAL: 0.7,
    ConditionCategory.OVERWEIGHT: 0.8,
    ConditionCategory.OBESE: 0.9,
    ConditionCategory.VERY_OBESE: 1.0,
    ConditionCategory.SEVERELY_OBESE: 1.1,
    ConditionCategory.EXTREMELY_OBESE: 1.2
}


# Weight ranges
TOY_DOG_WEIGHT = (2, 5)
SMALL_DOG_WEIGHT = (5, 10)
MEDIUM_DOG_WEIGHT = (10, 25)
LARGE_DOG_WEIGHT = (25, 40)
EXTRA_LARGE_DOG_WEIGHT = (40, 80)

# Factor ranges
TOY_DOG_FACTOR = (0.5, 0.7)
SMALL_DOG_FACTOR = (0.7, 0.9)
MEDIUM_DOG_FACTOR = (0.9, 1.1)
LARGE_DOG_FACTOR = (1.1, 1.3)
EXTRA_LARGE_DOG_FACTOR = (1.3, 1.6)

METABOLIC_SCALING_EXPONENT = 0.75
HOURS_IN_A_DAY = 24
AVERAGE_WEIGHT = 30  # Average weight in kg
AVERAGE_HEIGHT = 50  # Average height in cm


HEIGHT_RANGES = {
    'TOY_DOG': (0, 25),         # Up to 25 cm
    'SMALL_DOG': (25, 35),      # 25 to 35 cm
    'MEDIUM_DOG': (35, 50),     # 35 to 50 cm
    'LARGE_DOG': (50, 70),      # 50 to 70 cm
    'EXTRA_LARGE_DOG': (70, 100)  # More than 70 cm
}

# Steps length ranges in cm
STEP_LENGTH_RANGES = {
    'TOY_DOG': (25, 35),
    'SMALL_DOG': (35, 45),
    'MEDIUM_DOG': (45, 55),
    'LARGE_DOG': (55, 65),
    'EXTRA_LARGE_DOG': (65, 80)
}

# ideal weight
BREED_STANDARDS = {
    'labrador': {'male': (27, 36), 'female': (25, 32)},
    'german shepherd': {'male': (30, 40), 'female': (22, 32)},
    'beagle': {'male': (10, 11), 'female': (9, 10)},
    'border collie': {'male': (14, 20), 'female': (12, 19)},
    'labrador retriever': {'male': (29, 36), 'female': (25, 32)},
    'golden retriever': {'male': (30, 34), 'female': (25, 29)},
    'bulldog': {'male': (23, 25), 'female': (18, 23)},
    'poodle': {'male': (20, 32), 'female': (18, 30)},
    'rottweiler': {'male': (50, 60), 'female': (35, 48)},
    'yorkshire terrier': {'male': (2, 4), 'female': (2, 4)},
    'dachshund': {'male': (7, 15), 'female': (7, 15)},
    'boxer': {'male': (30, 36), 'female': (25, 30)},
    'shih tzu': {'male': (4, 7), 'female': (4, 7)},
    'doberman pinscher': {'male': (40, 45), 'female': (32, 35)},
    'siberian husky': {'male': (20, 27), 'female': (16, 23)},
    'great dane': {'male': (54, 90), 'female': (45, 59)},
    'chihuahua': {'male': (1.5, 3), 'female': (1.5, 3)},
    'collie': {'male': (20, 29), 'female': (18, 25)},
    'husky': {'male': (20, 27), 'female': (16, 23)},
    # Add more breeds as necessary...
}


def get_dog_weight_range(weight):
    if TOY_DOG_WEIGHT[0] <= weight <= TOY_DOG_WEIGHT[1]:
        return TOY_DOG_WEIGHT
    elif SMALL_DOG_WEIGHT[0] <= weight <= SMALL_DOG_WEIGHT[1]:
        return SMALL_DOG_WEIGHT
    elif MEDIUM_DOG_WEIGHT[0] <= weight <= MEDIUM_DOG_WEIGHT[1]:
        return MEDIUM_DOG_WEIGHT
    elif LARGE_DOG_WEIGHT[0] <= weight <= LARGE_DOG_WEIGHT[1]:
        return LARGE_DOG_WEIGHT
    elif EXTRA_LARGE_DOG_WEIGHT[0] <= weight <= EXTRA_LARGE_DOG_WEIGHT[1]:
        return EXTRA_LARGE_DOG_WEIGHT
    else:
        return MEDIUM_DOG_WEIGHT


def get_dog_factor_range(weight):
    if TOY_DOG_WEIGHT[0] <= weight <= TOY_DOG_WEIGHT[1]:
        return TOY_DOG_FACTOR
    elif SMALL_DOG_WEIGHT[0] <= weight <= SMALL_DOG_WEIGHT[1]:
        return SMALL_DOG_FACTOR
    elif MEDIUM_DOG_WEIGHT[0] <= weight <= MEDIUM_DOG_WEIGHT[1]:
        return MEDIUM_DOG_FACTOR
    elif LARGE_DOG_WEIGHT[0] <= weight <= LARGE_DOG_WEIGHT[1]:
        return LARGE_DOG_FACTOR
    elif EXTRA_LARGE_DOG_WEIGHT[0] <= weight <= EXTRA_LARGE_DOG_WEIGHT[1]:
        return EXTRA_LARGE_DOG_FACTOR
    else:
        return MEDIUM_DOG_FACTOR


def get_position_in_range(weight, weight_range):
    start, end = weight_range
    return (weight - start) / (end - start)


def number_in_range(fraction, range_tuple):
    start, end = range_tuple
    if not (0 <= fraction <= 1):
        raise ValueError("Fraction must be between 0 and 1.")
    return start + fraction * (end - start)


def get_converted_steps(weight, steps_to_convert):
    factor_range = get_dog_factor_range(weight)
    weight_range = get_dog_weight_range(weight)
    fraction = get_position_in_range(weight, weight_range)
    converted_steps = steps_to_convert * number_in_range(fraction, factor_range)

    return converted_steps


def get_calculated_distance(steps, height):
    size_category = determine_size_category_by_height(height)
    average_step_length_cm = calculate_average_step_length(size_category)
    distance_cm = steps * average_step_length_cm
    distance_km = distance_cm / 100000  # Convert cm to km

    return distance_km


def get_burned_calories(weight, distance):
    factor_range = get_dog_factor_range(weight)
    weight_range = get_dog_weight_range(weight)

    fraction = get_position_in_range(weight, weight_range)
    calculated_activity_factor = number_in_range(fraction, factor_range)

    # Estimating BMR (Basal Metabolic Rate) for the dog
    bmr = 70 * (weight ** METABOLIC_SCALING_EXPONENT)

    calories_burned = bmr * calculated_activity_factor * distance / HOURS_IN_A_DAY

    return calories_burned


def estimate_bcs(weight, gender, breed):
    breed = breed.lower()
    gender = gender.lower()

    # Check if breed is available in the standard data
    if breed not in BREED_STANDARDS:
        raise ValueError(f"Breed '{breed}' is not available in the database.")

    # Get the ideal weight range for the breed and gender
    breed_info = BREED_STANDARDS[breed]
    if gender not in breed_info:
        raise ValueError(f"Gender '{gender}' not available for breed '{breed}'.")

    ideal_weight_range = breed_info[gender]
    ideal_min_weight, ideal_max_weight = ideal_weight_range

    # Estimate BCS based on how far the current weight deviates from the ideal range
    if weight < ideal_min_weight:
        bcs = 1 + (ideal_min_weight - weight) / ideal_min_weight * 4  # Underweight
    elif weight > ideal_max_weight:
        bcs = 5 + (weight - ideal_max_weight) / ideal_max_weight * 4  # Overweight
    else:
        bcs = 5  # Ideal weight

    # Ensure BCS is between 1 and 9
    bcs = max(1, min(9, bcs))

    return round(bcs)


def calculate_average_step_length(size_category):
    step_length_range = STEP_LENGTH_RANGES[size_category]
    average_step_length_cm = (step_length_range[0] + step_length_range[1]) / 2

    return average_step_length_cm


def determine_size_category_by_height(height_cm):
    for category, (min_height, max_height) in HEIGHT_RANGES.items():
        if min_height <= height_cm <= max_height:
            return category
