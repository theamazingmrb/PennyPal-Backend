

from django.urls import path
from accounts.api.auth_views import RegisterView, SignInView
from accounts.api.views import (
    UserProfileView,
    ProfileUpdateView,
    total_expenses,
    monthly_summary,
    monthly_pie_data,
    annual_summary,
    day_view,
    CalendarListCreateView,
    CategoryListCreateView,
    BillDueListCreateView,
    BillDueDetailView,
    DeleteAccountView,
)
from accounts.api.transaction_views import TransactionListCreateView, TransactionDetailView

urlpatterns = [
    # -------- AUTH --------
    path("signup/", RegisterView.as_view(), name="signup"),
    path("signin/", SignInView.as_view(), name="signin"),

    # -------- PROFILE --------
    path("profile/", UserProfileView.as_view(), name="profile-detail"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("profile/delete/", DeleteAccountView.as_view(), name="profile-delete"),

    # -------- CATEGORIES & TRANSACTIONS --------
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("transactions/", TransactionListCreateView.as_view(), name="transaction-list-create"),
    path("transactions/<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("transactions/total-expenses/", total_expenses, name="total-expenses"),

    # -------- CALENDAR & DAILY VIEW --------
    path("calendar/", CalendarListCreateView.as_view(), name="calendar-list-create"),
    path("calendar/<int:calendar_id>/day/<str:date_str>/", day_view, name="day-view"),

    # -------- BILLS --------
    path("bills/", BillDueListCreateView.as_view(), name="bills-list-create"),
    path("bills/<int:pk>/", BillDueDetailView.as_view(), name="bill-detail"),

    # -------- SUMMARIES --------
    path("summary/monthly/", monthly_summary, name="monthly-summary"),
    path("summary/annual/", annual_summary, name="annual-summary"),
    path("monthly-pie-data/", monthly_pie_data, name="monthly-pie-data"),
]