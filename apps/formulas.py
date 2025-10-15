from apps.constants import ROUND_DECIMAL_DIGITS
from apps.models import Number, NumberValue


def get_month_weeks(week):
    current_month = week.sunday().month
    weeks = [week - i for i in range(5, 0, -1)] + [week]
    weeks = [w for w in weeks if w.sunday().month == current_month]
    return weeks


def get_number_values_in_month(number, week, user):
    weeks = get_month_weeks(week)
    values = NumberValue.objects.filter(number=number, user=user, week_index__in=weeks)
    return values


# TODO: Re-factor
class Formulas(object):
    def __init__(self, number, week, user, values, numbers):
        self.number = number
        self.week = week
        self.user = user

        # TODO: Add user check
        self.values = values
        self.numbers = numbers

    def calculate(self):
        if self.number.number_index == "N_WEEK_AVG_INV":
            # Sales for week (actual) / Number Invoices (actual)
            week_actual = None
            number_invoices = None
            for v in self.values:
                if v.number.number_index == "N_WEEK_SALES":
                    week_actual = v.actual_value
                if v.number.number_index == "N_WEEK_INVOICES":
                    number_invoices = v.actual_value

            if week_actual is not None and number_invoices is not None:
                number_invoices = float(number_invoices)
                if number_invoices != 0:
                    return round(float(week_actual) / float(number_invoices), ROUND_DECIMAL_DIGITS)

        elif self.number.number_index == "N_MONTH_QUOTES":
            #  Sum of all of the quotes for the week in this month.
            number = Number.objects.get(number_index="N_WEEK_QUOTES")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.actual_value) for v in values if v.actual_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None
        elif self.number.number_index == "N_MONTH_COGS":
            #  Sum of all of the COGS for the week in this month.
            number = Number.objects.get(number_index="N_WEEK_COGS")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.actual_value) for v in values if v.actual_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None
        elif self.number.number_index == "N_MONTH_SALES":
            # Sum of all of the sales for the week in this month.
            number = Number.objects.get(number_index="N_WEEK_SALES")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.actual_value) for v in values if v.actual_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None

        elif self.number.number_index == "N_MONTH_GROSS_PRF":

            month_gogs = None
            month_sales = None
            for n in self.numbers:
                if n.number_index == "N_MONTH_COGS":
                    month_gogs = self.get_number_value("N_MONTH_COGS", self.numbers, "actual_value")
                if n.number_index == "N_MONTH_SALES":
                    month_sales = self.get_number_value("N_MONTH_SALES", self.numbers, "actual_value")

            if month_gogs and month_sales and month_sales > 0:
                return round(1 - (month_gogs / float(month_sales)), ROUND_DECIMAL_DIGITS) * 100

        elif self.number.number_index == "N_WEEK_UTIL":
            # Actual sales for week / Target Utilisation as a %
            revenue_val = self.get_number_value("N_WEEK_SALES", self.numbers)

            rev_act = getattr(revenue_val, "actual_value")
            rev_target = getattr(revenue_val, "target_value")

            if rev_act is not None and rev_target is not None and float(rev_target) > 0:
                return round((float(rev_act) / float(rev_target)) * 100, ROUND_DECIMAL_DIGITS)

        elif self.number.number_index == "N_MONTH_BREAK_EV":
            # Compare your 11.Actual sales for the month against your monthly Breakeven #.
            # tg = self.number.value.target_value
            ac = self.get_number_value("N_MONTH_SALES", self.numbers, "actual_value")
            if ac is not None:
                return ac

        elif self.number.number_index == "N_TOTAL_EMP_COSTS":
            number = Number.objects.get(number_index="N_TOTAL_EMP_COSTS_WEEK")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.actual_value) for v in values if v.actual_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None

        elif self.number.number_index == "N_TOTAL_EMP_CO_REV":
            number1 = Number.objects.get(number_index="N_TOTAL_EMP_COSTS_WEEK")
            number2 = Number.objects.get(number_index="N_WEEK_SALES")
            values1 = get_number_values_in_month(number1, self.week, self.user)
            values2 = get_number_values_in_month(number2, self.week, self.user)

            sum1 = sum([float(v.actual_value) for v in values1 if v.actual_value is not None])
            sum2 = sum([float(v.actual_value) for v in values2 if v.actual_value is not None])

            if sum1 is not None and sum2 is not None and float(sum2) > 0:
                return round((float(sum1) / float(sum2)) * 100, ROUND_DECIMAL_DIGITS)

        elif self.number.number_index == "N_LIQ_RATIO":
            ac1 = self.get_number_value("N_BIB", self.numbers, "actual_value")
            ac2 = self.get_number_value("N_DEB_REC_TOT", self.numbers, "actual_value")
            ac3 = self.get_number_value("N_CRED_PAY_TOT", self.numbers, "actual_value")

            if ac1 is not None and ac2 is not None and ac3 is not None and float(ac3) > 0:
                return round(((float(ac1) + float(ac2)) / float(ac3)) * 100, ROUND_DECIMAL_DIGITS)

    def get_number_value(self, index, numbers, attr=None):
        from apps.numbers import calculate_week_number_value
        for number in numbers:
            if number.number_index == index:
                number = calculate_week_number_value(self.user, number, self.week, self.numbers, self.values)
                if attr is not None:
                    return getattr(number.value, attr, None)
                else:
                    return number.value


class TargetFormulas(Formulas):
    def __init__(self, *args, **kwargs):
        super(TargetFormulas, self).__init__(*args, **kwargs)

    def calculate(self):

        if self.number.number_index == "N_WEEK_AVG_INV":
            # Sales for week (target) / Number Invoices (target)

            week_target = None
            number_invoices = None
            for v in self.values:
                if v.number.number_index == "N_WEEK_SALES":
                    week_target = v.target_value
                if v.number.number_index == "N_WEEK_INVOICES":
                    number_invoices = v.target_value

            if week_target is not None and number_invoices is not None:
                number_invoices = float(number_invoices)
                if number_invoices != 0:
                    r = round(float(week_target) / float(number_invoices), ROUND_DECIMAL_DIGITS)
                    return r

        elif self.number.number_index == "N_MONTH_QUOTES":
            #  Sum of all of the quotes for the week in this month.
            number = Number.objects.get(number_index="N_WEEK_QUOTES")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.target_value) for v in values if v.target_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None

        elif self.number.number_index == "N_MONTH_COGS":
            #  Sum of all of the COGS for the week in this month.
            number = Number.objects.get(number_index="N_WEEK_COGS")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.target_value) for v in values if v.target_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None

        elif self.number.number_index == "N_MONTH_SALES":
            # Sum of all of the sales for the week in this month.
            number = Number.objects.get(number_index="N_WEEK_SALES")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.target_value) for v in values if v.target_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None

        elif self.number.number_index == "N_TOTAL_EMP_COSTS":
            number = Number.objects.get(number_index="N_TOTAL_EMP_COSTS_WEEK")
            values = get_number_values_in_month(number, self.week, self.user)
            s = sum([float(v.target_value) for v in values if v.target_value is not None])
            return round(s, ROUND_DECIMAL_DIGITS) if s > 0 else None
