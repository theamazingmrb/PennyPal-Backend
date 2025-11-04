

from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from accounts.models import Profile, Category, Transaction
from accounts.models import Calendar, CalendarCell, BillDue


# ---------- USER -------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

# ---------- PROFILE ----------------------------------------------------------------
class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'created_at']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()

        instance.save()
        return instance

# ---------- REGISTER ----------------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

# ---------- LOGIN -------------------------------------------------------------------------------------------   
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


# ---------- CATEGORY ----------------------------------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'user']
        read_only_fields = ['user']

# ---------- TRANSACTION -------------------------------------------------------------------------------------
class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'amount',
            'type',
            'description',
            'date',
            'category',
            'category_id'
        ]
        read_only_fields = ['user', 'date']

#-------------Bill due----------------------------------------------------------------------------------------
class BillDueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillDue
        fields = ['id', 'name', 'amount', 'due_date', 'is_paid']
#-------------calendar cell-----------------------------------------------------------------------------------
class CalendarCellSerializer(serializers.ModelSerializer):
    bills = serializers.SerializerMethodField()

    class Meta:
        model = CalendarCell
        fields = ['id', 'date', 'total_expenses', 'bills']

    def get_bills(self, obj):
        # Get bills due on this cell's date for the same user(update calendar cell)
        bills = BillDue.objects.filter(
            user=obj.calendar.user,
            due_date=obj.date
        )
        return BillDueSerializer(bills, many=True).data

#---------------calendar---------------------------------------------------------------------------------------
class CalendarSerializer(serializers.ModelSerializer):
    cells = CalendarCellSerializer(many=True, read_only=True)

    class Meta:
        model = Calendar
        fields = ['id', 'month', 'year', 'cells']

