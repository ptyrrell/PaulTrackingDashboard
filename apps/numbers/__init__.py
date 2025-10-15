import logging

from apps.constants import ROUND_DECIMAL_DIGITS, WEEK_DATE_FORMAT
from apps.formulas import Formulas, TargetFormulas
from apps.models import Number, NumberValue
from isoweek import Week


logger = logging.getLogger(__name__)

TAX_YES = 1
TAX_NO = 0
TAX_PAYMENT = 2


def find_number_value(number, week, all_values):
    for nv in all_values:
        if nv.number == number and nv.week_index == str(week):
            return nv
    return None


def calculate_week_number_value(user, number, week, all_numbers, all_values):

    val = find_number_value(number, week, all_values)
    number.value = val if val else NumberValue(number=number, user=user, week_index=str(week))
    number.value.variance = None

    if number.is_formula:
        number.value.actual_value = Formulas(number, week, user, all_values, all_numbers).calculate()

    if number.is_target_formula:
        number.value.target_value = TargetFormulas(number, week, user, all_values, all_numbers).calculate()

    if number.number_type == Number.TYPE_FLOAT:
        if number.value.actual_value and number.value.target_value:
            number.value.variance = calculate_variance(number, float(number.value.target_value), float(number.value.actual_value))

    return number


def read_week_numbers(user, week):
    """
    Reads week data

    """
    numbers = Number.objects.filter().order_by("-weight")
    values = NumberValue.objects.filter(week_index=week, user=user)

    for number in numbers:
        calculate_week_number_value(user, number, week, numbers, values)
    return numbers


def calculate_variance(number, target_value, actual_value):
    # Calculates variance for different numbers, in most cases variance is actual - target
    if number.number_index == "N_WEEK_UTIL":
        return round(actual_value - target_value, ROUND_DECIMAL_DIGITS)

    if number.number_index in ["N_DEB_REC_TOT", "N_CRED_PAY_TOT", "N_TOTAL_EMP_COSTS", "N_WEEK_ACT_PAYOUTS"]:
        return round(target_value - actual_value, ROUND_DECIMAL_DIGITS)
    else:
        return round(actual_value - target_value, ROUND_DECIMAL_DIGITS)


def serialize_number(number, week):
    target_value = number.value.target_value
    actual_value = number.value.actual_value
    variance = number.value.variance

    if number.number_type == Number.TYPE_FLOAT:
        if target_value is not None:
            target_value = round(float(target_value), ROUND_DECIMAL_DIGITS)
        if actual_value is not None:
            actual_value = round(float(actual_value), ROUND_DECIMAL_DIGITS)
        if variance is not None:
            variance = round(float(variance), ROUND_DECIMAL_DIGITS)

    elif number.number_type == Number.TYPE_BOOLEAN:
        if target_value is not None:
            # TODO: Temporary check, for compatibility issues
            if isinstance(target_value, str) and target_value in ["True", "False"]:
                target_value = TAX_YES if target_value else TAX_NO

            target_value = int(target_value)

        if actual_value is not None:
            # TODO: Temporary check, for compatibility issues
            if isinstance(actual_value, str) and actual_value in ["True", "False"]:
                actual_value = TAX_YES if actual_value else TAX_NO

            actual_value = int(actual_value)

    result = {
        "id": number.id,
        "name": number.name,
        "index": number.number_index,
        "target_symbol": number.target_symbol,
        "actual_symbol": number.actual_symbol,
        "variance_symbol": number.variance_symbol,
        "is_formula": number.is_formula,
        "is_negative_green": number.is_negative_green,
        "number_type": number.number_type,
        "description": number.description,
        "prefix": number.prefix,
        "value": {"target_value": target_value,
                  "actual_value": actual_value, "variance": variance}

    }
    return result
