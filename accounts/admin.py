from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'is_valid_display', 'start_date', 'end_date')
    list_editable = ('is_active',)
    search_fields = ('user__username', 'user__email')
    list_filter = ('plan', 'is_active')
    readonly_fields = ('stripe_customer_id', 'stripe_subscription_id', 'created_at')

    def is_valid_display(self, obj):
        return obj.is_valid
    is_valid_display.short_description = 'Valid'
    is_valid_display.boolean = True