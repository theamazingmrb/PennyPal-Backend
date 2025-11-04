

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView     
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication 
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, LoginSerializer, ProfileSerializer
from accounts.models import Profile, Category, Transaction, Calendar, CalendarCell, BillDue
from accounts.api.serializers import CategorySerializer, CalendarSerializer, CalendarCellSerializer, BillDueSerializer
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from calendar import monthrange
from datetime import date
from django.db.models.functions import TruncMonth, Coalesce
from django.db.models import Sum, F, Value as V, DecimalField
from django.db import models


# -------------------- USER & AUTH ---------------------------------------------------------------------------------
class ProfileListView(generics.ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer    

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    renderer_classes = [JSONRenderer]

    def get(self, request, *args, **kwargs):
        return Response({"detail": "Use POST to log in with username and password."})

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user) 
            return Response({
                "message": "Login successful!",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user.profile
    
class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile 

# -------------------- CATEGORY ------------------------------------------------------------------------------------
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user) 

# -------------------- TRANSACTIONS --------------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])

def total_expenses(request):
    total = Transaction.objects.filter(user=request.user, type='expense').aggregate(Sum('amount'))
    return Response({"total_expenses": total['amount__sum'] or 0})

# -------------------- MONTHLY SUMMARY -----------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def monthly_summary(request):
    user = request.user

    if not user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    transactions = (
        Transaction.objects
        .filter(user_id=user.id)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            total_income=Coalesce(
                Sum('amount', filter=models.Q(type='income')),
                V(0),
                output_field=DecimalField()
            ),
            total_expenses=Coalesce(
                Sum('amount', filter=models.Q(type='expense')),
                V(0),
                output_field=DecimalField()
            )
        )
        .annotate(
            net_balance=F('total_income') - F('total_expenses')
        )
        .order_by('-month')
    )

    return Response(transactions)

# ------------------- Day views-------------------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def day_view(request, calendar_id, date_str):
    try:
        calendar = Calendar.objects.get(id=calendar_id, user=request.user)
    except Calendar.DoesNotExist:
        return Response({"error": "Calendar not found"}, status=404)

    # Convert date string to Python date
    from datetime import datetime
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Invalid date format (use YYYY-MM-DD)"}, status=400)

    # Get all transactions and bills for this date
    transactions = Transaction.objects.filter(user=request.user, date=target_date)
    bills = BillDue.objects.filter(user=request.user, due_date=target_date)

    total_expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income - total_expenses

    return Response({
        "date": target_date,
        "transactions": list(transactions.values('id', 'type', 'amount', 'category__name', 'description')),
        "bills": list(bills.values('id', 'name', 'amount', 'due_date')),
        "total_expenses": total_expenses,
        "total_income": total_income,
        "net_balance": net_balance,
    })

# --------------------Annual summary -------------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def annual_summary(request):
    user = request.user
    year = request.query_params.get('year')

    from datetime import datetime
    if not year:
        year = datetime.now().year  # default to current year

    transactions = (
        Transaction.objects
        .filter(user=user, date__year=year)
        .values('category__name')
        .annotate(
            total_expenses=Coalesce(
                Sum('amount', filter=models.Q(type='expense')),
                V(0),
                output_field=DecimalField()
            ),
            total_income=Coalesce(
                Sum('amount', filter=models.Q(type='income')),
                V(0),
                output_field=DecimalField()
            )
        )
        .annotate(
            net_balance=F('total_income') - F('total_expenses')
        )
        .order_by('-total_expenses')
    )

    total_income_all = sum(t["total_income"] for t in transactions)
    total_expenses_all = sum(t["total_expenses"] for t in transactions)
    net_balance_all = total_income_all - total_expenses_all

    return Response({
        "year": year,
        "categories": list(transactions),
        "total_income": total_income_all,
        "total_expenses": total_expenses_all,
        "net_balance": net_balance_all
    })

# -------------------- CALENDAR ------------------------------------------------------------------------------------
class CalendarListCreateView(generics.ListCreateAPIView):
    serializer_class = CalendarSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return Calendar.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        calendar = serializer.save(user=self.request.user)
        _, num_days = monthrange(calendar.year, calendar.month)
        for day in range(1, num_days + 1):
            cell_date = date(calendar.year, calendar.month, day)
            CalendarCell.objects.create(calendar=calendar, date=cell_date)

# -------------------- BILLS ---------------------------------------------------------------------------------------
class BillDueListCreateView(generics.ListCreateAPIView):
    serializer_class = BillDueSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        return BillDue.objects.filter(user=self.request.user).order_by('due_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)