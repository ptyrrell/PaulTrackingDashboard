from django.conf.urls import include, url
from django.contrib import admin

from apps.api.cashflow import CashValueApi, CashSummaryApi, CashOrderApi, CashflowExcelExportApi
from apps.cashflow.views import cashflow_view
from apps.contacts.views import ContactsPageView
from apps.dashboard.views import dashboard_view
from apps.events_history.views import history_view
from apps.focus_sheet.api import FocusSheetApi
from apps.focus_sheet.views import focus_sheet_admin_view, focus_sheet_input_view, focus_sheet_edit_view, FocusSheetList
from apps.groups.views import (
    customer_activation,
    customer_add,
    customer_edit,
    customer_new_password,
    group_create,
    group_delete,
    group_list,
    group_update,
    my_customers,
)
from apps.journey.chart import JourneyChart, EarningsChart
from apps.journey.views import guarantee_view, earnings_view, journey_archive_view
from apps.numbers.chart import NumbersChart
from apps.numbers.generic import NumbersView, NumbersExportView
from apps.numbers.import_targets import import_targets
from apps.numbers.views import (
    index,
    numbers,
    pages,
    password_reset_confirm_view,
    password_reset_view,
    targets,
)
from apps.reports.views import ReportsApi, reports_view
from apps.users.views import LogOutView, LoginView

admin.autodiscover()


urlpatterns = [

    # admin
    url(r'^admin-main-panel/', include(admin.site.urls)),

    url(r'^$', index),

    url(r'^(about|calculators|break-even-analyzer)$', pages),

    url(r'^contacts/$', ContactsPageView.as_view()),

    # numbers
    url(r'^numbers/export$', NumbersExportView.as_view(), name='numbers_export'),
    url(r'^numbers/$', numbers, name="numbers_view"),
    url(r'^targets/$', targets, name="targets_view"),

    # cashflow
    url(r'^cashflow/$', cashflow_view, name="cashflow_view"),

    url(r'^api/1/cashflow/order/(in|out)', CashOrderApi.as_view()),
    url(r'^api/1/cashflow/(in|out)', CashValueApi.as_view()),
    url(r'^api/1/cashflow/summary', CashSummaryApi.as_view()),
    url(r'^cashflow/export$', CashflowExcelExportApi.as_view()),

    # groups & customers
    url(r'^groups/$', group_list, name="group_list"),
    url(r'^groups/new$', group_create, name="group_new"),
    url(r'^groups/update/(?P<pk>\d+)$', group_update, name="group_update"),
    url(r'^groups/delete/(?P<pk>\d+)$', group_delete, name="group_delete"),

    url(r'customers/$', my_customers, name="customers"),
    url(r'^customers/new$', customer_add, name="customer_add"),

    url(r'^customers/(\d+)/edit$', customer_edit, name="customer_edit"),
    url(r'^customers/(\d+)/activation$', customer_activation, name="customer_activation"),

    url(r'^customers/(\d+)/new_password', customer_new_password, name="customer_new_password"),

    # reports
    url(r'^reports/', reports_view, name="reports"),
    url(r'^api/1/reports/(\d+|all)/(\d{4}W\d{2})', ReportsApi.as_view()),

    # dashboard
    url(r'^dashboard/', dashboard_view, name="dashboard_view"),

    # user events
    url(r'^user-events/', history_view, name="history_view"),

    # focus sheet
    url(r'^focus-sheet-admin/', focus_sheet_admin_view, name="focus_sheet_admin"),
    url(r'^focus-sheet-list/', FocusSheetList.as_view(), name="focus_sheet_list"),
    url(r'^focus-sheet-create/', focus_sheet_input_view, name="focus_sheet_create"),
    url(r'^focus-sheet-edit/(?P<pk>\d+)', focus_sheet_edit_view, name="focus_sheet_edit"),
    url(r'^api/1/focus-sheet/', FocusSheetApi.as_view(), name="focus-sheet-api"),

    # user related stuff
    url(r'^login/$', LoginView.as_view(), name="login"),
    url(r'^logout/$', LogOutView.as_view(), name="logout"),

    # guarantee feature
    url(r'^journey/$', guarantee_view, name="guarantee_view"),
    url(r'^journey/earnings/$', earnings_view, name="earnings_view"),
    url(r'^journey/archive/$', journey_archive_view, name="journey_archive_view"),


    # api
    url(r'^api/1/journey/', JourneyChart.as_view(), name='journey-api'),
    url(r'^api/1/earnings/', EarningsChart.as_view(), name='earnings-api'),
    url(r'^api/1/numbers/(\d{4}W\d{2})', NumbersView.as_view()),
    url(r'^api/1/number/(\d+)/(\d{4}W\d{2})/(\d{4}W\d{2})?', NumbersChart.as_view()),
    url(r'^api/1/numbers/import/(\d{4}W\d{2})/(\d{4}W\d{2})/(\d{4}W\d{2})', import_targets),
    url(r'^impersonate/', include('impersonate.urls')),

    url(r'^password-reset-confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        password_reset_confirm_view, name='password_reset_confirm'),
    url(r'^password-reset/$', password_reset_view, name="password_reset"),
]
