

from django.urls import path
from accounts.api.views import (
    RegisterView, LoginView, UserProfileView, ProfileListView, ProfileUpdateView,
    total_expenses, monthly_summary, annual_summary, day_view
)
from accounts.api.transaction_views import (
    CategoryListCreateView, TransactionListCreateView
)
from accounts.api.views import CalendarListCreateView
from accounts.api.views import BillDueListCreateView
from accounts.api.views import monthly_summary




urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profiles/', ProfileListView.as_view(), name='profile-list'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/total-expenses/', total_expenses, name='total-expenses'),
    path('calendar/', CalendarListCreateView.as_view(), name='calendar-list-create'),
    path('bills/', BillDueListCreateView.as_view(), name='bills-list-create'),
    path('summary/monthly/', monthly_summary, name='monthly-summary'),
    path('summary/annual/', annual_summary, name='annual-summary'),
    path('calendar/<int:calendar_id>/day/<str:date_str>/', day_view, name='day-view'), 
]
