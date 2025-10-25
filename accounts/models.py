from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, date

class Subscription(models.Model):
    PLAN_CHOICES = [
        ("3_month", "3 Month"),
        ("6_month", "6 Month"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    # For Stripe integration
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically set end date if not already set
        if not self.end_date:
            if self.plan == "3_month":
                self.end_date = date.today() + timedelta(days=90)
            elif self.plan == "6_month":
                self.end_date = date.today() + timedelta(days=180)

        # Automatically mark subscription active if within valid period
        self.is_active = self.end_date >= date.today()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.plan} ({'Active' if self.is_active else 'Expired'})"
