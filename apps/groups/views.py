from apps.models import Customer, CustomerGroup, User
from apps.permissions import is_coach, is_supercoach
from apps.utils import get_weeks_range
from django import template
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
    ValidationError,
)
from django.db.models import Q
from django.forms import (
    CharField,
    EmailField,
    Form,
    ModelChoiceField,
    ModelForm,
    PasswordInput,
    Select,
)
from django.shortcuts import get_object_or_404, redirect, render
from isoweek import Week


SELECT_WEEKS = get_weeks_range(Week.fromstring("2015W01"), num_of_weeks_ahead=100, include_current=True)

register = template.Library()


def get_coaches_list():
    return User.objects.filter(Q(is_coach=True) | Q(is_supercoach=True), is_active=True).all()


class GroupsForm(ModelForm):
    class Meta:
        model = CustomerGroup
        exclude = ("creator", )


def user_exists_validator(val):
    try:
        get_user_model().objects.get(email=val)
        raise ValidationError("User which such email already exists.")
    except ObjectDoesNotExist:
        return True


class CustomerForm(ModelForm):
    first_name = CharField(min_length=2, max_length=100)
    last_name = CharField(min_length=2, max_length=100)
    email = EmailField(validators=[user_exists_validator])
    password = CharField(widget=PasswordInput)
    coach = ModelChoiceField(queryset=get_coaches_list(), widget=Select(attrs={"class": "form-control"}))

    class Meta:
        model = Customer
        exclude = ("user", "added_by", "disabled", "coach_notify_email" "date_created")

    def __init__(self, user, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields["groups"].queryset = CustomerGroup.objects.all()


class CustomerEditForm(ModelForm):
    first_name = CharField(min_length=2, max_length=100)
    last_name = CharField(min_length=2, max_length=100)

    coach = ModelChoiceField(queryset=get_coaches_list(), widget=Select(attrs={"class": "form-control"}))

    class Meta:
        model = Customer
        exclude = ("user", "added_by", "disabled", "date_created", "coach_notify_email")

    def __init__(self, user, *args, **kwargs):
        super(CustomerEditForm, self).__init__(*args, **kwargs)
        self.fields["groups"].queryset = CustomerGroup.objects.all()


class UserForm(ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name']


class NewPasswordForm(Form):
    password = CharField(widget=PasswordInput)


def is_allowed_impersonate(request):
    if not request.user:
        return False

    if request.user.is_superuser or request.user.is_supercoach or request.user.is_coach:
        return True

    return False


@login_required
def group_list(request, template_name='groups/groups.html'):
    """
    Retrieves list of groups
    """
    if not is_supercoach(request.user):
        raise PermissionDenied

    groups = list(CustomerGroup.objects.order_by("name"))
    return render(request, template_name, {"groups": groups})


@login_required
def group_create(request, template_name='groups/group_form.html'):
    """
    Creates new group
    """
    if not is_supercoach(request.user):
        raise PermissionDenied

    form = GroupsForm(request.POST or None)
    if form.is_valid():
        group = CustomerGroup(name=form.cleaned_data["name"], creator=request.user)
        group.save()
        return redirect('group_list')
    return render(request, template_name, {'form': form})


@login_required
def group_update(request, pk, template_name='groups/group_form.html'):
    """
    Updates existing group
    """
    if not is_supercoach(request.user):
        raise PermissionDenied

    group = get_object_or_404(CustomerGroup, pk=pk)
    form = GroupsForm(request.POST or None, instance=group)
    if form.is_valid():
        form.save()
        return redirect('group_list')
    return render(request, template_name, {'form': form})


@login_required
def group_delete(request, pk, template_name='groups/group_delete.html'):
    """
    Removes existing group
    """
    if not is_supercoach(request.user):
        raise PermissionDenied

    group = get_object_or_404(CustomerGroup, pk=pk)
    if request.method == 'POST':
        group.delete()
        return redirect('group_list')
    return render(request, template_name, {'object': group})


@login_required
def customer_edit(request, customer_id):
    """
    Edits existing customer
    """
    if not is_supercoach(request.user):
        raise PermissionDenied

    customer = Customer.objects.get(id=customer_id)
    user = customer.user
    email = user.email

    form = CustomerEditForm(request.user, {"first_name": user.first_name,
                                           "last_name": user.last_name,
                                           "groups": customer.get_groups,
                                           "coach": customer.coach,
                                           "cashflow_start_week": customer.cashflow_start_week,
                                           "cashflow_weeks": customer.cashflow_weeks,
                                           "can_edit_cashflow": customer.can_edit_cashflow,
                                           "can_edit_target": customer.can_edit_target},
                            instance=customer)

    if request.method == "POST":
        form = CustomerEditForm(request.user, request.POST, instance=customer)
        if form.is_valid():
            user_form = UserForm(data=request.POST, instance=user)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.save()

            customer.can_edit_cashflow = form.cleaned_data["can_edit_cashflow"]
            customer.coach = form.cleaned_data["coach"]
            customer.coach_notify_email = customer.coach.email
            customer.cashflow_start_week = form.cleaned_data["cashflow_start_week"]
            customer.can_edit_target = form.cleaned_data["can_edit_target"]
            customer.cashflow_weeks = form.cleaned_data["cashflow_weeks"]
            customer.groups = form.cleaned_data["groups"]
            customer.save()

            messages.add_message(request, messages.INFO, "Customer ({}) data was updated successfully.".format(customer.user.email))

            return redirect("customers")
        else:
            pass

    return render(request, "groups/customer_edit.html",
                  {"form": form, "weeks": SELECT_WEEKS, "customer": customer, "email": email})


@login_required
def customer_add(request):
    """
    Adds new customer
    """

    if not is_supercoach(request.user):
        raise PermissionDenied

    form = CustomerForm(request.user)

    if request.method == "POST":
        form = CustomerForm(request.user, request.POST)
        if form.is_valid():

            email = get_user_model().objects.normalize_email(form.cleaned_data["email"])
            password = form.cleaned_data["password"]

            user = get_user_model().objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=email,
                password=password
            )
            user.set_password(password)
            user.save()

            customer = Customer.objects.create(user=user,
                                               coach=form.cleaned_data["coach"],
                                               added_by=request.user,
                                               cashflow_start_week=form.cleaned_data["cashflow_start_week"],
                                               can_edit_cashflow=form.cleaned_data["can_edit_cashflow"],
                                               cashflow_weeks=form.cleaned_data["cashflow_weeks"],
                                               can_edit_target=form.cleaned_data["can_edit_target"])
            customer.groups = form.cleaned_data["groups"]
            customer.coach_notify_email = customer.coach.email
            customer.save()

            messages.add_message(request, messages.INFO, "Customer ({}) data was added successfully.".format(customer.user.email))

            return redirect("customers")

    return render(request, "groups/customer_add.html", {"form": form, "weeks": SELECT_WEEKS})


@login_required
def my_customers(request):
    """
    Gets list of all customers (if super coach) or customers associated with coach
    """

    if not is_coach(request.user):
        raise PermissionDenied

    inactive_customers = []

    if request.user.is_supercoach or request.user.is_superuser:
        customers = Customer.objects.filter(user__is_active=True).order_by("user__first_name")
        inactive_customers = Customer.objects.filter(user__is_active=False).order_by("user__first_name")
    else:
        customers = Customer.objects.filter(coach=request.user).order_by("user__first_name")

    return render(request, "groups/customers.html", {"customers": customers, "inactive_customers": inactive_customers})


@login_required
def customer_activation(request, customer_id):
    """
    Swtiches customer "is_active" status
    """

    if not is_supercoach(request.user):
        raise PermissionDenied

    customer = Customer.objects.get(id=customer_id)
    user = customer.user
    user.is_active = not user.is_active
    user.save()
    return redirect("customers")


@login_required
def customer_new_password(request, customer_id):
    """
    Sets new password for customer
    """
    if not is_supercoach(request.user):
        raise PermissionDenied

    customer = Customer.objects.get(id=customer_id)
    user = customer.user
    email = user.email

    form = NewPasswordForm()

    if request.method == "POST":
        form = NewPasswordForm(request.POST)
        if form.is_valid():
            passwd = form.cleaned_data["password"]
            user.set_password(passwd)
            user.save()
            messages.add_message(request, messages.INFO, "Password for {} was changed.".format(user.email))
            return redirect("customers")

    return render(request, "groups/customer_new_password.html", {"form": form, "email": email})
