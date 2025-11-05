from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from accounts.models import Profile, Category, Transaction, Calendar, CalendarCell, BillDue


# ---------- USER (used for /profile/, /profile/update/, etc.) ----------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "email": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        instance.save()
        return instance


# ---------- PROFILE (used if you ever show extended user info) ----------
class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "user"]


# ---------- REGISTER (SIGNUP) ----------
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        user = User.objects.create_user(**validated_data)
        return user


# ---------- LOGIN ----------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


# ---------- CATEGORY ----------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "user"]
        read_only_fields = ["user"]


# ---------- TRANSACTION ----------
class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "user",
            "amount",
            "type",
            "description",
            "date",
            "category",
            "category_id",
        ]
        read_only_fields = ["user"]

    def create(self, validated_data):
        """Assign user automatically"""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)


# ---------- BILL DUE ----------
class BillDueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillDue
        fields = ["id", "name", "amount", "type", "due_date", "note", "is_paid"]


# ---------- CALENDAR CELL ----------
class CalendarCellSerializer(serializers.ModelSerializer):
    bills = serializers.SerializerMethodField()

    class Meta:
        model = CalendarCell
        fields = ["id", "date", "total_income", "total_expenses", "net_balance", "bills"]

    def get_bills(self, obj):
        bills = BillDue.objects.filter(
            user=obj.calendar.user, due_date=obj.date
        )
        return BillDueSerializer(bills, many=True).data


# ---------- CALENDAR ----------
class CalendarSerializer(serializers.ModelSerializer):
    cells = CalendarCellSerializer(many=True, read_only=True)

    class Meta:
        model = Calendar
        fields = ["id", "month", "year", "cells"]