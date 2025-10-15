from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from isoweek import Week
from django.utils import timezone

from .constants import WEEK_DATE_FORMAT, ROUND_DECIMAL_DIGITS
from .managers import UserManager

DEFAULT_CASHFLOW_WEEKS = 13


class Number(models.Model):
    TYPE_FLOAT = 0
    TYPE_STR = 1
    TYPE_BOOLEAN = 2

    NUMBER_TYPES = (
        (TYPE_FLOAT, "Float"),
        (TYPE_STR, "String"),
        (TYPE_BOOLEAN, "Boolean"),
    )

    name = models.CharField(max_length=200, unique=True, null=False, db_index=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    short_description = models.TextField(max_length=200, null=True, blank=True)

    number_index = models.CharField(max_length=100, null=True, blank=True,
                                    verbose_name="Number Index (required for formulas)")

    is_formula = models.BooleanField(default=False, db_index=True, verbose_name="Formula actual")
    is_target_formula = models.BooleanField(default=False, db_index=True, verbose_name="Formula target")

    is_negative_green = models.BooleanField(default=False, verbose_name="Revert colors (negative is green)")
    is_optional = models.BooleanField(default=False, db_index=True,
                                      verbose_name="Optional field while building completion report")

    weight = models.IntegerField(default=0, verbose_name="Order weight")
    prefix = models.CharField(default="", max_length=10, blank=True,
                              verbose_name="Num value prefix to display, e.g. %,$, etc.")

    number_type = models.IntegerField(choices=NUMBER_TYPES, default=TYPE_FLOAT)
    target_symbol = models.CharField(max_length=100, null=True, blank=True)
    actual_symbol = models.CharField(max_length=100, null=True, blank=True)
    variance_symbol = models.CharField(max_length=100, null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {} - {}".format(self.name, self.number_index, self.id)


class CustomerGroup(models.Model):
    name = models.CharField(max_length=200)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Customer Groups'

    @property
    def get_customers(self):
        return self.customers.all()

    def __str__(self):
        return "{}".format(self.name)


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="customer")

    groups = models.ManyToManyField(CustomerGroup, related_name="customers", blank=True)

    can_edit_target = models.BooleanField(default=False)

    can_edit_cashflow = models.BooleanField(default=False)

    cashflow_weeks = models.IntegerField(default=DEFAULT_CASHFLOW_WEEKS)
    cashflow_start_week = models.CharField(max_length=8, blank=True, verbose_name="Cashflow start week")

    coach_notify_email = models.CharField(max_length=200, null=True, blank=True)

    coach = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name="customer_coach")

    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+")
    disabled = models.BooleanField(default=False)

    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def get_groups(self):
        return self.groups.all()

    @property
    def name(self):
        return "{} {}".format(self.user.first_name, self.user.last_name)

    def __str__(self):
        return "{} {} {}".format(self.user.first_name, self.user.last_name, self.user.email)


class CompletionReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    week_index = models.CharField(max_length=8, verbose_name="Week index representation", db_index=True)
    completion_rate = models.IntegerField(default=0)
    report_emailed = models.BooleanField(default=False, db_index=True)
    report_emailed_to = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'week_index')

    def __str__(self):
        return "{} {} {}".format(self.user, self.week_index, self.report_emailed_to)


