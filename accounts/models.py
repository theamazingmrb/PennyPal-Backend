
from django.db import models #define database tables
from django.contrib.auth.models import User #builduser model that stores username, password,email,...
from django.db.models.signals import post_save #signal sens after a model is saved
from django.dispatch import receiver # a decorator to connect your function to that signal
from django.db.models import Sum
from datetime import date


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) #each user has one profile,if user is deleted the prifile is deleted,records when profile was created,how the profile appears in admin lists.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User) # signal reciver
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

#-------categories---------------------------------------------------------------------------------------------------- 
class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

#-------Transactions----------------------------------------------------------------------------------------------------   
class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.type.capitalize()} - {self.amount} ({self.category})"

#-------calendar for specific month---------------------------------------------------------------------------------------- 
class Calendar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField()  # 1–12
    year = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}"
    
# -------Each day cell in the calendar--------------------------------------------------------------------------------------
class CalendarCell(models.Model):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name='cells')
    date = models.DateField()
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def update_total_expenses(self):
        from accounts.models import Transaction  # avoid circular import
        total = Transaction.objects.filter(
            user=self.calendar.user,
            date=self.date,
            type='expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        self.total_expenses = total
        self.save()

    def __str__(self):
        return f"{self.date} - {self.total_expenses}"

#-------Bills due dates---------------------------------------------------------------------------------------------------- 
class BillDue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.due_date}"

