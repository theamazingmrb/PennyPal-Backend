from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum


# ---------- PROFILE -------------------------------------------------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile when a new User is created."""
    if created:
        Profile.objects.create(user=instance)


# ---------- CATEGORY ------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return f"{self.name} ({self.user.username})"


# ---------- TRANSACTION ---------------------------------------------------------------
class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.type.capitalize()} - {self.amount} ({self.category or 'No Category'})"


# ---------- CALENDAR ------------------------------------------------------------------
class Calendar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendars')
    month = models.IntegerField()  # 1–12
    year = models.IntegerField()

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}"


# ---------- CALENDAR CELL -------------------------------------------------------------
class CalendarCell(models.Model):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='cells')
    date = models.DateField()
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def update_totals(self):
        """Recalculate income, expenses, and balance for this day."""
        transactions = Transaction.objects.filter(
            user=self.calendar.user,
            date=self.date
        )

        income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

        self.total_income = income
        self.total_expenses = expenses
        self.net_balance = income - expenses
        self.save()

    def __str__(self):
        return f"{self.date} - Net: {self.net_balance}"


# ---------- BILL DUE ------------------------------------------------------------------
class BillDue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills')
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=[('Bill', 'Bill'), ('Credit Card', 'Credit Card')])
    due_date = models.DateField() 
    note = models.TextField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    

# ---------- SIGNALS ------------------------------------------------------------------
@receiver(post_save, sender=Transaction)
def update_calendar_cell(sender, instance, **kwargs):
    """Update the daily cell totals whenever a transaction is added or updated."""
    calendar, created = Calendar.objects.get_or_create(
        user=instance.user,
        month=instance.date.month,
        year=instance.date.year
    )
    cell, created = CalendarCell.objects.get_or_create(calendar=calendar, date=instance.date)
    cell.update_totals()