class CashFlowInOut(models.Model):
    CASH_IN = 0
    CASH_OUT = 1

    VALUE_TYPES = (
        (CASH_IN, "Cash In"),
        (CASH_OUT, "Cash Out"),
    )

    # NOTE: User, not a customer
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    value_type = models.IntegerField(choices=VALUE_TYPES, default=CASH_IN, db_index=True)
    debtor_name = models.CharField(max_length=255, blank=True)

    order = models.IntegerField(default=1)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class CashFlowInOutValue(models.Model):
    flow = models.ForeignKey(CashFlowInOut)

    actual_value = models.FloatField(null=True, blank=True)
    target_value = models.FloatField(null=True, blank=True)

    order_index = models.IntegerField(default=0, blank=True)

    week_index = models.CharField(max_length=8, verbose_name="Week index representation", db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('week_index', 'flow')


class NumberValue(models.Model):
    number = models.ForeignKey(Number)

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    actual_value = models.CharField(max_length=200, null=True, blank=True)
    target_value = models.CharField(max_length=200, null=True, blank=True)

    week_index = models.CharField(max_length=8, verbose_name="Week index representation", db_index=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('number', 'week_index', 'user')

    def __str__(self):
        return "{} {} {} {}".format(self.id, self.number.name, self.week_index, self.user.id)


class ContactsMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200, db_index=True)
    message = models.TextField(null=True, blank=True)
    ip = models.CharField(max_length=200, null=True, blank=True)
    hash = models.CharField(max_length=200, db_index=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {} {}".format(self.name, self.email, self.date_created)


class GuaranteeValue(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    rev_1_year = models.FloatField(default=0, blank=True)
    rev_2_year = models.FloatField(default=0, blank=True)
    rev_3_year = models.FloatField(default=0, blank=True)

    year_1_lbl = models.CharField(max_length=10)
    year_2_lbl = models.CharField(max_length=10)
    year_3_lbl = models.CharField(max_length=10)

    minimum_profit = models.FloatField(default=0, blank=True)
    minimum_profit_year = models.CharField(max_length=10, blank=True)

    is_archived = models.BooleanField(default=False)
    guarantee_val = models.FloatField(default=0, blank=True)
    next_range_start_date = models.DateField(null=True, blank=True, help_text="Next range start date")
    next_range_end_date = models.DateField(null=True, blank=True, help_text="Next range end date")

    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    @property
    def average(self):
        return round(
            (self.rev_1_year + self.rev_2_year + self.rev_3_year) / 3,
            ROUND_DECIMAL_DIGITS
        )

    @property
    def target_revenue(self):
        return round(self.average + self.guarantee_val, ROUND_DECIMAL_DIGITS)

    @property
    def next_range_month_delta(self):

        start = self.next_range_start_date
        end = self.next_range_end_date

        if not start or not end:
            return None

        return (end.year - start.year) * 12 + end.month - start.month

    def __str__(self):
        return "{}".format(self.user)


class GuaranteeEarnings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    retained_earnings = models.FloatField(default=0, blank=True)
    current_earnings = models.FloatField(default=0, blank=True)

    date = models.DateField(blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class FocusSheetValue(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    week_index = models.CharField(max_length=8, verbose_name="Week index representation", db_index=True)

    thing_learned = models.TextField(verbose_name="The Number 1 Thing I've Learnt From Today's Session")

    # Goals Data

    goal_1 = models.CharField(verbose_name="Goal 1", max_length=100)
    goal_1_achieved = models.BooleanField(verbose_name="Achieved", default=False)
    goal_1_comments = models.TextField(verbose_name="Comments", null=True, blank=True)

    goal_2 = models.CharField(verbose_name="Goal 2", max_length=100, null=True, blank=True)
    goal_2_achieved = models.BooleanField(verbose_name="Achieved", default=False)
    goal_2_comments = models.TextField(verbose_name="Comments", null=True, blank=True)

    goal_3 = models.CharField(verbose_name="Goal 3", max_length=100, null=True, blank=True)
    goal_3_achieved = models.BooleanField(verbose_name="Achieved", default=False)
    goal_3_comments = models.TextField(verbose_name="Comments", null=True, blank=True)

    goal_4 = models.CharField(verbose_name="Goal 4", max_length=100, null=True, blank=True)
    goal_4_achieved = models.BooleanField(verbose_name="Achieved")
    goal_4_comments = models.TextField(verbose_name="Comments", null=True, blank=True)

    # Fields

    field_achievement = models.CharField(verbose_name="My brightest achievement in the week just pass...",
                                         max_length=255, null=True, blank=True)
    field_challenge = models.CharField(verbose_name="My main challenge during the week gone...", max_length=255,
                                       null=True, blank=True)
    field_learnt = models.CharField(
        verbose_name="Something that I learnt through reading, listening to a tape, watching a video or living life...",
        max_length=255, null=True, blank=True)
    field_focus = models.CharField(verbose_name=" At the moment, my greatest focus when working on my business is...",
                                   max_length=255, null=True, blank=True)
    field_coach_help = models.CharField(verbose_name="As my coach you can help me out in this next session by...",
                                        max_length=255, null=True, blank=True)

    bod_12_program_name = models.CharField(verbose_name="Name", max_length=255, null=True, blank=True)
    bod_12_program_phone = models.CharField(verbose_name="Phone", max_length=255, null=True, blank=True)
    bod_12_program_area_concern = models.CharField(verbose_name="Area of Concern", max_length=255, null=True,
                                                   blank=True)

    # Briefly speaking...
    spent_hours = models.CharField(verbose_name="Hours spent working ON my business this last week", max_length=5,
                                   null=True, blank=True)
    motivation_percentage = models.CharField(verbose_name="My motivation level is at, %", max_length=7, null=True,
                                             blank=True)
    business_is = models.CharField(verbose_name="Business is ", max_length=50, null=True, blank=True)

    # I have concentrated on...
    lead_generation = models.BooleanField(verbose_name="Lead Generation", default=False)
    conversion_rates = models.BooleanField(verbose_name="Conversion Rates", default=False)
    transactions_number = models.BooleanField(verbose_name="Number of Transactions", default=False)
    avg_sale = models.BooleanField(verbose_name="Average $ Sale", default=False)
    margins = models.BooleanField(verbose_name="Margins", default=False)

    # I have also worked on...
    testing = models.BooleanField(verbose_name="Testing and Measuring", default=False)
    documenting = models.BooleanField(verbose_name="Documenting more Systems", default=False)
    training = models.BooleanField(verbose_name="Training my Team", default=False)
    new_marketing = models.BooleanField(verbose_name="Implemented new Marketing", default=False)
    refining_delivery = models.BooleanField(verbose_name="Refining Delivery & Distribution", default=False)

    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    @property
    def week_name(self):
        return str(Week.fromstring(self.week_index).sunday().strftime(WEEK_DATE_FORMAT))


class UserHistoryEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    event_name = models.CharField(max_length=255, null=True, blank=True)
    event_type = models.CharField(max_length=255, null=True, blank=True)
    event_additional = models.CharField(max_length=255, null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'

    first_name = models.CharField(_('first name'), max_length=255, blank=True)
    last_name = models.CharField(_('last name'), max_length=255, blank=True)
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    is_coach = models.BooleanField(default=False, help_text=_("Level 2 coach"))

    is_supercoach = models.BooleanField(default=False, help_text=_("Level 1 coach"))

    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)

    activation_key = models.CharField(max_length=200, null=True, blank=True)

    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    region = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)

    objects = UserManager()

    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    @property
    def full_name(self):
        return self.get_full_name()

    def __str__(self):
        return "{}".format(self.email)


from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

class UserAdminCustom(UserAdmin):
    fieldsets = (
        (None, {'fields': ('password',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_coach', 'is_supercoach')}),
        (_('Additional'), {'fields': ('address', 'city', 'region', 'country', 'activation_key',)}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'password1', 'password2', 'is_coach', 'is_supercoach'),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('email', 'first_name', 'last_name', 'is_coach', 'is_supercoach')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)


class UserHistoryEventAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'event_type',
                    'event_name',
                    'event_additional',
                    'date_created')

    search_fields = ('user__email', 'event_type', 'event_name', 'event_additional')


class CompletionReportsAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'week_index',
                    'completion_rate',
                    'report_emailed',
                    'report_emailed_to')


class GuaranteeValueAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'rev_1_year',
        'rev_2_year',
        'rev_3_year',

        'year_1_lbl',
        'year_2_lbl',
        'year_3_lbl',

        'guarantee_val',
        'next_range_start_date',
        'date_created'
    )


class GuaranteeEarningsAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'retained_earnings',
        'current_earnings',
        'date',
        'date_created')


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'get_groups',
                    'can_edit_target',
                    'can_edit_cashflow',
                    'cashflow_weeks',
                    'cashflow_start_week',
                    'coach_notify_email',
                    'coach',
                    'added_by',
                    'disabled')

    search_fields = ('user__email', 'coach__email')


admin.site.register(Number)
admin.site.register(NumberValue)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerGroup)
admin.site.register(CompletionReport, CompletionReportsAdmin)
admin.site.register(ContactsMessage)
admin.site.register(User, UserAdminCustom)
admin.site.register(UserHistoryEvent, UserHistoryEventAdmin)
admin.site.register(GuaranteeValue, GuaranteeValueAdmin)
admin.site.register(GuaranteeEarnings, GuaranteeEarningsAdmin)
admin.site.register(FocusSheetValue)
