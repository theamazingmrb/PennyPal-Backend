
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.contrib.auth.models import User 
from django.db.models.functions import TruncMonth, Coalesce
from django.db import models
from django.db.models import Sum, F, Value as V, DecimalField
from calendar import monthrange
from datetime import date, datetime
from rest_framework.decorators import api_view, permission_classes
from accounts.models import Profile, Category, Transaction, Calendar, CalendarCell, BillDue
from .serializers import (
    ProfileSerializer,
    CategorySerializer,
    CalendarSerializer,
    BillDueSerializer,
    TransactionSerializer,
    UserSerializer,
)
from accounts.api.serializers import CategorySerializer  # make sure already imported


# -------------------- PROFILE & USER VIEWS --------------------

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user

class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class DeleteAccountView(generics.DestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user


# -------------------- CATEGORIES --------------------
class CategoryListCreateView(generics.ListCreateAPIView):
   
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by('name')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# -------------------- TRANSACTIONS (helpers) --------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def total_expenses(request):
    
    total = (
        Transaction.objects
        .filter(user=request.user, type='expense')
        .aggregate(Sum('amount'))
    )
    return Response({"total_expenses": total['amount__sum'] or 0})


# -------------------- MONTHLY SUMMARY --------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def monthly_summary(request):
    
    user = request.user
    transactions = (
        Transaction.objects
        .filter(user_id=user.id)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_income=Coalesce(
                Sum('amount', filter=models.Q(type='income')),
                V(0),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            total_expenses=Coalesce(
                Sum('amount', filter=models.Q(type='expense')),
                V(0),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )
        .annotate(net_balance=F('total_income') - F('total_expenses'))
        .order_by('-month')
    )
    return Response(transactions)


# -------------------- DAY VIEW --------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def day_view(request, calendar_id, date_str):
    
    try:
        calendar = Calendar.objects.get(id=calendar_id, user=request.user)
    except Calendar.DoesNotExist:
        return Response({"error": "Calendar not found"}, status=404)

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Invalid date format (use YYYY-MM-DD)"}, status=400)

    transactions = Transaction.objects.filter(user=request.user, date=target_date)
    bills = BillDue.objects.filter(user=request.user, due_date=target_date)

    total_expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    total_income   = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance    = total_income - total_expenses

    return Response({
        "date": target_date,
        "transactions": list(
            transactions.values('id', 'type', 'amount', 'category__name', 'description', 'date')
        ),
        "bills": list(
            bills.values('id', 'name', 'amount', 'type', 'note', 'due_date', 'is_paid')
        ),
        "total_expenses": total_expenses,
        "total_income": total_income,
        "net_balance": net_balance,
    })

# -------------------- ANNUAL SUMMARY --------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def annual_summary(request):
    user = request.user
    year = int(request.query_params.get("year", datetime.now().year))

    transactions = Transaction.objects.filter(user=user, date__year=year)
    bills = BillDue.objects.filter(user=user, due_date__year=year)

    total_income = transactions.filter(type="income").aggregate(Sum("amount"))["amount__sum"] or 0
    total_expenses = transactions.filter(type="expense").aggregate(Sum("amount"))["amount__sum"] or 0
    total_bills = bills.aggregate(Sum("amount"))["amount__sum"] or 0

    total_balance = total_income - total_expenses - total_bills

    return Response({
        "year": year,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_bills": total_bills,
        "total_balance": total_balance,
    })

# -------------------- CALENDAR --------------------
class CalendarListCreateView(generics.ListCreateAPIView):
   
    serializer_class = CalendarSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        qs = Calendar.objects.filter(user=self.request.user).order_by('-year', '-month')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            qs = qs.filter(month=month, year=year)
        return qs

    def perform_create(self, serializer):
        month = self.request.data.get('month')
        year  = self.request.data.get('year')
        if not month or not year:
            raise ValueError("month and year are required.")

        existing = Calendar.objects.filter(user=self.request.user, month=month, year=year).first()
        if existing:
            return  

        calendar = serializer.save(user=self.request.user, month=month, year=year)

        _, num_days = monthrange(int(year), int(month))
        for day in range(1, num_days + 1):
            CalendarCell.objects.get_or_create(
                calendar=calendar,
                date=date(int(year), int(month), day)
            )


# -------------------- BILLS --------------------
class BillDueListCreateView(generics.ListCreateAPIView):
    
    serializer_class = BillDueSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        qs = BillDue.objects.filter(user=self.request.user).order_by('due_date')
        # Optional: filter by month/year to help the calendar page
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            qs = qs.filter(due_date__year=year, due_date__month=month)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BillDueDetailView(generics.RetrieveUpdateDestroyAPIView):
    
    serializer_class = BillDueSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return BillDue.objects.filter(user=self.request.user)
    
# -------------------- TRANSACTION DETAIL --------------------
class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
# -------------------- MONTHLY PIE DATA FOR FRONTEND --------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def monthly_pie_data(request):
    """Return monthly totals of income, expenses, and bills for the current year."""
    user = request.user
    year = int(request.query_params.get('year', datetime.now().year))

    monthly_data = []
    for month in range(1, 13):
        transactions = Transaction.objects.filter(user=user, date__year=year, date__month=month)
        bills = BillDue.objects.filter(user=user, due_date__year=year, due_date__month=month)

        total_income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        total_bills = bills.aggregate(Sum('amount'))['amount__sum'] or 0

        if total_income > 0 or total_expenses > 0 or total_bills > 0:
            monthly_data.append({
                "month": month,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "total_bills": total_bills,
            })

    return Response({
        "year": year,
        "months": monthly_data
    })